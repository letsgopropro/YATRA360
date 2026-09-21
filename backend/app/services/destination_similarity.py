"""
YATRA360 — Destination Similarity Service
Evaluates content-based and geographic similarity between a source destination
and candidate destinations to identify suitable alternatives.
Weights are centrally configurable and calibratable.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# Centralized Configurable Similarity Weights
# ============================================================================

DEFAULT_SIMILARITY_WEIGHTS: Dict[str, float] = {
    "category": 0.40,
    "location": 0.30,
    "crowd_gem": 0.20,
    "budget": 0.10,
}


def validate_similarity_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that similarity weights contain the expected keys, are non-negative,
    and sum to 1.0 within a standard floating tolerance.
    """
    expected_keys = {"category", "location", "crowd_gem", "budget"}
    if not expected_keys.issubset(weights.keys()):
        return False
    if any(w < 0.0 for w in weights.values()):
        return False
    total = sum(weights[k] for k in expected_keys)
    return math.isclose(total, 1.0, rel_tol=1e-3, abs_tol=1e-3)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two coordinates in kilometers."""
    earth_radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_km * c


def calculate_destination_similarity(
    source: Any,
    candidate: Any,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, Dict[str, float], str]:
    """
    Calculate normalized similarity (0-100) between a source destination and candidate.

    Returns:
        Tuple[float, Dict[str, float], str]:
            - overall_similarity: 0.0 to 100.0 score.
            - components: breakdown of sub-similarity scores.
            - explanation: human-readable explanation of similarity factors.
    """
    applied_weights = weights if weights is not None else DEFAULT_SIMILARITY_WEIGHTS
    if not validate_similarity_weights(applied_weights):
        raise ValueError(f"Invalid similarity weights: {applied_weights}. Must sum to 1.0.")

    # 1. Category / Theme Similarity (Default: 40%)
    source_cat = (getattr(source, "category", "") or "").strip().lower()
    cand_cat = (getattr(candidate, "category", "") or "").strip().lower()

    if source_cat == cand_cat and source_cat:
        cat_sim = 100.0
        cat_desc = f"Identical category ({source.category})"
    elif source_cat in cand_cat or cand_cat in source_cat:
        cat_sim = 75.0
        cat_desc = f"Related category ({source.category} ~ {candidate.category})"
    else:
        # Check description keyword overlap
        s_desc = (getattr(source, "description", "") or "").lower()
        c_desc = (getattr(candidate, "description", "") or "").lower()
        s_words = set(w for w in s_desc.split() if len(w) > 4)
        c_words = set(w for w in c_desc.split() if len(w) > 4)
        overlap = len(s_words & c_words)
        cat_sim = min(50.0, overlap * 5.0)
        cat_desc = f"Distinct category ({source.category} vs {candidate.category})"

    # 2. Geographic & Location Proximity (Default: 30%)
    source_state = (getattr(source, "state", "") or "").strip().lower()
    cand_state = (getattr(candidate, "state", "") or "").strip().lower()
    source_city = (getattr(source, "city", "") or "").strip().lower()
    cand_city = (getattr(candidate, "city", "") or "").strip().lower()

    s_lat = getattr(source, "latitude", None)
    s_lon = getattr(source, "longitude", None)
    c_lat = getattr(candidate, "latitude", None)
    c_lon = getattr(candidate, "longitude", None)

    if s_lat is not None and s_lon is not None and c_lat is not None and c_lon is not None:
        dist_km = haversine_distance(s_lat, s_lon, c_lat, c_lon)
        if dist_km <= 50.0:
            loc_sim = 100.0
        elif dist_km <= 200.0:
            loc_sim = 85.0
        elif dist_km <= 500.0:
            loc_sim = 65.0
        elif dist_km <= 1000.0:
            loc_sim = 40.0
        else:
            loc_sim = max(10.0, 40.0 - (dist_km - 1000.0) / 100.0)
        loc_desc = f"{dist_km:.0f} km away"
    elif source_city and source_city == cand_city:
        loc_sim = 95.0
        loc_desc = f"Same city ({candidate.city})"
    elif source_state and source_state == cand_state:
        loc_sim = 75.0
        loc_desc = f"Same state ({candidate.state})"
    else:
        loc_sim = 30.0
        loc_desc = f"Different state ({candidate.state})"

    # 3. Crowd Level & Hidden-Gem Affinity (Default: 20%)
    source_crowd = (getattr(source, "base_crowd_level", "") or "moderate").strip().lower()
    cand_crowd = (getattr(candidate, "base_crowd_level", "") or "moderate").strip().lower()
    s_gem = bool(getattr(source, "is_hidden_gem", False))
    c_gem = bool(getattr(candidate, "is_hidden_gem", False))

    crowd_order = {"low": 1, "moderate": 2, "high": 3, "overcrowded": 4}
    s_order = crowd_order.get(source_crowd, 2)
    c_order = crowd_order.get(cand_crowd, 2)
    crowd_diff = abs(s_order - c_order)

    if crowd_diff == 0:
        crowd_sim = 100.0
    elif crowd_diff == 1:
        crowd_sim = 70.0
    else:
        crowd_sim = 30.0

    gem_sim = 100.0 if s_gem == c_gem else 50.0
    crowd_gem_sim = 0.6 * crowd_sim + 0.4 * gem_sim

    # 4. Budget & Entry Fee Similarity (Default: 10%)
    s_fee = float(getattr(source, "entry_fee", 0.0) or 0.0)
    c_fee = float(getattr(candidate, "entry_fee", 0.0) or 0.0)

    if s_fee == 0.0 and c_fee == 0.0:
        budget_sim = 100.0
    else:
        max_fee = max(s_fee, c_fee)
        diff = abs(s_fee - c_fee)
        budget_sim = max(0.0, 100.0 * (1.0 - (diff / max(1.0, max_fee))))

    # Compute overall weighted similarity
    overall = (
        applied_weights["category"] * cat_sim
        + applied_weights["location"] * loc_sim
        + applied_weights["crowd_gem"] * crowd_gem_sim
        + applied_weights["budget"] * budget_sim
    )
    overall = max(0.0, min(100.0, overall))

    components = {
        "category": round(cat_sim, 1),
        "location": round(loc_sim, 1),
        "crowd_gem": round(crowd_gem_sim, 1),
        "budget": round(budget_sim, 1),
    }

    explanation = (
        f"Similarity {overall:.1f}/100 based on {cat_desc}, {loc_desc}, "
        f"crowd profile '{cand_crowd}', and fee ₹{c_fee:.0f}."
    )

    return round(overall, 1), components, explanation
