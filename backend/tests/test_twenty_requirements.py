"""
YATRA360 — Twenty Mandatory Recommendation & Scoring Engine Tests
Explicitly implements all 20 required test cases from Section 24 of the specification:

Test 1: Perfect preference match.
Test 2: No preference match.
Test 3: Low crowd.
Test 4: High crowd.
Test 5: High safety vs low safety.
Test 6: Destination within budget.
Test 7: Destination exceeding budget.
Test 8: Nearby vs distant destinations.
Test 9: Favorable vs unfavorable weather.
Test 10: Missing weather data.
Test 11: Missing crowd data.
Test 12: Missing safety data.
Test 13: Weight validation.
Test 14: Final score remains between 0 and 100.
Test 15: Recommendations are correctly ranked.
Test 16: Preferred overcrowded destination produces alternatives.
Test 17: Preferred destination is not returned as its own alternative.
Test 18: Changing user interests changes recommendation scores.
Test 19: Changing budget affects cost suitability.
Test 20: Same input produces deterministic output.
"""

import pytest
from app.models.destination import Destination
from app.schemas.scoring import TravelRequest
from app.services.preference_matcher import calculate_preference_match
from app.services.scoring_engine import (
    DEFAULT_WEIGHTS,
    calculate_accessibility_distance_score,
    calculate_cost_suitability,
    calculate_crowd_suitability,
    calculate_destination_score,
    calculate_safety_score,
    calculate_weather_condition_score,
    is_overcrowded,
    validate_weights,
)
from app.services.recommendation_engine import (
    check_and_redirect_if_overcrowded,
    recommend_alternatives,
    recommend_destinations,
)


def create_dest(
    id: int = 1,
    name: str = "Sample Spot",
    slug: str = None,
    category: str = "Nature",
    state: str = "Uttarakhand",
    city: str = "Rishikesh",
    latitude: float = 30.0869,
    longitude: float = 78.2676,
    entry_fee: float = 50.0,
    safety_rating: float = 4.0,
    base_crowd_level: str = "moderate",
    is_hidden_gem: bool = False,
    description: str = "A scenic natural spot with forests and trails.",
    accessibility_info: str = "Paved flat paths available.",
    estimated_visit_duration: int = 120,
) -> Destination:
    dest = Destination(
        name=name,
        slug=slug or f"sample-spot-{id}",
        category=category,
        state=state,
        city=city,
        latitude=latitude,
        longitude=longitude,
        entry_fee=entry_fee,
        safety_rating=safety_rating,
        base_crowd_level=base_crowd_level,
        is_hidden_gem=is_hidden_gem,
        description=description,
        accessibility_info=accessibility_info,
        estimated_visit_duration=estimated_visit_duration,
    )
    dest.id = id
    return dest


# ============================================================================
# Test 1: Perfect preference match
# ============================================================================
def test_01_perfect_preference_match():
    dest = create_dest(category="Nature", description="Scenic wildlife sanctuary with birdwatching.")
    req = TravelRequest(interests=["Nature", "Wildlife"])
    score, expl = calculate_preference_match(dest, req)
    assert score is not None
    assert score >= 90.0
    assert "direct category match" in expl.lower()


# ============================================================================
# Test 2: No preference match
# ============================================================================
def test_02_no_preference_match():
    dest = create_dest(category="Heritage", description="Ancient royal fortress ruins.")
    req = TravelRequest(interests=["Beach", "Scuba"])
    score, expl = calculate_preference_match(dest, req)
    assert score is not None
    assert score <= 25.0
    assert "does not match" in expl.lower()


# ============================================================================
# Test 3: Low crowd
# ============================================================================
def test_03_low_crowd():
    dest = create_dest(base_crowd_level="low")
    score, expl = calculate_crowd_suitability(dest, TravelRequest())
    assert score == 100.0


# ============================================================================
# Test 4: High crowd
# ============================================================================
def test_04_high_crowd():
    dest = create_dest(base_crowd_level="high")
    score, expl = calculate_crowd_suitability(dest, TravelRequest())
    assert score == 20.0
    # Higher crowd pressure must yield lower crowd suitability
    dest_low = create_dest(base_crowd_level="low")
    score_low, _ = calculate_crowd_suitability(dest_low, TravelRequest())
    assert score < score_low


# ============================================================================
# Test 5: High safety vs low safety
# ============================================================================
def test_05_high_safety_vs_low_safety():
    dest_high = create_dest(safety_rating=5.0)
    dest_low = create_dest(safety_rating=2.0)
    score_high, _ = calculate_safety_score(dest_high)
    score_low, _ = calculate_safety_score(dest_low)
    assert score_high == 100.0
    assert score_low == 40.0
    assert score_high > score_low


# ============================================================================
# Test 6: Destination within budget
# ============================================================================
def test_06_destination_within_budget():
    dest = create_dest(entry_fee=50.0)
    req = TravelRequest(budget=1000.0)
    score, expl = calculate_cost_suitability(dest, req)
    assert score == 95.0
    assert "within budget" in expl.lower()


