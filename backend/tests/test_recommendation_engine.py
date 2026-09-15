"""
YATRA360 — Personalized Recommendation Engine Tests
Step 3: Validates content-based recommendation flow, scoring reuse, filters,
conservative diversity, limit handling, explainability, and alternative scaffolding.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.destination import Destination
from app.schemas.recommendation import RecommendationRequest
from app.services.recommendation_engine import (
    apply_category_diversity,
    find_alternative_destinations,
    get_recommendations,
)
from app.services.scoring_engine import calculate_destination_score

client = TestClient(app)


# ============================================================================
# 1. Basic Recommendation Flow & Scoring Engine Reuse
# ============================================================================

def test_basic_recommendation_request():
    """Verify POST /api/recommendations accepts request and returns structured recommendations."""
    payload = {
        "interests": ["Nature", "Adventure"],
        "budget": 2000.0,
        "available_time_minutes": 480,
        "preferred_crowd_level": "low",
        "prefer_hidden_gems": True,
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total_candidates_evaluated"] >= 50
    assert 1 <= data["recommendations_count"] <= 5
    assert len(data["recommendations"]) == data["recommendations_count"]

    first = data["recommendations"][0]
    assert "destination_id" in first
    assert "destination_name" in first
    assert "slug" in first
    assert "overall_score" in first
    assert "components" in first
    assert "reasons" in first
    assert 0.0 <= first["overall_score"] <= 100.0


def test_scoring_engine_reuse():
    """Verify that recommendations use the existing proposal scoring engine."""
    db = SessionLocal()
    req = RecommendationRequest(interests=["Heritage"], budget=1000.0, limit=3)
    response = get_recommendations(req, db)
    db.close()

    assert len(response.recommendations) > 0
    item = response.recommendations[0]

    # Verify all 6 proposal scoring components are present
    comp = item.components
    assert hasattr(comp, "preference_match")
    assert hasattr(comp, "safety")
    assert hasattr(comp, "crowd_suitability")
    assert hasattr(comp, "accessibility_distance")
    assert hasattr(comp, "cost_suitability")
    assert hasattr(comp, "weather_condition")


# ============================================================================
# 2. Interest-Based Ranking
# ============================================================================

def test_interest_based_ranking():
    """Verify that specifying interests elevates matching category destinations to top ranks."""
    payload_nature = {"interests": ["Nature"], "limit": 5}
    resp_nature = client.post("/api/recommendations", json=payload_nature).json()

    payload_spiritual = {"interests": ["Spiritual"], "limit": 5}
    resp_spiritual = client.post("/api/recommendations", json=payload_spiritual).json()

    top_nature_categories = [r["category"] for r in resp_nature["recommendations"][:3]]
    top_spiritual_categories = [r["category"] for r in resp_spiritual["recommendations"][:3]]

    assert any("nature" in c.lower() for c in top_nature_categories)
    assert any("spiritual" in c.lower() for c in top_spiritual_categories)


# ============================================================================
# 3. Hidden-Gem Preference
# ============================================================================

def test_hidden_gem_preference():
    """Verify prefer_hidden_gems=True prioritizes hidden gem destinations."""
    payload = {
        "interests": ["Nature"],
        "prefer_hidden_gems": True,
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload).json()
    gems = [r for r in response["recommendations"] if r["is_hidden_gem"]]
    assert len(gems) >= 3, "Expected majority of recommendations to be hidden gems"


# ============================================================================
# 4. Search / Candidate Filters (Category & State)
# ============================================================================

def test_category_filtering():
    """Verify category filter strictly limits candidate selection to that category."""
    payload = {
        "category": "Beach",
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload).json()
    assert response["recommendations_count"] >= 1
    for item in response["recommendations"]:
        assert item["category"].lower() == "beach"


def test_state_filtering():
    """Verify state filter limits candidates to the requested state."""
    payload = {
        "state": "Kerala",
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload).json()
    assert response["recommendations_count"] >= 1
    for item in response["recommendations"]:
        assert item["state"].lower() == "kerala"


def test_is_hidden_gem_strict_filter():
    """Verify is_hidden_gem filter strictly enforces boolean status."""
    payload = {
        "is_hidden_gem": False,
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload).json()
    assert response["recommendations_count"] >= 1
    for item in response["recommendations"]:
        assert item["is_hidden_gem"] is False


# ============================================================================
# 5. Budget Suitability
# ============================================================================

def test_budget_suitability():
    """Verify budget limits reward zero-fee or low-fee destinations."""
    payload = {
        "budget": 25.0,
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload).json()
    for item in response["recommendations"]:
        # Top recommendations should be highly cost suitable
        assert item["components"]["cost_suitability"] >= 80.0


# ============================================================================
# 6. Crowd Preference
# ============================================================================

def test_crowd_preference():
    """Verify preferred_crowd_level='low' gives high crowd suitability to low-crowd sites."""
    payload = {
        "preferred_crowd_level": "low",
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload).json()
    top_pick = response["recommendations"][0]
    assert top_pick["components"]["crowd_suitability"] >= 60.0


# ============================================================================
# 7. Available-Time Schedule Handling
# ============================================================================

def test_available_time_schedule_penalty():
    """Verify destinations with visit duration far exceeding available time receive schedule adjustment."""
    db = SessionLocal()
    # User has only 45 minutes
    req_short = RecommendationRequest(available_time_minutes=45, limit=50)
    res_short = get_recommendations(req_short, db)
    db.close()

    # Destinations taking 240+ minutes (e.g. Hampi, Valley of Flowers) should be penalized down
    top_5_ids = [r.destination_id for r in res_short.recommendations[:5]]
    
    # Hampi requires 300 minutes; should not dominate a 45-minute request
    db = SessionLocal()
    hampi = db.scalar(select(Destination).where(Destination.slug == "hampi-monuments-vijayanagara"))
    db.close()
    if hampi:
        hampi_in_short = next((r for r in res_short.recommendations if r.destination_id == hampi.id), None)
        if hampi_in_short:
            # Score should reflect overtime penalty
            assert any("exceeds your available window" in r for r in hampi_in_short.reasons)


# ============================================================================
# 8. Empty Request & Default Handling
# ============================================================================

def test_empty_request_handling():
    """Verify empty request body defaults gracefully without errors."""
    response = client.post("/api/recommendations", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations_count"] > 0
    assert data["total_candidates_evaluated"] >= 50


# ============================================================================
# 9. Limit Returns UP TO Requested Count
# ============================================================================

def test_limit_behavior_up_to_count():
    """Verify limit returns up to requested count and never exceeds available candidates."""
    # 1. Normal limit
    res1 = client.post("/api/recommendations", json={"limit": 3}).json()
    assert res1["recommendations_count"] == 3

    # 2. Limit larger than candidates matching filter (e.g. Goa has ~3 destinations)
    res2 = client.post("/api/recommendations", json={"state": "Goa", "limit": 20}).json()
    assert res2["recommendations_count"] <= res2["total_candidates_evaluated"]
    assert res2["recommendations_count"] <= 20
    assert res2["recommendations_count"] > 0


# ============================================================================
# 10. Ranking & Integrity Tests
# ============================================================================

def test_ranking_is_descending_by_score():
    """Verify that returned recommendations are sorted in descending order of score."""
    response = client.post("/api/recommendations", json={"limit": 10}).json()
    scores = [r["overall_score"] for r in response["recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_no_duplicate_destinations():
    """Verify recommendations contain no duplicate destination IDs."""
    response = client.post("/api/recommendations", json={"limit": 15}).json()
    dest_ids = [r["destination_id"] for r in response["recommendations"]]
    assert len(dest_ids) == len(set(dest_ids))


def test_transparent_reasons_present():
    """Verify every recommendation item contains 3 to 5 non-empty factual reasons."""
    response = client.post("/api/recommendations", json={"limit": 5}).json()
    for item in response["recommendations"]:
        assert isinstance(item["reasons"], list)
        assert 3 <= len(item["reasons"]) <= 5
        for reason in item["reasons"]:
            assert isinstance(reason, str) and len(reason.strip()) > 5


# ============================================================================
# 11. Conservative Category Diversity Tests
# ============================================================================

def test_conservative_diversity_within_threshold():
    """Verify that diversity promotes a diverse category candidate if within 10 points."""
    # Test dummy candidates: A1, A2, A3 (Category A) and B1 (Category B)
    from app.models.destination import Destination
    d1 = Destination(name="A1", slug="a1", category="Heritage", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)
    d2 = Destination(name="A2", slug="a2", category="Heritage", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)
    d3 = Destination(name="A3", slug="a3", category="Heritage", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)
    d4 = Destination(name="B1", slug="b1", category="Nature", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)

    # Scored items with 8.0 point difference between A3 and B1 (within 10.0 threshold)
    items = [
        {"destination": d1, "adjusted_score": 90.0, "reasons": []},
        {"destination": d2, "adjusted_score": 88.0, "reasons": []},
        {"destination": d3, "adjusted_score": 86.0, "reasons": []},
        {"destination": d4, "adjusted_score": 80.0, "reasons": []},  # 86.0 - 80.0 = 6.0 <= 10.0
    ]
    diversified = apply_category_diversity(items, limit=3, diversity_threshold=10.0, max_per_category=2)
    categories = [x["destination"].category for x in diversified]
    # Expected: A1, A2, and B1 (since A3 is the 3rd of Heritage and B1 is within 10 points)
    assert categories == ["Heritage", "Heritage", "Nature"]


def test_conservative_diversity_preserves_high_score():
    """Verify that diversity does NOT promote a diverse candidate if score difference exceeds 10 points."""
    from app.models.destination import Destination
    d1 = Destination(name="A1", slug="a1", category="Heritage", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)
    d2 = Destination(name="A2", slug="a2", category="Heritage", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)
    d3 = Destination(name="A3", slug="a3", category="Heritage", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)
    d4 = Destination(name="B1", slug="b1", category="Nature", state="RJ", city="J", latitude=26.0, longitude=75.0, entry_fee=0.0)

    # 15.0 point difference (exceeds 10.0 threshold)
    items = [
        {"destination": d1, "adjusted_score": 90.0, "reasons": []},
        {"destination": d2, "adjusted_score": 88.0, "reasons": []},
        {"destination": d3, "adjusted_score": 86.0, "reasons": []},
        {"destination": d4, "adjusted_score": 70.0, "reasons": []},  # 86.0 - 70.0 = 16.0 > 10.0
    ]
    diversified = apply_category_diversity(items, limit=3, diversity_threshold=10.0, max_per_category=2)
    categories = [x["destination"].category for x in diversified]
    # Expected: A1, A2, A3 (quality preserved because B1 score gap is too large)
    assert categories == ["Heritage", "Heritage", "Heritage"]


# ============================================================================
# 12. Alternative Destination Scaffolding Tests (Step 4 Preparation)
# ============================================================================

def test_alternative_destinations_scaffolding():
    """Verify alternative destination scaffolding retrieves valid alternatives."""
    db = SessionLocal()
    taj = db.scalar(select(Destination).where(Destination.slug == "taj-mahal-agra"))
    taj_id = taj.id
    db.close()

    response = client.get(f"/api/recommendations/alternatives/{taj_id}?limit=3")
    assert response.status_code == 200
    data = response.json()

    assert data["source_destination_id"] == taj_id
    assert data["source_destination_name"] == "Taj Mahal"
    assert "alternatives" in data
    assert 1 <= data["alternatives_count"] <= 3

    # Ensure source destination is not returned in its own alternatives
    for alt in data["alternatives"]:
        assert alt["destination_id"] != taj_id
        assert len(alt["reasons"]) >= 2


def test_alternative_destinations_not_found():
    """Verify requesting alternatives for nonexistent ID returns 404."""
    response = client.get("/api/recommendations/alternatives/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
