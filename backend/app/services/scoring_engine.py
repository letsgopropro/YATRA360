"""
YATRA360 — Dynamic Destination Scoring Engine
Calculates transparent, normalized suitability scores (0-100) for destinations.

Scoring Formula (Project Proposal):
    Destination Score =
        0.25 * Preference Match
      + 0.20 * Safety
      + 0.20 * Crowd Suitability
      + 0.15 * Accessibility / Distance
      + 0.10 * Cost Suitability
      + 0.10 * Weather / Condition Suitability

All components are strictly normalized to a 0-100 scale.
Weights sum to 1.00.
"""

import math
from typing import Dict, List, Optional, Tuple

from app.models.destination import Destination
from app.schemas.scoring import (
    DestinationScoreResponse,
    ScoringComponents,
    ScoringWeights,
    TravelRequest,
)

# ============================================================================
# Configurable Weights & Thresholds
# ============================================================================

WEIGHTS = {
    "preference_match": 0.25,
    "safety": 0.20,
    "crowd_suitability": 0.20,
    "accessibility_distance": 0.15,
    "cost_suitability": 0.10,
    "weather_condition": 0.10,
}

# General crowd-pressure mapping (when user specifies no crowd preference)
DEFAULT_CROWD_PRESSURE_SCORES: Dict[str, float] = {
    "low": 100.0,
    "moderate": 60.0,
    "high": 20.0,
}

