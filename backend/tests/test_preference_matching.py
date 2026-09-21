"""
Unit tests for the Preference Matching service.
Validates content-based matching, token normalization, overlap calculations,
hidden-gem alignment, and missing data behavior.
"""

import pytest
from app.models.destination import Destination
from app.schemas.scoring import TravelRequest
from app.services.preference_matcher import calculate_preference_match


def make_dummy_destination(
    name="Test Spot",
    category="Nature",
    description="A scenic wildlife sanctuary with lush forests and birdwatching trails.",
    is_hidden_gem=False,
) -> Destination:
    return Destination(
        name=name,
        slug="test-spot",
        category=category,
        description=description,
        is_hidden_gem=is_hidden_gem,
        state="Uttarakhand",
        city="Rishikesh",
        latitude=30.0869,
        longitude=78.2676,
        entry_fee=0.0,
        safety_rating=4.0,
        base_crowd_level="moderate",
    )


def test_perfect_preference_match():
    dest = make_dummy_destination(category="Nature", description="Scenic wildlife sanctuary")
    req = TravelRequest(interests=["nature", "wildlife"])
    score, expl = calculate_preference_match(dest, req)
    assert score is not None
    assert score >= 90.0
    assert "direct category match" in expl.lower()


def test_no_preference_match():
    dest = make_dummy_destination(category="Heritage", description="Ancient temple ruins")
    req = TravelRequest(interests=["beach", "scuba"])
    score, expl = calculate_preference_match(dest, req)
    assert score is not None
    assert score <= 25.0
    assert "does not match" in expl.lower()


def test_missing_preference_returns_none_and_missing_quality():
    dest = make_dummy_destination()
    req = TravelRequest()  # empty interests, no hidden gem preference
    score, expl = calculate_preference_match(dest, req)
    assert score is None
    assert "renormalized" in expl.lower()


def test_partial_description_match():
    dest = make_dummy_destination(
        category="Adventure",
        description="A river rafting base near an ancient cultural heritage fortress."
    )
    req = TravelRequest(interests=["heritage"])
    score, expl = calculate_preference_match(dest, req)
    assert score is not None
    assert score == 45.0
    assert "keywords found in description" in expl.lower()


def test_hidden_gem_alignment_bonus():
    dest = make_dummy_destination(category="Nature", is_hidden_gem=True)
    req_match = TravelRequest(interests=["nature"], prefer_hidden_gems=True)
    req_mismatch = TravelRequest(interests=["nature"], prefer_hidden_gems=False)

    score_match, _ = calculate_preference_match(dest, req_match)
    score_mismatch, _ = calculate_preference_match(dest, req_mismatch)

    assert score_match > score_mismatch
