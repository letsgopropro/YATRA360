"""
YATRA360 — Content-Based Preference Matching Service
Compares user travel interests and preferred activities against destination
categories, descriptions, and tags using transparent, explainable calculations.
"""

from typing import Any, List, Optional, Set, Tuple


def _normalize_tokens(tokens: Optional[List[str]]) -> Set[str]:
    """Normalize a list of strings into clean, lowercase alphanumeric tokens."""
    if not tokens:
        return set()
    normalized = set()
    for token in tokens:
        if token and isinstance(token, str):
            clean = token.strip().lower()
            if clean:
                normalized.add(clean)
    return normalized


def calculate_preference_match(
    destination: Any,
    travel_request: Optional[Any] = None,
) -> Tuple[Optional[float], str]:
    """
    Calculate content-based preference similarity between user preferences and destination.

    Returns:
        Tuple[Optional[float], str]:
            - score: Normalized 0-100 float, or None if no user preferences provided.
            - explanation: Human-readable explainability text.
    """
    if not travel_request:
        return (
            None,
            "No user preference information provided; preference component excluded and weight renormalized.",
        )

    # Collect user preferences
    interests = getattr(travel_request, "interests", None) or []
    preferred_activities = getattr(travel_request, "preferred_activities", None) or []
    prefer_hidden_gems = getattr(travel_request, "prefer_hidden_gems", None)

    user_tokens = _normalize_tokens(interests) | _normalize_tokens(preferred_activities)

    # If no interest tokens and no hidden gem preference, data is genuinely missing
    if not user_tokens and prefer_hidden_gems is None:
        return (
            None,
            "No user interests or activity preferences provided; preference component excluded and weight renormalized.",
        )

    dest_category = (getattr(destination, "category", "") or "").strip().lower()
    dest_description = (getattr(destination, "description", "") or "").strip().lower()
    is_hidden_gem = bool(getattr(destination, "is_hidden_gem", False))

    if user_tokens:
        matched_interest = None
        for token in sorted(user_tokens):
            if token in dest_category or dest_category in token:
                matched_interest = token
                break

        if matched_interest:
            base_score = 90.0
            explanation = f"Direct category match for interest '{matched_interest.title()}' with '{getattr(destination, 'category', '')}'."
            if prefer_hidden_gems is not None and prefer_hidden_gems == is_hidden_gem:
                base_score += 10.0
                explanation += " Hidden-gem preference fully aligned (+10 bonus)."
        else:
            # Check description for keyword mention as partial match
            partial_match = any(token in dest_description for token in user_tokens)
            if partial_match:
                base_score = 45.0
                explanation = f"Category '{getattr(destination, 'category', '')}' did not match primary interests, but relevant keywords found in description."
            else:
                base_score = 20.0
                specified_str = ", ".join(t.title() for t in user_tokens)
                explanation = f"Destination category '{getattr(destination, 'category', '')}' does not match specified interests ({specified_str})."

            if prefer_hidden_gems is not None and prefer_hidden_gems == is_hidden_gem:
                base_score += 10.0
                explanation += " Hidden-gem preference bonus applied (+10)."
    else:
        # User specified only hidden-gem preference
        base_score = 50.0
        if prefer_hidden_gems == is_hidden_gem:
            base_score = 60.0
            explanation = "Evaluated preference aligned with offbeat hidden-gem preference (+10 bonus)."
        else:
            base_score = 40.0
            explanation = "Evaluated preference does not match hidden-gem preference."

    clamped_score = max(0.0, min(100.0, base_score))
    return round(clamped_score, 1), explanation
