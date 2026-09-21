"""
Unit tests for the Destination Similarity Service.
Validates category matching, geographic proximity, crowd similarity,
configurable weights validation, and custom calibration.
"""

import pytest
from app.models.destination import Destination
from app.services.destination_similarity import (
    DEFAULT_SIMILARITY_WEIGHTS,
    calculate_destination_similarity,
    validate_similarity_weights,
)


def make_dest(
    id=1,
    name="Spot A",
    category="Nature",
    state="Uttarakhand",
    city="Rishikesh",
    latitude=30.0869,
    longitude=78.2676,
    entry_fee=0.0,
    base_crowd_level="moderate",
    is_hidden_gem=False,
    description="Lush green forested sanctuary with river trails.",
) -> Destination:
    return Destination(
        id=id,
        name=name,
        slug=f"spot-{id}",
        category=category,
        state=state,
        city=city,
        latitude=latitude,
        longitude=longitude,
        entry_fee=entry_fee,
        base_crowd_level=base_crowd_level,
        is_hidden_gem=is_hidden_gem,
        description=description,
    )


def test_similarity_weights_validation():
    # Valid default weights
    assert validate_similarity_weights(DEFAULT_SIMILARITY_WEIGHTS) is True

    # Invalid weights: don't sum to 1.0
    bad_weights = {"category": 0.5, "location": 0.3, "crowd_gem": 0.2, "budget": 0.5}
    assert validate_similarity_weights(bad_weights) is False

    # Invalid weights: missing key
    missing_key = {"category": 0.5, "location": 0.5}
    assert validate_similarity_weights(missing_key) is False

    # Invalid weights: negative value
    neg_weights = {"category": 1.2, "location": -0.2, "crowd_gem": 0.0, "budget": 0.0}
    assert validate_similarity_weights(neg_weights) is False


def test_identical_destinations_high_similarity():
    dest1 = make_dest(id=1, name="Spot 1")
    dest2 = make_dest(id=2, name="Spot 2")
    sim, comp, expl = calculate_destination_similarity(dest1, dest2)
    assert sim >= 95.0
    assert comp["category"] == 100.0
    assert comp["budget"] == 100.0


def test_different_category_lower_similarity():
    dest_nature = make_dest(id=1, category="Nature", description="Serene natural waterfall")
    dest_heritage = make_dest(id=2, category="Heritage", description="Ancient royal palace fort", state="Rajasthan", city="Jaipur")

    sim_diff, comp, _ = calculate_destination_similarity(dest_nature, dest_heritage)
    dest_nature_similar = make_dest(id=3, category="Nature", description="Scenic nature mountain valley")
    sim_same, _, _ = calculate_destination_similarity(dest_nature, dest_nature_similar)

    assert sim_same > sim_diff


def test_custom_similarity_weights_calibration():
    dest1 = make_dest(id=1, category="Heritage", state="Rajasthan", city="Jaipur", latitude=26.9124, longitude=75.7873)
    dest2 = make_dest(id=2, category="Heritage", state="Kerala", city="Kochi", latitude=9.9312, longitude=76.2673)  # Same category, ~2000 km away

    # Standard weights (category=0.40, location=0.30)
    sim_std, _, _ = calculate_destination_similarity(dest1, dest2)

    # Location-heavy calibrated weights (category=0.10, location=0.70, crowd_gem=0.10, budget=0.10)
    location_heavy = {"category": 0.10, "location": 0.70, "crowd_gem": 0.10, "budget": 0.10}
    sim_loc_heavy, _, _ = calculate_destination_similarity(dest1, dest2, weights=location_heavy)

    # Far away destination should score much lower when location weight is high
    assert sim_loc_heavy < sim_std
