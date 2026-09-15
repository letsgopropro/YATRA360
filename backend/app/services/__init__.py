"""
Services package.
Contains modular business logic:
- Scoring engine
- Recommendation engine (future phase)
- Crowd analysis & prediction (future phase)
"""

from app.services.scoring_engine import (
    calculate_preference_match,
    calculate_safety_score,
    calculate_crowd_suitability,
    calculate_accessibility_distance_score,
    calculate_cost_suitability,
    calculate_weather_condition_score,
    calculate_destination_score,
    haversine_distance_km,
)
from app.services.recommendation_engine import (
    apply_category_diversity,
    find_alternative_destinations,
    generate_recommendation_reasons,
    get_recommendations,
)

__all__ = [
    "calculate_preference_match",
    "calculate_safety_score",
    "calculate_crowd_suitability",
    "calculate_accessibility_distance_score",
    "calculate_cost_suitability",
    "calculate_weather_condition_score",
    "calculate_destination_score",
    "haversine_distance_km",
    "get_recommendations",
    "find_alternative_destinations",
    "generate_recommendation_reasons",
    "apply_category_diversity",
]
