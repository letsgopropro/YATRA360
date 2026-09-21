"""
YATRA360 — Dynamic Destination Scoring Engine
Calculates transparent, normalized suitability scores (0-100) for destinations.

Scoring Formula (Project Proposal):
    S(d,u) = 0.25 * Preference + 0.20 * Safety + 0.20 * Crowd
           + 0.15 * Accessibility + 0.10 * Cost + 0.10 * Weather

Features:
- Centralized configurable weights with validation.
- Deterministic missing-data handling via proportional weight renormalization.
- Clear data quality tagging: 'real', 'fallback', or 'missing'.
- Centralized overcrowding threshold definition.
- Mathematical transparency and explainability suitable for academic viva evaluation.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.scoring import (
    DestinationScoreResponse,
    ScoringComponents,
    ScoringWeights,
    TravelRequest,
)
from app.services.preference_matcher import calculate_preference_match

# ============================================================================
# Centralized Configurable Weights & Thresholds
# ============================================================================

DEFAULT_WEIGHTS: Dict[str, float] = {
    "preference": 0.25,
    "safety": 0.20,
    "crowd": 0.20,
    "accessibility": 0.15,
    "cost": 0.10,
    "weather": 0.10,
}

# Alias mapping for backward compatibility with schema field names
WEIGHT_KEY_ALIASES: Dict[str, str] = {
    "preference_match": "preference",
    "crowd_suitability": "crowd",
    "accessibility_distance": "accessibility",
    "cost_suitability": "cost",
    "weather_condition": "weather",
}

# Configurable Overcrowding Threshold
OVERCROWDING_THRESHOLD: str = "high"


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that scoring weights are non-negative and sum to 1.0 (within floating tolerance).
    Accepts either standard or schema alias keys.
    """
    if not weights:
        return False
    canonical_weights: Dict[str, float] = {}
    for k, v in weights.items():
        canonical_k = WEIGHT_KEY_ALIASES.get(k, k)
        canonical_weights[canonical_k] = v

    expected_keys = {"preference", "safety", "crowd", "accessibility", "cost", "weather"}
    if not expected_keys.issubset(canonical_weights.keys()):
        return False
    if any(v < 0.0 for v in canonical_weights.values()):
        return False

    total = sum(canonical_weights[k] for k in expected_keys)
    return math.isclose(total, 1.0, rel_tol=1e-3, abs_tol=1e-3)


def is_overcrowded(destination: Any, threshold: str = OVERCROWDING_THRESHOLD) -> bool:
    """
    Check whether a destination exceeds the overcrowding threshold.
    Returns True if crowd level is 'high' or 'overcrowded'.
    """
    crowd_level = (getattr(destination, "base_crowd_level", "") or "").strip().lower()
    if threshold.lower() == "high":
        return crowd_level in {"high", "overcrowded"}
    return crowd_level == threshold.lower()


