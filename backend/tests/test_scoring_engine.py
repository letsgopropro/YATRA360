"""
YATRA360 — Unit & Integration Tests for Dynamic Destination Scoring Engine
Step 2: Validates all 6 components, normalization, weights, idempotency, and API routes.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.destination import Destination
from app.schemas.scoring import TravelRequest
from app.services.scoring_engine import (
    WEIGHTS,
    calculate_accessibility_distance_score,
    calculate_cost_suitability,
    calculate_crowd_suitability,
    calculate_destination_score,
    calculate_preference_match,
    calculate_safety_score,
    calculate_weather_condition_score,
    haversine_distance_km,
)

client = TestClient(app)


# ============================================================================
# Helper Fixtures & Dummy Objects
# ============================================================================

def make_dummy_destination(
    name="Test Spot",
    category="Nature",
    state="Uttarakhand",
    city="Rishikesh",
    latitude=30.0869,
    longitude=78.2676,
    entry_fee=0.0,
    safety_rating=4.0,
    is_hidden_gem=False,
    base_crowd_level="moderate",
    accessibility_info=None,
    description="A scenic natural river viewpoint with forest paths.",
) -> Destination:
    dest = Destination(
        name=name,
        slug="test-spot-slug",
        description=description,
        category=category,
        state=state,
        city=city,
        latitude=latitude,
        longitude=longitude,
        entry_fee=entry_fee,
        safety_rating=safety_rating,
        is_hidden_gem=is_hidden_gem,
        base_crowd_level=base_crowd_level,
        accessibility_info=accessibility_info,
    )
    dest.id = 999
    return dest


# ============================================================================
# 1. Component 1: Preference Match Tests
# ============================================================================

def test_preference_match_no_interests_returns_neutral():
    dest = make_dummy_destination(category="Nature")
    score, expl = calculate_preference_match(dest, TravelRequest())
    assert score is None
    assert "renormalized" in expl.lower()


def test_preference_match_exact_category():
    dest = make_dummy_destination(category="Nature", is_hidden_gem=False)
    req = TravelRequest(interests=["Nature", "Wildlife"])
    score, expl = calculate_preference_match(dest, req)
    assert score == 90.0
    assert "direct category match" in expl.lower()


def test_preference_match_with_hidden_gem_alignment():
    # Matching category + matching hidden gem preference -> 100.0
    dest = make_dummy_destination(category="Adventure", is_hidden_gem=True)
    req = TravelRequest(interests=["Adventure"], prefer_hidden_gems=True)
    score, expl = calculate_preference_match(dest, req)
    assert score == 100.0
    assert "bonus" in expl.lower()


def test_preference_match_non_matching_category():
    dest = make_dummy_destination(category="Spiritual")
    req = TravelRequest(interests=["Beach", "Wildlife"])
    score, expl = calculate_preference_match(dest, req)
    assert score == 20.0
    assert "does not match" in expl.lower()


def test_preference_match_description_keyword_fallback():
    dest = make_dummy_destination(category="Cultural", description="Ancient Buddhist temple ruins and shrines.")
    req = TravelRequest(interests=["Temple"])
    score, expl = calculate_preference_match(dest, req)
    assert score == 45.0
    assert "keywords found in description" in expl.lower()


# ============================================================================
# 2. Component 2: Safety Score Tests
# ============================================================================

@pytest.mark.parametrize(
    "safety_rating,expected_score",
    [
        (1.0, 20.0),
        (2.0, 40.0),
        (3.0, 60.0),
        (4.0, 80.0),
        (5.0, 100.0),
        (4.2, 84.0),
        (0.5, 20.0),  # clamped below
        (6.0, 100.0), # clamped above
    ]
)
def test_safety_score_normalization(safety_rating, expected_score):
    dest = make_dummy_destination(safety_rating=safety_rating)
    score, expl = calculate_safety_score(dest)
    assert score == pytest.approx(expected_score, rel=1e-2)
    assert "normalized to" in expl.lower()


# ============================================================================
# 3. Component 3: Crowd Suitability Tests
# ============================================================================

def test_crowd_suitability_default_mapping():
    """When no preferred_crowd_level is provided, general crowd-pressure applies."""
    dest_low = make_dummy_destination(base_crowd_level="low")
    dest_mod = make_dummy_destination(base_crowd_level="moderate")
    dest_high = make_dummy_destination(base_crowd_level="high")

    score_low, _ = calculate_crowd_suitability(dest_low, TravelRequest())
    score_mod, _ = calculate_crowd_suitability(dest_mod, TravelRequest())
    score_high, _ = calculate_crowd_suitability(dest_high, TravelRequest())

    assert score_low == 100.0
    assert score_mod == 60.0
    assert score_high == 20.0


def test_crowd_suitability_preferred_low():
    req = TravelRequest(preferred_crowd_level="low")
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="low"), req)[0] == 100.0
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="moderate"), req)[0] == 60.0
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="high"), req)[0] == 20.0


def test_crowd_suitability_preferred_moderate():
    req = TravelRequest(preferred_crowd_level="moderate")
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="moderate"), req)[0] == 100.0
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="low"), req)[0] == 80.0
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="high"), req)[0] == 30.0


def test_crowd_suitability_preferred_high():
    req = TravelRequest(preferred_crowd_level="high")
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="high"), req)[0] == 100.0
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="moderate"), req)[0] == 70.0
    assert calculate_crowd_suitability(make_dummy_destination(base_crowd_level="low"), req)[0] == 50.0


# ============================================================================
# 4. Component 4: Accessibility & Distance Tests
# ============================================================================

def test_haversine_distance():
    # Delhi (28.6139, 77.2090) to Agra (27.1767, 78.0081) is approximately 175-185 km
    dist = haversine_distance_km(28.6139, 77.2090, 27.1767, 78.0081)
    assert 170.0 <= dist <= 190.0


def test_accessibility_without_requirement():
    dest = make_dummy_destination(accessibility_info=None)
    score, _ = calculate_accessibility_distance_score(dest, TravelRequest(requires_accessibility=False))
    # 0.5 * 80 (access baseline) + 0.5 * 70 (dist baseline) = 75.0
    assert score == 75.0


def test_accessibility_with_requirement_positive():
    dest = make_dummy_destination(accessibility_info="Wheelchair ramps and paved flat pathways available.")
    req = TravelRequest(requires_accessibility=True)
    score, expl = calculate_accessibility_distance_score(dest, req)
    # access score = 95.0, dist baseline = 70.0 -> average = 82.5
    assert score == 82.5
    assert "wheelchair/ramp" in expl.lower()


def test_accessibility_with_requirement_negative():
    dest = make_dummy_destination(accessibility_info="Steep rocky trek with 3000 stone stairs. Not wheelchair accessible.")
    req = TravelRequest(requires_accessibility=True)
    score, expl = calculate_accessibility_distance_score(dest, req)
    # access score = 30.0, dist baseline = 70.0 -> average = 50.0
    assert score == 50.0
    assert "steep stairs" in expl.lower()


def test_distance_proximity_scoring():
    # Destination at (28.5, 77.2)
    dest = make_dummy_destination(latitude=28.5, longitude=77.2)
    # User very close (28.51, 77.21) -> distance ~ 1.5 km
    req_close = TravelRequest(user_latitude=28.51, user_longitude=77.21, max_distance_km=100.0)
    score_close, expl_close = calculate_accessibility_distance_score(dest, req_close)

    # User far away (19.0, 72.8) Mumbai ~ 1100 km
    req_far = TravelRequest(user_latitude=19.0, user_longitude=72.8, max_distance_km=200.0)
    score_far, expl_far = calculate_accessibility_distance_score(dest, req_far)

    assert score_close > score_far
    assert "within requested radius" in expl_close.lower()
    assert "exceeds desired radius" in expl_far.lower()


# ============================================================================
# 5. Component 5: Cost Suitability Tests
# ============================================================================

def test_cost_suitability_no_budget():
    dest = make_dummy_destination(entry_fee=50.0)
    score, expl = calculate_cost_suitability(dest, TravelRequest(budget=None))
    assert score == 80.0
    assert "unconstrained" in expl.lower()


def test_cost_suitability_free_entry():
    dest = make_dummy_destination(entry_fee=0.0)
    score, expl = calculate_cost_suitability(dest, TravelRequest(budget=200.0))
    assert score == 100.0
    assert "free entry" in expl.lower()


def test_cost_suitability_within_budget():
    dest = make_dummy_destination(entry_fee=50.0)
    score, expl = calculate_cost_suitability(dest, TravelRequest(budget=1000.0))
    # 50 / 1000 = 5% of budget -> 95.0
    assert score == 95.0


def test_cost_suitability_over_budget():
    dest = make_dummy_destination(entry_fee=200.0)
    score, expl = calculate_cost_suitability(dest, TravelRequest(budget=100.0))
    # 200 / 100 = 2.0 ratio -> score = max(0, 50 - (2.0 - 1.0)*50) = 0.0
    assert score == 0.0
    assert "exceeds" in expl.lower()


# ============================================================================
# 6. Component 6: Weather Condition Tests
# ============================================================================

def test_weather_condition_neutral_baseline():
    dest = make_dummy_destination(category="Heritage")
    score, expl = calculate_weather_condition_score(dest, TravelRequest())
    assert score == 70.0
    assert "prototype baseline" in expl.lower()


def test_weather_condition_climate_alignment():
    dest_hill = make_dummy_destination(category="Hill Station")
    score_cool, _ = calculate_weather_condition_score(dest_hill, TravelRequest(weather_preference="cool"))
    assert score_cool == 90.0

    dest_beach = make_dummy_destination(category="Beach")
    score_warm, _ = calculate_weather_condition_score(dest_beach, TravelRequest(weather_preference="sunny"))
    assert score_warm == 90.0


# ============================================================================
# 7. Master Function: Overall Weighted Score & Mathematical Integrity
# ============================================================================

def test_weights_sum_to_one():
    total_weight = sum(WEIGHTS.values())
    assert pytest.approx(total_weight, rel=1e-5) == 1.00


def test_overall_score_range_and_structure():
    dest = make_dummy_destination(
        category="Nature",
        safety_rating=4.0,
        base_crowd_level="moderate",
        entry_fee=50.0,
    )
    req = TravelRequest(
        interests=["Nature"],
        budget=500.0,
        preferred_crowd_level="moderate",
    )
    res = calculate_destination_score(dest, req)

    assert 0.0 <= res.overall_score <= 100.0
    assert res.destination_id == 999
    assert res.destination_name == "Test Spot"

    # All components bounded in [0, 100]
    for key, val in res.components.model_dump().items():
        assert 0.0 <= val <= 100.0, f"Component {key} has out of bounds value: {val}"

    # Verify explanations exist for all 6 components
    assert len(res.explanations) == 6
    for key in res.components.model_dump():
        assert key in res.explanations
        assert len(res.explanations[key]) > 0


# ============================================================================
# 8. API Integration Tests
# ============================================================================

def test_api_score_single_destination_success():
    # Query seeded Taj Mahal from database
    db = SessionLocal()
    dest = db.scalar(select(Destination).where(Destination.slug == "taj-mahal-agra"))
    dest_id = dest.id
    db.close()

    payload = {
        "interests": ["Heritage"],
        "budget": 500.0,
        "preferred_crowd_level": "moderate",
        "requires_accessibility": True,
    }
    response = client.post(f"/api/scoring/destination/{dest_id}", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["destination_id"] == dest_id
    assert data["destination_name"] == "Taj Mahal"
    assert "overall_score" in data
    assert 0.0 <= data["overall_score"] <= 100.0

    # Components structure
    comp = data["components"]
    assert comp["preference_match"] >= 90.0  # Heritage matches
    assert comp["safety"] == 80.0           # 4.0/5.0
    assert comp["cost_suitability"] >= 85.0 # Entry fee 50 <= budget 500
    assert "weights" in data
    assert "explanations" in data


def test_api_score_single_destination_empty_body():
    """Endpoint works cleanly when empty body / default travel request is provided."""
    db = SessionLocal()
    dest = db.scalar(select(Destination).where(Destination.slug == "taj-mahal-agra"))
    dest_id = dest.id
    db.close()

    response = client.post(f"/api/scoring/destination/{dest_id}", json={})
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["overall_score"] <= 100.0


def test_api_score_single_destination_not_found():
    response = client.post("/api/scoring/destination/999999", json={})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_score_destinations_batch():
    payload = {
        "interests": ["Beach"],
        "preferred_crowd_level": "low",
        "budget": 1000.0,
    }
    response = client.post("/api/scoring/destinations?category=Beach&limit=5", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "results" in data
    assert len(data["results"]) >= 1

    # Verify descending sort order by overall_score
    scores = [r["overall_score"] for r in data["results"]]
    assert scores == sorted(scores, reverse=True)