# User preference-dependent crowd mapping
PREFERRED_CROWD_SCORES: Dict[str, Dict[str, float]] = {
    "low": {
        "low": 100.0,
        "moderate": 60.0,
        "high": 20.0,
    },
    "moderate": {
        "moderate": 100.0,
        "low": 80.0,
        "high": 30.0,
    },
    "high": {
        "high": 100.0,
        "moderate": 70.0,
        "low": 50.0,
    },
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two geographic coordinates in kilometers."""
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
# Component 1: Preference Match (0.25)
# ============================================================================

def calculate_preference_match(
    destination: Destination,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[float, str]:
    """
    Compare user interests against destination category and characteristics.
    Returns (score_0_100, explanation).
    """
    if not travel_request or not travel_request.interests:
        # Neutral open-preference baseline
        score = 70.0
        explanation = "No specific category interests provided; applying open neutral baseline (70.0)."
        return score, explanation

    dest_category = (destination.category or "").strip().lower()
    user_interests = [i.strip().lower() for i in travel_request.interests if i.strip()]

    if not user_interests:
        return 70.0, "Empty interests list; applying open neutral baseline (70.0)."

    # Direct match or substring containment
    matched_interest = None
    for interest in user_interests:
        if interest in dest_category or dest_category in interest:
            matched_interest = interest
            break

    if matched_interest:
        # High affinity for matching category
        score = 90.0
        explanation = f"Direct category match for interest '{matched_interest.title()}' with '{destination.category}'."
        
        # Alignment with hidden-gem preference
        if travel_request.prefer_hidden_gems is not None:
            if travel_request.prefer_hidden_gems == destination.is_hidden_gem:
                score += 10.0
                explanation += " Hidden-gem preference fully aligned (+10 bonus)."
    else:
        # Check description for keyword mention as a partial match
        desc_lower = (destination.description or "").lower()
        partial_match = any(i in desc_lower for i in user_interests)
        if partial_match:
            score = 45.0
            explanation = f"Category '{destination.category}' did not match primary interests, but relevant keywords found in description."
        else:
            score = 20.0
            explanation = f"Destination category '{destination.category}' does not match specified interests ({', '.join(travel_request.interests)})."

        if travel_request.prefer_hidden_gems is not None and travel_request.prefer_hidden_gems == destination.is_hidden_gem:
            score += 10.0
            explanation += " Hidden-gem preference bonus applied (+10)."

    score = max(0.0, min(100.0, score))
    return round(score, 1), explanation


# ============================================================================
# Component 2: Safety Score (0.20)
# ============================================================================

def calculate_safety_score(
    destination: Destination,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[float, str]:
    """
    Normalize the database safety_rating (1.0 - 5.0) into a 0 - 100 scale.
    Example: 1 -> 20, 2 -> 40, 3 -> 60, 4 -> 80, 5 -> 100.
    Returns (score_0_100, explanation).
    """
    raw_rating = getattr(destination, "safety_rating", 4.0)
    if raw_rating is None:
        raw_rating = 4.0

    clamped_rating = max(1.0, min(5.0, float(raw_rating)))
    normalized_score = (clamped_rating / 5.0) * 100.0

    explanation = (
        f"Database safety baseline rating {clamped_rating:.1f}/5.0 normalized to {normalized_score:.1f} "
        f"(prototype baseline, not an official safety guarantee)."
    )
    return round(normalized_score, 1), explanation


# ============================================================================
# Component 3: Crowd Suitability (0.20)
# ============================================================================

def calculate_crowd_suitability(
    destination: Destination,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[float, str]:
    """
    Evaluate crowd suitability based on destination crowd level and user preference.
    Returns (score_0_100, explanation).
    """
    dest_crowd = (destination.base_crowd_level or "moderate").strip().lower()
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
            f"Evaluated general crowd pressure for level '{dest_crowd}' "
            f"-> score {score:.1f} (prototype baseline, lower crowd = higher suitability)."
        )

    score = max(0.0, min(100.0, score))
    return round(score, 1), explanation


# ============================================================================
# Component 4: Accessibility / Distance Score (0.15)
# ============================================================================

def calculate_accessibility_distance_score(
    destination: Destination,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[float, str]:
    """
    Calculate composite score incorporating accessibility requirements and distance proximity.
    Returns (score_0_100, explanation).
    """
    # 1. Accessibility Evaluation
    requires_access = travel_request.requires_accessibility if travel_request else False
    access_info = (destination.accessibility_info or "").lower()

    if requires_access:
        positive_keywords = ["wheelchair", "ramp", "ramped", "paved", "battery cart", "level", "elevator", "flat", "boardwalk"]
        negative_keywords = ["steep", "stairs", "steps", "trek", "not wheelchair", "boulder", "rocky", "rugged", "climb"]

        has_positive = any(k in access_info for k in positive_keywords)
        has_negative = any(k in access_info for k in negative_keywords)

        if has_positive and not has_negative:
            access_score = 95.0
            access_expl = "Documented wheelchair/ramp facilities match accessibility requirements."
        elif has_negative:
            access_score = 30.0
            access_expl = "Terrain features steep stairs, rugged paths, or difficult access."
        elif destination.accessibility_info is None:
            access_score = 50.0
            access_expl = "Accessibility information unverified; applying cautious prototype baseline (50.0)."
        else:
            access_score = 65.0
            access_expl = "Moderate accessibility terrain noted."
    else:
        access_score = 80.0
        access_expl = "General travel accessibility baseline applied."

    # 2. Distance Evaluation
    has_coords = (
        travel_request
        and travel_request.user_latitude is not None
        and travel_request.user_longitude is not None
    )

    if has_coords:
        distance_km = haversine_distance_km(
            travel_request.user_latitude,
            travel_request.user_longitude,
            destination.latitude,
            destination.longitude,
        )
        max_dist = travel_request.max_distance_km or 1000.0

        if distance_km <= max_dist:
            # Linear decay from 100 (0 km) down to 50 (max_dist km)
            dist_score = 100.0 - (distance_km / max_dist) * 50.0
            dist_expl = f"Distance {distance_km:.1f} km is within requested radius {max_dist:.0f} km."
        else:
            # Over radius penalty
            overshoot_ratio = (distance_km - max_dist) / max_dist
            dist_score = max(10.0, 50.0 - overshoot_ratio * 40.0)
            dist_expl = f"Distance {distance_km:.1f} km exceeds desired radius {max_dist:.0f} km."
    else:
        dist_score = 70.0
        dist_expl = "User starting location not provided; neutral proximity baseline (70.0) used."

    # Blended composite (equal weighting between accessibility and distance)
    composite_score = 0.5 * access_score + 0.5 * dist_score
    composite_score = max(0.0, min(100.0, composite_score))
    
    explanation = f"{access_expl} | {dist_expl}"
    return round(composite_score, 1), explanation


# ============================================================================
# Component 5: Cost Suitability (0.10)
# ============================================================================

def calculate_cost_suitability(
    destination: Destination,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[float, str]:
    """
    Compare destination entry fee against user budget.
    Honest limitation: entry fee reflects admission only, not full trip cost.
    Returns (score_0_100, explanation).
    """
    entry_fee = getattr(destination, "entry_fee", 0.0) or 0.0
    budget = travel_request.budget if travel_request and travel_request.budget is not None else None

    if budget is None or budget <= 0:
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
# Component 6: Weather / Condition Suitability (0.10)
# ============================================================================

def calculate_weather_condition_score(
    destination: Destination,
    travel_request: Optional[TravelRequest] = None
) -> Tuple[float, str]:
    """
    Modular plug-in interface for weather/condition suitability.
    In the prototype stage, uses a documented neutral default (70.0) with heuristic alignment.
    Returns (score_0_100, explanation).
    """
    weather_pref = (
        travel_request.weather_preference.strip().lower()
        if travel_request and travel_request.weather_preference
        else None
    )

    dest_category = (destination.category or "").strip().lower()

    if not weather_pref:
        score = 70.0
        explanation = "Neutral weather prototype baseline (70.0) applied; live weather API integration pending."
    else:
        # Heuristic alignment for climate preferences
        if ("cool" in weather_pref or "cold" in weather_pref) and dest_category in {"hill station", "adventure"}:
            score = 90.0
            explanation = f"Climate preference '{weather_pref}' aligns with '{destination.category}' setting."
        elif ("warm" in weather_pref or "sunny" in weather_pref) and dest_category in {"beach"}:
            score = 90.0
            explanation = f"Climate preference '{weather_pref}' aligns with coastal '{destination.category}' setting."
        elif "pleasant" in weather_pref:
            score = 80.0
            explanation = f"General pleasant climate preference accommodated at baseline (80.0)."
        else:
            score = 70.0
            explanation = f"Weather preference '{weather_pref}' recorded; neutral prototype baseline (70.0) used."

    score = max(0.0, min(100.0, score))
    return round(score, 1), explanation


# ============================================================================
# Master Function: Calculate Overall Destination Score
# ============================================================================

def calculate_destination_score(
    destination: Destination,
    travel_request: Optional[TravelRequest] = None
) -> DestinationScoreResponse:
    """
    Master scoring function computing all 6 components and the weighted total score.
    Returns DestinationScoreResponse.
    """
    s_pref, exp_pref = calculate_preference_match(destination, travel_request)
    s_safety, exp_safety = calculate_safety_score(destination, travel_request)
    s_crowd, exp_crowd = calculate_crowd_suitability(destination, travel_request)
    s_access, exp_access = calculate_accessibility_distance_score(destination, travel_request)
    s_cost, exp_cost = calculate_cost_suitability(destination, travel_request)
    s_weather, exp_weather = calculate_weather_condition_score(destination, travel_request)

    overall = (
        WEIGHTS["preference_match"] * s_pref
        + WEIGHTS["safety"] * s_safety
        + WEIGHTS["crowd_suitability"] * s_crowd
        + WEIGHTS["accessibility_distance"] * s_access
        + WEIGHTS["cost_suitability"] * s_cost
        + WEIGHTS["weather_condition"] * s_weather
    )
    overall = max(0.0, min(100.0, overall))

    components = ScoringComponents(
        preference_match=s_pref,
        safety=s_safety,
        crowd_suitability=s_crowd,
        accessibility_distance=s_access,
        cost_suitability=s_cost,
        weather_condition=s_weather,
    )

    weights = ScoringWeights(
        preference_match=WEIGHTS["preference_match"],
        safety=WEIGHTS["safety"],
        crowd_suitability=WEIGHTS["crowd_suitability"],
        accessibility_distance=WEIGHTS["accessibility_distance"],
        cost_suitability=WEIGHTS["cost_suitability"],
        weather_condition=WEIGHTS["weather_condition"],
    )

    explanations = {
        "preference_match": exp_pref,
        "safety": exp_safety,
        "crowd_suitability": exp_crowd,
        "accessibility_distance": exp_access,
        "cost_suitability": exp_cost,
        "weather_condition": exp_weather,
    }

    return DestinationScoreResponse(
        destination_id=destination.id,
        destination_name=destination.name,
        destination_slug=destination.slug,
        overall_score=round(overall, 1),
        components=components,
        weights=weights,
        explanations=explanations,
    )