# Backward compatibility dictionary
WEIGHTS = {
    "preference_match": 0.25,
    "safety": 0.20,
    "crowd_suitability": 0.20,
    "accessibility_distance": 0.15,
    "cost_suitability": 0.10,
    "weather_condition": 0.10,
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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


# ============================================================================
# Component 1: Preference Match
# ============================================================================

def evaluate_preference_match(
    destination: Any,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[Optional[float], str]:
    """
    Delegates to modular preference matcher.
    Returns (score_0_100, explanation).
    """
    return calculate_preference_match(destination, travel_request)


# ============================================================================
# Component 2: Safety Score
# ============================================================================

def calculate_safety_score(
    destination: Any,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[Optional[float], str]:
    """
    Normalize safety indicator (1.0 - 5.0 scale) into 0 - 100 scale.
    If safety data is missing, returns (None, explanation).
    Returns (score_0_100, explanation).
    """
    raw_rating = getattr(destination, "safety_rating", None)

    if raw_rating is None:
        return (
            None,
            "Safety rating unavailable in destination records; safety component excluded and weight renormalized.",
        )

    clamped_rating = max(1.0, min(5.0, float(raw_rating)))
    normalized_score = (clamped_rating / 5.0) * 100.0

    explanation = (
        f"Database safety baseline rating {clamped_rating:.1f}/5.0 normalized to {normalized_score:.1f} "
        f"(prototype baseline, not an official safety guarantee)."
    )
    return round(normalized_score, 1), explanation


# ============================================================================
# Component 3: Crowd Suitability
# ============================================================================

DEFAULT_CROWD_PRESSURE_SCORES: Dict[str, float] = {
    "low": 100.0,
    "moderate": 60.0,
    "high": 20.0,
    "overcrowded": 10.0,
}

PREFERRED_CROWD_SCORES: Dict[str, Dict[str, float]] = {
    "low": {
        "low": 100.0,
        "moderate": 60.0,
        "high": 20.0,
        "overcrowded": 10.0,
    },
    "moderate": {
        "moderate": 100.0,
        "low": 80.0,
        "high": 30.0,
        "overcrowded": 15.0,
    },
    "high": {
        "high": 100.0,
        "moderate": 70.0,
        "low": 50.0,
        "overcrowded": 30.0,
    },
}


def calculate_crowd_suitability(
    destination: Any,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[Optional[float], str]:
    """
    Evaluate crowd suitability based on destination crowd level and user preference.
    Higher crowd pressure yields lower crowd suitability.
    Returns (score_0_100, explanation).
    """
    raw_crowd = getattr(destination, "base_crowd_level", None)
    if not raw_crowd:
        return (
            None,
            "Crowd telemetry/level unavailable; crowd component excluded and weight renormalized.",
        )

    dest_crowd = raw_crowd.strip().lower()
    user_pref = (
        travel_request.preferred_crowd_level.strip().lower()
        if travel_request and travel_request.preferred_crowd_level
        else None
    )

    if user_pref and user_pref in PREFERRED_CROWD_SCORES:
        crowd_table = PREFERRED_CROWD_SCORES[user_pref]
        score = crowd_table.get(dest_crowd, 60.0)
        explanation = (
            f"User preferred '{user_pref}' crowd level matched against destination level '{dest_crowd}' "
            f"-> score {score:.1f} (prototype baseline)."
        )
    else:
        score = DEFAULT_CROWD_PRESSURE_SCORES.get(dest_crowd, 60.0)
        explanation = (
            f"Evaluated general crowd pressure for level '{dest_crowd}' -> score {score:.1f} "
            f"(prototype baseline, lower crowd = higher suitability)."
        )

    score = max(0.0, min(100.0, score))
    return round(score, 1), explanation


# ============================================================================
# Component 4: Accessibility / Distance Score
# ============================================================================

def calculate_accessibility_distance_score(
    destination: Any,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[Optional[float], str]:
    """
    Calculate composite score incorporating accessibility accommodations and geodesic distance.
    Returns (score_0_100, explanation).
    """
    requires_access = bool(travel_request.requires_accessibility) if travel_request else False
    access_info = getattr(destination, "accessibility_info", None)

    # 1. Accessibility Sub-Score
    if requires_access:
        if access_info:
            info_lower = access_info.lower()
            positive_kw = ["wheelchair", "ramp", "ramped", "paved", "battery cart", "level", "elevator", "flat", "boardwalk"]
            negative_kw = ["steep", "stairs", "steps", "trek", "not wheelchair", "boulder", "rocky", "rugged", "climb"]

            has_pos = any(k in info_lower for k in positive_kw)
            has_neg = any(k in info_lower for k in negative_kw)

            if has_pos and not has_neg:
                access_score = 95.0
                access_expl = "Documented wheelchair/ramp facilities match accessibility requirements."
            elif has_neg:
                access_score = 30.0
                access_expl = "Terrain features steep stairs, rugged paths, or difficult access."
            else:
                access_score = 65.0
                access_expl = "Moderate accessibility terrain noted."
        else:
            access_score = 50.0
            access_expl = "Accessibility information unverified; applying cautious prototype baseline (50.0)."
    else:
        access_score = 80.0
        access_expl = "General travel accessibility baseline applied."

    # 2. Distance Sub-Score
    user_lat = getattr(travel_request, "user_latitude", None) if travel_request else None
    user_lon = getattr(travel_request, "user_longitude", None) if travel_request else None
    dest_lat = getattr(destination, "latitude", None)
    dest_lon = getattr(destination, "longitude", None)

    has_coords = (
        user_lat is not None
        and user_lon is not None
        and dest_lat is not None
        and dest_lon is not None
    )

    if has_coords:
        distance_km = haversine_distance_km(user_lat, user_lon, dest_lat, dest_lon)
        max_dist = getattr(travel_request, "max_distance_km", None) or 1000.0

        if distance_km <= max_dist:
            dist_score = 100.0 - (distance_km / max_dist) * 50.0
            dist_expl = f"Distance {distance_km:.1f} km is within requested radius {max_dist:.0f} km."
        else:
            overshoot = (distance_km - max_dist) / max_dist
            dist_score = max(10.0, 50.0 - overshoot * 40.0)
            dist_expl = f"Distance {distance_km:.1f} km exceeds desired radius {max_dist:.0f} km."
    else:
        dist_score = 70.0
        dist_expl = "User starting location not provided; neutral proximity baseline (70.0) used."

    composite_score = 0.5 * access_score + 0.5 * dist_score
    composite_score = max(0.0, min(100.0, composite_score))
    explanation = f"{access_expl} | {dist_expl}"

    return round(composite_score, 1), explanation


# ============================================================================
# Component 5: Cost Suitability
# ============================================================================

def calculate_cost_suitability(
    destination: Any,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[Optional[float], str]:
    """
    Compare destination entry fee against user budget.
    - If entry fee is missing from DB: returns (None, explanation).
    - If entry fee is 0.0: maximum suitability (100.0).
    - If no budget specified: unconstrained baseline (80.0) applied.
    Returns (score_0_100, explanation).
    """
    raw_fee = getattr(destination, "entry_fee", None)
    if raw_fee is None:
        return (
            None,
            "Entry fee / cost data unavailable; cost component excluded and weight renormalized.",
        )

    entry_fee = float(raw_fee)
    budget = getattr(travel_request, "budget", None) if travel_request else None

    if budget is None or budget <= 0:
        if entry_fee == 0.0:
            return 100.0, "Free entry (₹0.0) provides maximum cost suitability."
        score = 80.0
        explanation = "No budget constraint specified; unconstrained baseline (80.0) applied."
        return score, explanation

    if entry_fee == 0.0:
        score = 100.0
        explanation = f"Free entry (₹0.0) provides maximum cost suitability within budget of ₹{budget:.0f}."
    elif entry_fee <= budget:
        ratio = entry_fee / budget
        if ratio <= 0.10:
            score = 95.0
        elif ratio <= 0.30:
            score = 85.0
        elif ratio <= 0.60:
            score = 75.0
        else:
            score = 65.0
        explanation = (
            f"Entry fee ₹{entry_fee:.0f} is within budget ₹{budget:.0f} "
            f"({ratio*100:.1f}% of budget; note: entry fee does not cover travel/lodging)."
        )
    else:
        ratio = entry_fee / budget
        score = max(0.0, 50.0 - (ratio - 1.0) * 50.0)
        explanation = (
            f"Entry fee ₹{entry_fee:.0f} exceeds user allocated budget ₹{budget:.0f} "
            f"(over-budget penalty applied)."
        )

    score = max(0.0, min(100.0, score))
    return round(score, 1), explanation


# ============================================================================
# Component 6: Weather / Condition Suitability
# ============================================================================

def calculate_weather_condition_score(
    destination: Any,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[Optional[float], str]:
    """
    Modular plug-in interface for weather/condition suitability.
    - If destination explicitly has weather_condition=None: marked missing.
    - If user provides weather preference: evaluated via climate heuristics.
    - Default prototype: neutral baseline (70.0) applied as documented fallback.
    Returns (score_0_100, explanation).
    """
    # Check if weather data is explicitly flagged as unavailable
    if hasattr(destination, "weather_data_available") and not destination.weather_data_available:
        return (
            None,
            "Weather data genuinely unavailable; weather component excluded and weight renormalized.",
        )

    weather_pref = (
        travel_request.weather_preference.strip().lower()
        if travel_request and travel_request.weather_preference
        else None
    )
    if not weather_pref and travel_request and getattr(travel_request, "preferred_weather", None):
        weather_pref = travel_request.preferred_weather.strip().lower()

    dest_category = (getattr(destination, "category", "") or "").strip().lower()

    if not weather_pref:
        score = 70.0
        explanation = "Neutral weather prototype baseline (70.0) applied; live weather API integration pending."
    else:
        if ("cool" in weather_pref or "cold" in weather_pref) and dest_category in {"hill station", "adventure"}:
            score = 90.0
            explanation = f"Climate preference '{weather_pref}' aligns with '{getattr(destination, 'category', '')}' setting."
        elif ("warm" in weather_pref or "sunny" in weather_pref) and dest_category in {"beach"}:
            score = 90.0
            explanation = f"Climate preference '{weather_pref}' aligns with coastal '{getattr(destination, 'category', '')}' setting."
        elif "pleasant" in weather_pref:
            score = 80.0
            explanation = "General pleasant climate preference accommodated at baseline (80.0)."
        else:
            score = 70.0
            explanation = f"Weather preference '{weather_pref}' recorded; neutral prototype baseline (70.0) used."

    score = max(0.0, min(100.0, score))
    return round(score, 1), explanation


# ============================================================================
# Master Scoring Function
# ============================================================================

def calculate_destination_score(
    destination: Any,
    travel_request: Optional[TravelRequest] = None,
    weights: Optional[Dict[str, float]] = None,
) -> DestinationScoreResponse:
    """
    Master scoring function computing all 6 components, applying dynamic
    proportional weight renormalization when data is missing, and formatting
    complete transparent explainability results.

    Returns DestinationScoreResponse.
    """
    raw_weights = weights if weights is not None else DEFAULT_WEIGHTS

    # Normalize weights keys
    canonical_weights: Dict[str, float] = {}
    for k, v in raw_weights.items():
        canon_k = WEIGHT_KEY_ALIASES.get(k, k)
        canonical_weights[canon_k] = v

    # Compute individual component scores
    s_pref, exp_pref = evaluate_preference_match(destination, travel_request)
    s_safety, exp_safety = calculate_safety_score(destination, travel_request)
    s_crowd, exp_crowd = calculate_crowd_suitability(destination, travel_request)
    s_access, exp_access = calculate_accessibility_distance_score(destination, travel_request)
    s_cost, exp_cost = calculate_cost_suitability(destination, travel_request)
    s_weather, exp_weather = calculate_weather_condition_score(destination, travel_request)

    scores_map: Dict[str, Optional[float]] = {
        "preference": s_pref,
        "safety": s_safety,
        "crowd": s_crowd,
        "accessibility": s_access,
        "cost": s_cost,
        "weather": s_weather,
    }

    explanations_map: Dict[str, str] = {
        "preference_match": exp_pref,
        "safety": exp_safety,
        "crowd_suitability": exp_crowd,
        "accessibility_distance": exp_access,
        "cost_suitability": exp_cost,
        "weather_condition": exp_weather,
    }

    # Deterministic Data Quality Tracking
    data_quality_map: Dict[str, str] = {
        "preference": "real" if s_pref is not None else "missing",
        "safety": "missing" if s_safety is None else ("real" if getattr(destination, "safety_records", None) else "fallback"),
        "crowd": "missing" if s_crowd is None else ("real" if getattr(destination, "crowd_metrics", None) else "fallback"),
        "accessibility": "real" if (travel_request and (travel_request.user_latitude is not None or travel_request.requires_accessibility)) else "fallback",
        "cost": "missing" if s_cost is None else ("real" if (travel_request and travel_request.budget is not None) or getattr(destination, "entry_fee", None) == 0.0 else "fallback"),
        "weather": "missing" if s_weather is None else ("real" if getattr(destination, "live_weather_condition", None) else "fallback"),
    }

    # Proportional Weight Renormalization for Available Components
    available_keys = [k for k, v in scores_map.items() if v is not None]
    total_available_weight = sum(canonical_weights.get(k, 0.0) for k in available_keys)

    applied_weights: Dict[str, float] = {}
    if total_available_weight > 0.0:
        for k in available_keys:
            applied_weights[k] = round(canonical_weights.get(k, 0.0) / total_available_weight, 4)
        for k in scores_map:
            if k not in applied_weights:
                applied_weights[k] = 0.0
    else:
        applied_weights = {k: 0.0 for k in scores_map}

    # Calculate overall weighted score
    overall = sum(applied_weights[k] * (scores_map[k] or 0.0) for k in available_keys)
    overall = max(0.0, min(100.0, round(overall, 1)))

    components = ScoringComponents(
        preference_match=s_pref,
        safety=s_safety,
        crowd_suitability=s_crowd,
        accessibility_distance=s_access,
        cost_suitability=s_cost,
        weather_condition=s_weather,
    )

    weights_response = ScoringWeights(
        preference_match=canonical_weights.get("preference", 0.25),
        safety=canonical_weights.get("safety", 0.20),
        crowd_suitability=canonical_weights.get("crowd", 0.20),
        accessibility_distance=canonical_weights.get("accessibility", 0.15),
        cost_suitability=canonical_weights.get("cost", 0.10),
        weather_condition=canonical_weights.get("weather", 0.10),
    )

    dest_id = getattr(destination, "id", 0)
    dest_name = getattr(destination, "name", "Unknown Destination")
    dest_slug = getattr(destination, "slug", "unknown-slug")

    return DestinationScoreResponse(
        destination_id=dest_id,
        destination_name=dest_name,
        destination_slug=dest_slug,
        overall_score=overall,
        components=components,
        score_breakdown=scores_map,
        weights=weights_response,
        applied_weights=applied_weights,
        data_quality=data_quality_map,
        explanations=explanations_map,
    )
