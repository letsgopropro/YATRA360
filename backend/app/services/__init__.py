"""
Services package.
Contains modular business logic:
- Preference matcher
- Destination similarity engine
- Scoring engine
- Recommendation engine
"""

from app.services.preference_matcher import (
    calculate_preference_match,
)
from app.services.destination_similarity import (
    DEFAULT_SIMILARITY_WEIGHTS,
    calculate_destination_similarity,
    validate_similarity_weights,
)
from app.services.scoring_engine import (
    DEFAULT_WEIGHTS,
    OVERCROWDING_THRESHOLD,
    calculate_accessibility_distance_score,
    calculate_cost_suitability,
    calculate_crowd_suitability,
    calculate_destination_score,
    calculate_safety_score,
    calculate_weather_condition_score,
    evaluate_preference_match,
    haversine_distance_km,
    is_overcrowded,
    validate_weights,
)
from app.services.recommendation_engine import (
    apply_category_diversity,
    check_and_redirect_if_overcrowded,
    find_alternative_destinations,
    generate_recommendation_reasons,
    get_alternatives_for_request,
    get_recommendations,
    recommend_alternatives,
    recommend_destinations,
)

__all__ = [
    # Preference Matcher
    "calculate_preference_match",
    # Destination Similarity
    "DEFAULT_SIMILARITY_WEIGHTS",
    "calculate_destination_similarity",
    "validate_similarity_weights",
    # Scoring Engine
    "DEFAULT_WEIGHTS",
    "OVERCROWDING_THRESHOLD",
    "validate_weights",
    "is_overcrowded",
    "calculate_safety_score",
    "calculate_crowd_suitability",
    "calculate_accessibility_distance_score",
    "calculate_cost_suitability",
    "calculate_weather_condition_score",
    "calculate_destination_score",
    "evaluate_preference_match",
    "haversine_distance_km",
    # Recommendation Engine
    "recommend_destinations",
    "recommend_alternatives",
    "check_and_redirect_if_overcrowded",
    "get_recommendations",
    "find_alternative_destinations",
    "get_alternatives_for_request",
    "generate_recommendation_reasons",
    "apply_category_diversity",
]