# ============================================================================
# Test 7: Destination exceeding budget
# ============================================================================
def test_07_destination_exceeding_budget():
    dest = create_dest(entry_fee=250.0)
    req = TravelRequest(budget=100.0)
    score, expl = calculate_cost_suitability(dest, req)
    assert score is not None
    assert score < 50.0
    assert "exceeds" in expl.lower()


# ============================================================================
# Test 8: Nearby vs distant destinations
# ============================================================================
def test_08_nearby_vs_distant_destinations():
    # User in New Delhi
    user_lat, user_lon = 28.6139, 77.2090
    dest_near = create_dest(id=1, name="Delhi Monument", latitude=28.6200, longitude=77.2100)
    dest_far = create_dest(id=2, name="Kerala Beach", latitude=9.9312, longitude=76.2673)

    req = TravelRequest(user_latitude=user_lat, user_longitude=user_lon, max_distance_km=500.0)
    score_near, _ = calculate_accessibility_distance_score(dest_near, req)
    score_far, _ = calculate_accessibility_distance_score(dest_far, req)
    assert score_near > score_far


# ============================================================================
# Test 9: Favorable vs unfavorable weather
# ============================================================================
def test_09_favorable_vs_unfavorable_weather():
    dest_hill = create_dest(category="Hill Station")
    dest_beach = create_dest(category="Beach")
    req = TravelRequest(weather_preference="cool")

    score_favorable, _ = calculate_weather_condition_score(dest_hill, req)
    score_unfavorable, _ = calculate_weather_condition_score(dest_beach, req)
    assert score_favorable == 90.0
    assert score_favorable > score_unfavorable


# ============================================================================
# Test 10: Missing weather data
# ============================================================================
def test_10_missing_weather_data():
    dest = create_dest()
    dest.weather_data_available = False  # Mark explicitly unavailable
    res = calculate_destination_score(dest, TravelRequest(interests=["Nature"]))

    assert res.score_breakdown["weather"] is None
    assert res.data_quality["weather"] == "missing"
    # Verify remaining weights renormalized and sum to 1.0
    applied = res.applied_weights
    active_keys = [k for k, v in res.score_breakdown.items() if v is not None]
    assert "weather" not in active_keys
    total_active_weight = sum(applied[k] for k in active_keys)
    assert pytest.approx(total_active_weight, rel=1e-2) == 1.0


# ============================================================================
# Test 11: Missing crowd data
# ============================================================================
def test_11_missing_crowd_data():
    dest = create_dest()
    dest.base_crowd_level = None
    dest.crowd_metrics = []

    res = calculate_destination_score(dest, TravelRequest(interests=["Nature"]))
    assert res.score_breakdown["crowd"] is None
    assert res.data_quality["crowd"] == "missing"
    active_keys = [k for k, v in res.score_breakdown.items() if v is not None]
    assert "crowd" not in active_keys
    total_active_weight = sum(res.applied_weights[k] for k in active_keys)
    assert pytest.approx(total_active_weight, rel=1e-2) == 1.0


# ============================================================================
# Test 12: Missing safety data
# ============================================================================
def test_12_missing_safety_data():
    dest = create_dest()
    dest.safety_rating = None
    dest.safety_records = []

    res = calculate_destination_score(dest, TravelRequest(interests=["Nature"]))
    assert res.score_breakdown["safety"] is None
    assert res.data_quality["safety"] == "missing"
    active_keys = [k for k, v in res.score_breakdown.items() if v is not None]
    assert "safety" not in active_keys
    total_active_weight = sum(res.applied_weights[k] for k in active_keys)
    assert pytest.approx(total_active_weight, rel=1e-2) == 1.0


# ============================================================================
# Test 13: Weight validation
# ============================================================================
def test_13_weight_validation():
    # Valid proposal default weights (sum to 1.0)
    assert validate_weights(DEFAULT_WEIGHTS) is True

    # Invalid: sum != 1.0
    bad_weights = {"preference": 0.5, "safety": 0.5, "crowd": 0.5, "accessibility": 0.1, "cost": 0.1, "weather": 0.1}
    assert validate_weights(bad_weights) is False

    # Invalid: negative weight
    neg_weights = {"preference": 1.2, "safety": -0.2, "crowd": 0.0, "accessibility": 0.0, "cost": 0.0, "weather": 0.0}
    assert validate_weights(neg_weights) is False


