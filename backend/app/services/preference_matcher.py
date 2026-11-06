"""
YATRA360 — Content-Based Preference Matching Service
Compares user travel interests and preferred activities against destination
categories, descriptions, and tags using transparent, explainable calculations.
"""

from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# Category Mappings & Thematic Interest Definitions
# ============================================================================

# Canonical categories as recorded in the destinations database table:
# 'Heritage' (31), 'Spiritual' (28), 'Nature' (20), 'Wildlife' (7),
# 'Adventure' (5), 'Cultural' (5), 'Beach' (5), 'Hill Station' (2)
CANONICAL_DB_CATEGORIES: Dict[str, str] = {
    "heritage": "Heritage",
    "cultural": "Cultural",
    "nature": "Nature",
    "adventure": "Adventure",
    "spiritual": "Spiritual",
    "wildlife": "Wildlife",
    "beach": "Beach",
    "hill station": "Hill Station",
}

# Explicit synonyms and morphological variations mapping to canonical DB categories
CATEGORY_SYNONYMS: Dict[str, str] = {
    # Culture <-> Cultural (distinct strings, normalized to canonical 'Cultural')
    "culture": "Cultural",
    "cultural": "Cultural",
    "arts": "Cultural",
    "art": "Cultural",
    "folk": "Cultural",
    "tradition": "Cultural",
    "traditions": "Cultural",

    # History <-> Heritage (distinct strings, normalized to canonical 'Heritage')
    "history": "Heritage",
    "historic": "Heritage",
    "historical": "Heritage",
    "heritage": "Heritage",
    "monument": "Heritage",
    "monuments": "Heritage",
    "architecture": "Heritage",
    "palace": "Heritage",
    "fort": "Heritage",

    # Nature
    "nature": "Nature",
    "natural": "Nature",
    "scenic": "Nature",
    "landscape": "Nature",
    "landscapes": "Nature",
    "mountains": "Nature",
    "forest": "Nature",

    # Adventure
    "adventure": "Adventure",
    "trekking": "Adventure",
    "hiking": "Adventure",
    "rafting": "Adventure",
    "outdoor": "Adventure",

    # Spiritual
    "spiritual": "Spiritual",
    "pilgrimage": "Spiritual",
    "temple": "Spiritual",
    "temples": "Spiritual",
    "religious": "Spiritual",
    "ghats": "Spiritual",

    # Wildlife
    "wildlife": "Wildlife",
    "safari": "Wildlife",
    "fauna": "Wildlife",
    "national park": "Wildlife",
    "birds": "Wildlife",

    # Beach
    "beach": "Beach",
    "beaches": "Beach",
    "coastal": "Beach",
    "coast": "Beach",
    "sea": "Beach",

    # Hill Station
    "hill station": "Hill Station",
    "hill stations": "Hill Station",
    "hillstation": "Hill Station",
    "hills": "Hill Station",
}

# Supported user interests that DO NOT exist as dedicated database categories.
# Explicitly explained and scored through transparent thematic destination correlations.
THEMATIC_INTEREST_CORRELATIONS: Dict[str, Dict[str, Any]] = {
    "photography": {
        "correlated_categories": {"Nature", "Heritage", "Hill Station"},
        "affinity_score": 75.0,
        "note": "Database does not define a dedicated 'Photography' category; photographic appeal supported via scenic/architectural destinations (Nature, Heritage, Hill Station).",
    },
    "wellness": {
        "correlated_categories": {"Spiritual", "Hill Station", "Nature"},
        "affinity_score": 75.0,
        "note": "Database does not define a dedicated 'Wellness' category; wellness retreat atmosphere supported via peaceful/spiritual destinations (Spiritual, Hill Station, Nature).",
    },
}


def resolve_canonical_category(category_name: Optional[str]) -> Optional[str]:
    """
    Resolve any category string, synonym, or alias to the canonical database category.
    Returns None if not recognized as a database category.
    """
    if not category_name or not isinstance(category_name, str):
        return None
    clean = category_name.strip().lower()
    return CATEGORY_SYNONYMS.get(clean, CANONICAL_DB_CATEGORIES.get(clean))


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

    raw_dest_category = getattr(destination, "category", "") or ""
    dest_category_clean = raw_dest_category.strip().lower()
    dest_canonical = resolve_canonical_category(raw_dest_category) or raw_dest_category
    dest_description = (getattr(destination, "description", "") or "").strip().lower()
    is_hidden_gem = bool(getattr(destination, "is_hidden_gem", False))

    if user_tokens:
        matched_direct = None
        matched_thematic = None

        # 1. Check for direct category or synonym matches (e.g. Culture -> Cultural, History -> Heritage)
        for token in sorted(user_tokens):
            resolved = resolve_canonical_category(token)
            if resolved and resolved == dest_canonical:
                matched_direct = (token, resolved)
                break
            # Substring fallback within categories
            if dest_category_clean and (token in dest_category_clean or dest_category_clean in token):
                matched_direct = (token, raw_dest_category)
                break

        if matched_direct:
            user_tok, matched_cat = matched_direct
            base_score = 90.0
            if user_tok.title() == matched_cat:
                explanation = f"Direct category match for interest '{user_tok.title()}' with '{matched_cat}'."
            else:
                explanation = f"Direct category match for interest '{user_tok.title()}' mapped to '{matched_cat}'."

            if prefer_hidden_gems is not None and prefer_hidden_gems == is_hidden_gem:
                base_score += 10.0
                explanation += " Hidden-gem preference fully aligned (+10 bonus)."
        else:
            # 2. Check for supported thematic interest correlations (e.g. Photography, Wellness)
            for token in sorted(user_tokens):
                if token in THEMATIC_INTEREST_CORRELATIONS:
                    corr = THEMATIC_INTEREST_CORRELATIONS[token]
                    if dest_canonical in corr["correlated_categories"]:
                        matched_thematic = (token, corr)
                        break

            if matched_thematic:
                tok, corr = matched_thematic
                base_score = corr["affinity_score"]
                explanation = (
                    f"{tok.title()} affinity aligned with {dest_canonical} environment "
                    f"({corr['note']})"
                )
                if prefer_hidden_gems is not None and prefer_hidden_gems == is_hidden_gem:
                    base_score += 10.0
                    explanation += " Hidden-gem preference bonus applied (+10)."
            else:
                # 3. Check destination description for relevant keywords
                partial_match = any(token in dest_description for token in user_tokens)
                if partial_match:
                    base_score = 45.0
                    explanation = (
                        f"Category '{raw_dest_category}' did not match primary interests, "
                        f"but relevant keywords found in description."
                    )
                else:
                    base_score = 20.0
                    specified_str = ", ".join(t.title() for t in sorted(user_tokens))
                    # If user specified photography or wellness, explain truthful DB limitation
                    if any(t in THEMATIC_INTEREST_CORRELATIONS for t in user_tokens):
                        special_tokens = [t.title() for t in user_tokens if t in THEMATIC_INTEREST_CORRELATIONS]
                        explanation = (
                            f"Destination category '{raw_dest_category}' does not directly align with "
                            f"{', '.join(special_tokens)} (database has no dedicated category for these interests)."
                        )
                    else:
                        explanation = (
                            f"Destination category '{raw_dest_category}' does not match "
                            f"specified interests ({specified_str})."
                        )

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