# ============================================================================
# Test 14: Final score remains between 0 and 100
# ============================================================================
def test_14_final_score_remains_between_0_and_100():
    # Worst case destination
    worst_dest = create_dest(safety_rating=1.0, base_crowd_level="overcrowded", entry_fee=10000.0)
    worst_req = TravelRequest(interests=["Unrelated"], budget=10.0, max_distance_km=10.0, user_latitude=0.0, user_longitude=0.0)
    res_worst = calculate_destination_score(worst_dest, worst_req)
    assert 0.0 <= res_worst.overall_score <= 100.0

    # Best case destination
    best_dest = create_dest(category="Nature", safety_rating=5.0, base_crowd_level="low", entry_fee=0.0)
    best_req = TravelRequest(interests=["Nature"], budget=1000.0)
    res_best = calculate_destination_score(best_dest, best_req)
    assert 0.0 <= res_best.overall_score <= 100.0


# ============================================================================
# Test 15: Recommendations are correctly ranked
# ============================================================================
def test_15_recommendations_are_correctly_ranked():
    dest_great = create_dest(id=1, name="Great Fit", category="Nature", safety_rating=5.0, base_crowd_level="low", entry_fee=0.0)
    dest_medium = create_dest(id=2, name="Medium Fit", category="Nature", safety_rating=4.0, base_crowd_level="moderate", entry_fee=50.0)
    dest_poor = create_dest(id=3, name="Poor Fit", category="Shopping", safety_rating=2.0, base_crowd_level="high", entry_fee=500.0)

    req = TravelRequest(interests=["Nature"], budget=200.0)
    results = recommend_destinations(req, [dest_poor, dest_great, dest_medium], top_k=3, apply_diversity=False)

    scores = [r["adjusted_score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0]["destination"].name == "Great Fit"


# ============================================================================
# Test 16: Preferred overcrowded destination produces alternatives
# ============================================================================
def test_16_preferred_overcrowded_destination_produces_alternatives():
    overcrowded_site = create_dest(id=10, name="Crowded Monument", category="Heritage", base_crowd_level="high")
    alt_site_1 = create_dest(id=11, name="Serene Fort", category="Heritage", base_crowd_level="low")
    alt_site_2 = create_dest(id=12, name="Quiet Palace", category="Heritage", base_crowd_level="moderate")

    all_dests = [overcrowded_site, alt_site_1, alt_site_2]
    res = check_and_redirect_if_overcrowded(
        preferred_destination=overcrowded_site,
        user_preferences=TravelRequest(interests=["Heritage"]),
        destinations=all_dests,
        top_k=2,
    )

    assert res["is_overcrowded"] is True
    assert len(res["alternatives"]) > 0
    alt_ids = [a["destination"].id for a in res["alternatives"]]
    assert 10 not in alt_ids  # Source destination not in alternatives


# ============================================================================
# Test 17: Preferred destination is not returned as its own alternative
# ============================================================================
def test_17_preferred_destination_not_returned_as_its_own_alternative():
    pref_dest = create_dest(id=5, name="Taj Site", slug="taj-site")
    cand1 = create_dest(id=6, name="Fatehpur Site", slug="fatehpur-site")
    cand2 = create_dest(id=7, name="Agra Fort Site", slug="agra-fort-site")

    alts = recommend_alternatives(
        preferred_destination=pref_dest,
        user_preferences=TravelRequest(),
        destinations=[pref_dest, cand1, cand2],
        top_k=5,
    )

    for item in alts:
        assert item["destination"].id != pref_dest.id
        assert item["destination"].slug != pref_dest.slug


# ============================================================================
# Test 18: Changing user interests changes recommendation scores
# ============================================================================
def test_18_changing_user_interests_changes_recommendation_scores():
    heritage_dest = create_dest(category="Heritage", description="Ancient historical palace.")

    req_heritage = TravelRequest(interests=["Heritage"])
    req_adventure = TravelRequest(interests=["Adventure"])

    score_heritage = calculate_destination_score(heritage_dest, req_heritage).overall_score
    score_adventure = calculate_destination_score(heritage_dest, req_adventure).overall_score

    assert score_heritage > score_adventure


# ============================================================================
# Test 19: Changing budget affects cost suitability
# ============================================================================
def test_19_changing_budget_affects_cost_suitability():
    ticketed_dest = create_dest(entry_fee=500.0)

    req_low_budget = TravelRequest(budget=200.0)
    req_high_budget = TravelRequest(budget=2000.0)

    score_low = calculate_cost_suitability(ticketed_dest, req_low_budget)[0]
    score_high = calculate_cost_suitability(ticketed_dest, req_high_budget)[0]

    assert score_high > score_low


# ============================================================================
# Test 20: Same input produces deterministic output
# ============================================================================
def test_20_same_input_produces_deterministic_output():
    dest = create_dest(category="Nature", safety_rating=4.5, base_crowd_level="moderate", entry_fee=30.0)
    req = TravelRequest(interests=["Nature"], budget=500.0, available_time_minutes=180)

    res1 = calculate_destination_score(dest, req)
    res2 = calculate_destination_score(dest, req)

    assert res1.overall_score == res2.overall_score
    assert res1.score_breakdown == res2.score_breakdown
    assert res1.applied_weights == res2.applied_weights
    assert res1.explanations == res2.explanations
