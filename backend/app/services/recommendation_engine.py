"""
YATRA360 — Personalized Recommendation Engine
Generates personalized ranked destination recommendations and intelligent alternative
recommendations for overcrowded sites using multi-criteria scoring and content similarity.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.schemas.recommendation import (
    AlternativeDestinationsResponse,
    AlternativeRecommendationRequest,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.scoring import DestinationScoreResponse, TravelRequest
from app.services.destination_similarity import (
    DEFAULT_SIMILARITY_WEIGHTS,
    calculate_destination_similarity,
)
from app.services.scoring_engine import (
    calculate_destination_score,
    is_overcrowded,
)


# ============================================================================
# Explainability Reason Generator
# ============================================================================

def generate_recommendation_reasons(
    destination: Any,
    score_response: DestinationScoreResponse,
    travel_request: Optional[TravelRequest] = None,
    time_penalty: float = 0.0,
    is_alternative: bool = False,
    source_destination: Optional[Any] = None,
) -> List[str]:
    """
    Generate 3 to 5 concise, truthful, factual reasons explaining why the destination
    was recommended, directly supported by scoring components and user criteria.
    """
    reasons: List[str] = []
    comp = score_response.components
    req = travel_request or TravelRequest()

    # 1. Alternative Context (if applicable)
    if is_alternative and source_destination:
        source_crowd = getattr(source_destination, "base_crowd_level", "moderate")
        cand_crowd = getattr(destination, "base_crowd_level", "moderate")
        reasons.append(
            f"Recommended alternative offering lower crowd footfall ({cand_crowd}) compared to {source_destination.name} ({source_crowd})."
        )

    # 2. Interest & Category Alignment
    if comp.preference_match is not None:
        if comp.preference_match >= 85.0:
            reasons.append(
                f"Strong match for your travel interests in the {getattr(destination, 'category', 'General')} category."
            )
        elif comp.preference_match >= 45.0:
            reasons.append(
                f"Relevant themes in destination overview align with your travel interests."
            )
        else:
            reasons.append(
                f"Well-rounded tourist destination in {getattr(destination, 'state', 'India')} offering sightseeing."
            )
    else:
        reasons.append(
            f"Popular destination in {getattr(destination, 'city', 'India')}, {getattr(destination, 'state', '')}."
        )

    # 3. Hidden-Gem Status
    is_gem = bool(getattr(destination, "is_hidden_gem", False))
    if is_gem:
        if req.prefer_hidden_gems is True:
            reasons.append("Authentic offbeat hidden gem aligned with your preference for lesser-known spots.")
        else:
            reasons.append("Lesser-known hidden gem offering peaceful surroundings.")
    else:
        reasons.append(f"Iconic landmark recognized across {getattr(destination, 'state', 'the region')}.")

    # 4. Crowd Atmosphere
    dest_crowd = (getattr(destination, "base_crowd_level", "moderate") or "moderate").lower()
    if req.preferred_crowd_level:
        user_pref = req.preferred_crowd_level.lower()
        if dest_crowd == user_pref:
            reasons.append(f"Matches your preferred {user_pref} crowd atmosphere.")
        elif dest_crowd == "low":
            reasons.append("Low crowd pressure providing a calm, uncrowded visit.")
        else:
            reasons.append(f"Features a lively atmosphere ({dest_crowd} crowd baseline).")
    else:
        if dest_crowd == "low":
            reasons.append("Low visitor footfall providing a serene, unhurried experience.")
        elif dest_crowd == "moderate":
            reasons.append("Balanced visitor presence with comfortable crowd conditions.")
        else:
            reasons.append(f"High-footfall attraction in {getattr(destination, 'city', 'the city')}.")

    # 5. Budget & Cost Suitability
    fee = float(getattr(destination, "entry_fee", 0.0) or 0.0)
    if fee == 0.0:
        reasons.append("Free public entry with zero admission cost.")
    elif req.budget and req.budget > 0:
        if fee <= req.budget:
            reasons.append(f"Entry fee of ₹{fee:.0f} is well within your budget of ₹{req.budget:.0f}.")
        else:
            reasons.append(f"Entry fee of ₹{fee:.0f} requires a minor budget adjustment.")
    else:
        reasons.append(f"Standard domestic admission fee of ₹{fee:.0f}.")

    # 6. Visit Duration Compatibility
    duration = getattr(destination, "estimated_visit_duration", None)
    avail = req.available_time_minutes
    if duration and avail:
        if duration <= avail:
            reasons.append(f"Estimated visit time ({duration} mins) comfortably fits within your available schedule ({avail} mins).")
        elif time_penalty > 0:
            reasons.append(f"Estimated visit time ({duration} mins) exceeds your schedule ({avail} mins).")

    # Return top 3-5 high-relevance reasons
    return reasons[:5] if len(reasons) >= 3 else reasons


# ============================================================================
# Conservative Category Diversity Filter
# ============================================================================

def apply_category_diversity(
    scored_items: List[Dict[str, Any]],
    limit: int,
    diversity_threshold: float = 10.0,
    max_per_category: int = 2,
) -> List[Dict[str, Any]]:
    """
    Conservative non-destructive category diversity algorithm:
    - If a category already has `max_per_category` picks, looks ahead for diverse candidates.
    - Promotes diverse candidate ONLY if within `diversity_threshold` points.
    - Never sacrifices high-relevance candidates for artificial variety.
    """
    if len(scored_items) <= 2 or limit <= 1:
        return scored_items[:limit]

    selected: List[Dict[str, Any]] = []
    pool = list(scored_items)
    category_counts: Dict[str, int] = {}

    while pool and len(selected) < limit:
        candidate = pool[0]
        cat = getattr(candidate["destination"], "category", "General")

        if category_counts.get(cat, 0) < max_per_category:
            selected.append(candidate)
            category_counts[cat] = category_counts.get(cat, 0) + 1
            pool.pop(0)
        else:
            promoted_idx = None
            for idx in range(1, len(pool)):
                competing = pool[idx]
                comp_cat = getattr(competing["destination"], "category", "General")
                if comp_cat != cat and category_counts.get(comp_cat, 0) < max_per_category:
                    score_gap = candidate["adjusted_score"] - competing["adjusted_score"]
                    if score_gap <= diversity_threshold:
                        promoted_idx = idx
                        break

            if promoted_idx is not None:
                promoted = pool.pop(promoted_idx)
                selected.append(promoted)
                p_cat = getattr(promoted["destination"], "category", "General")
                category_counts[p_cat] = category_counts.get(p_cat, 0) + 1
            else:
                selected.append(candidate)
                category_counts[cat] = category_counts.get(cat, 0) + 1
                pool.pop(0)

    return selected


# ============================================================================
# Core Pure Ranking Functions (Decoupled from Database)
# ============================================================================

def recommend_destinations(
    user_preferences: TravelRequest,
    destinations: List[Any],
    top_k: int = 5,
    weights: Optional[Dict[str, float]] = None,
    apply_diversity: bool = True,
    diversity_threshold: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Pure in-memory ranking function evaluating a list of Destination candidates.
    1. Evaluates all eligible destinations using calculate_destination_score().
    2. Applies available-time duration penalty.
    3. Generates transparent explainability reasons.
    4. Deterministically sorts by score descending.
    5. Optionally applies category diversity balancing.
    6. Returns top K items.
    """
    if not destinations:
        return []

    scored_items: List[Dict[str, Any]] = []

    for dest in destinations:
        score_res = calculate_destination_score(
            destination=dest,
            travel_request=user_preferences,
            weights=weights,
        )

        time_penalty = 0.0
        avail_time = user_preferences.available_time_minutes if user_preferences else None
        visit_duration = getattr(dest, "estimated_visit_duration", None)

        if avail_time and avail_time > 0 and visit_duration:
            if visit_duration > 2.0 * avail_time:
                time_penalty = 20.0
            elif visit_duration > avail_time:
                overtime_ratio = (visit_duration - avail_time) / avail_time
                time_penalty = min(10.0, overtime_ratio * 10.0)

        adjusted_score = max(0.0, min(100.0, score_res.overall_score - time_penalty))
        reasons = generate_recommendation_reasons(
            destination=dest,
            score_response=score_res,
            travel_request=user_preferences,
            time_penalty=time_penalty,
        )

        scored_items.append({
            "destination": dest,
            "score_response": score_res,
            "adjusted_score": round(adjusted_score, 1),
            "reasons": reasons,
        })

    # Deterministic sort by adjusted score descending, then by name
    scored_items.sort(
        key=lambda x: (x["adjusted_score"], getattr(x["destination"], "name", "")),
        reverse=True,
    )

    if apply_diversity and len(scored_items) > 1:
        final_items = apply_category_diversity(
            scored_items=scored_items,
            limit=top_k,
            diversity_threshold=diversity_threshold,
        )
    else:
        final_items = scored_items[:top_k]

    return final_items


def recommend_alternatives(
    preferred_destination: Any,
    user_preferences: Optional[TravelRequest] = None,
    destinations: Optional[List[Any]] = None,
    top_k: int = 5,
    weights: Optional[Dict[str, float]] = None,
    similarity_weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Recommend alternative destinations for a preferred destination.
    - NEVER returns the preferred destination as its own alternative.
    - Blends destination similarity (40%) and general suitability score (60%).
    - Boosts candidates with lower crowd level than preferred destination.
    - Deterministically ranks and returns top K alternatives.
    """
    if not destinations:
        return []

    preferred_id = getattr(preferred_destination, "id", None)
    preferred_slug = getattr(preferred_destination, "slug", "")
    preferred_crowd = (getattr(preferred_destination, "base_crowd_level", "moderate") or "moderate").lower()

    # Rule: Never recommend the preferred destination as its own alternative
    candidates = [
        d for d in destinations
        if (preferred_id is None or getattr(d, "id", None) != preferred_id)
        and (not preferred_slug or getattr(d, "slug", None) != preferred_slug)
    ]

    req = user_preferences or TravelRequest()
    alternatives_scored: List[Dict[str, Any]] = []

    for cand in candidates:
        # 1. Similarity to preferred destination
        sim_score, sim_comp, sim_expl = calculate_destination_similarity(
            source=preferred_destination,
            candidate=cand,
            weights=similarity_weights,
        )

        # 2. Suitability score for user preferences
        score_res = calculate_destination_score(
            destination=cand,
            travel_request=req,
            weights=weights,
        )

        # 3. Crowd relief bonus
        cand_crowd = (getattr(cand, "base_crowd_level", "moderate") or "moderate").lower()
        crowd_ranks = {"low": 1, "moderate": 2, "high": 3, "overcrowded": 4}
        is_lower_crowd = crowd_ranks.get(cand_crowd, 2) < crowd_ranks.get(preferred_crowd, 2)
        crowd_bonus = 10.0 if is_lower_crowd else 0.0

        # Blended alternative suitability (40% similarity + 60% user suitability + crowd bonus)
        composite_alt_score = 0.40 * sim_score + 0.60 * score_res.overall_score + crowd_bonus
        composite_alt_score = max(0.0, min(100.0, composite_alt_score))

        reasons = generate_recommendation_reasons(
            destination=cand,
            score_response=score_res,
            travel_request=req,
            is_alternative=True,
            source_destination=preferred_destination,
        )

        alternatives_scored.append({
            "destination": cand,
            "score_response": score_res,
            "similarity_score": sim_score,
            "adjusted_score": round(composite_alt_score, 1),
            "reasons": reasons,
        })

    alternatives_scored.sort(
        key=lambda x: (x["adjusted_score"], getattr(x["destination"], "name", "")),
        reverse=True,
    )

    return alternatives_scored[:top_k]


def check_and_redirect_if_overcrowded(
    preferred_destination: Any,
    user_preferences: Optional[TravelRequest] = None,
    destinations: Optional[List[Any]] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Overcrowding redirection logic:
    - If preferred destination exceeds overcrowding threshold, identify alternatives.
    - Else, return preferred destination normally.
    """
    overcrowded = is_overcrowded(preferred_destination)
    if overcrowded and destinations:
        alts = recommend_alternatives(
            preferred_destination=preferred_destination,
            user_preferences=user_preferences,
            destinations=destinations,
            top_k=top_k,
        )
        return {
            "is_overcrowded": True,
            "preferred_destination": preferred_destination,
            "alternatives": alts,
            "message": f"{getattr(preferred_destination, 'name', 'Destination')} is currently experiencing high crowd levels. Here are suitable lower-crowd alternatives.",
        }
    else:
        return {
            "is_overcrowded": False,
            "preferred_destination": preferred_destination,
            "alternatives": [],
            "message": f"{getattr(preferred_destination, 'name', 'Destination')} crowd conditions are within acceptable levels.",
        }


# ============================================================================
# Database Orchestration Services for FastAPI Routes
# ============================================================================

def get_recommendations(
    request: RecommendationRequest,
    db: Session,
) -> RecommendationResponse:
    """
    API orchestration service retrieving candidates from DB and generating recommendations.
    """
    stmt = select(Destination)
    applied_filters: Dict[str, Any] = {}

    if request.category:
        stmt = stmt.where(Destination.category.ilike(f"%{request.category.strip()}%"))
        applied_filters["category"] = request.category.strip()

    if request.state:
        stmt = stmt.where(Destination.state.ilike(f"%{request.state.strip()}%"))
        applied_filters["state"] = request.state.strip()

    if request.is_hidden_gem is not None:
        stmt = stmt.where(Destination.is_hidden_gem == request.is_hidden_gem)
        applied_filters["is_hidden_gem"] = request.is_hidden_gem

    if request.destination:
        term = f"%{request.destination.strip()}%"
        stmt = stmt.where(
            or_(
                Destination.city.ilike(term),
                Destination.state.ilike(term),
                Destination.name.ilike(term),
            )
        )
        applied_filters["destination_keyword"] = request.destination.strip()

    candidates = db.scalars(stmt).all()
    total_evaluated = len(candidates)

    if total_evaluated == 0:
        return RecommendationResponse(
            total_candidates_evaluated=0,
            recommendations_count=0,
            recommendations=[],
            request_summary=request,
            applied_filters=applied_filters,
        )

    ranked_items = recommend_destinations(
        user_preferences=request,
        destinations=candidates,
        top_k=request.limit,
        apply_diversity=request.apply_diversity and not request.category,
        diversity_threshold=request.diversity_threshold,
    )

    recommendations = [
        RecommendationItem(
            destination_id=item["destination"].id,
            destination_name=item["destination"].name,
            slug=item["destination"].slug,
            city=item["destination"].city,
            state=item["destination"].state,
            category=item["destination"].category,
            is_hidden_gem=item["destination"].is_hidden_gem,
            entry_fee=item["destination"].entry_fee,
            safety_rating=item["destination"].safety_rating,
            base_crowd_level=item["destination"].base_crowd_level,
            estimated_visit_duration=item["destination"].estimated_visit_duration,
            overall_score=item["adjusted_score"],
            components=item["score_response"].components,
            score_breakdown=item["score_response"].score_breakdown,
            data_quality=item["score_response"].data_quality,
            is_alternative=False,
            reasons=item["reasons"],
        )
        for item in ranked_items
    ]

    return RecommendationResponse(
        total_candidates_evaluated=total_evaluated,
        recommendations_count=len(recommendations),
        recommendations=recommendations,
        request_summary=request,
        applied_filters=applied_filters,
    )


def find_alternative_destinations(
    destination_id: int,
    request: Optional[TravelRequest] = None,
    limit: int = 5,
    db: Session = None,
) -> AlternativeDestinationsResponse:
    """
    API service retrieving alternatives for a specific destination by primary key ID.
    """
    from fastapi import HTTPException, status

    source_dest = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not source_dest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source destination with ID {destination_id} not found",
        )

    # Candidate destinations in same state or category
    stmt = (
        select(Destination)
        .where(Destination.id != destination_id)
        .where(
            or_(
                Destination.category == source_dest.category,
                Destination.state == source_dest.state,
            )
        )
    )
    candidates = db.scalars(stmt).all()
    if not candidates:
        candidates = db.scalars(select(Destination).where(Destination.id != destination_id).limit(20)).all()

    req = request or TravelRequest()
    ranked_alts = recommend_alternatives(
        preferred_destination=source_dest,
        user_preferences=req,
        destinations=candidates,
        top_k=limit,
    )

    alt_items = [
        RecommendationItem(
            destination_id=item["destination"].id,
            destination_name=item["destination"].name,
            slug=item["destination"].slug,
            city=item["destination"].city,
            state=item["destination"].state,
            category=item["destination"].category,
            is_hidden_gem=item["destination"].is_hidden_gem,
            entry_fee=item["destination"].entry_fee,
            safety_rating=item["destination"].safety_rating,
            base_crowd_level=item["destination"].base_crowd_level,
            estimated_visit_duration=item["destination"].estimated_visit_duration,
            overall_score=item["adjusted_score"],
            components=item["score_response"].components,
            score_breakdown=item["score_response"].score_breakdown,
            data_quality=item["score_response"].data_quality,
            is_alternative=True,
            reasons=item["reasons"],
        )
        for item in ranked_alts
    ]

    return AlternativeDestinationsResponse(
        source_destination_id=source_dest.id,
        source_destination_name=source_dest.name,
        source_crowd_level=source_dest.base_crowd_level,
        is_source_overcrowded=is_overcrowded(source_dest),
        alternatives_count=len(alt_items),
        alternatives=alt_items,
    )


def get_alternatives_for_request(
    request: AlternativeRecommendationRequest,
    db: Session,
) -> AlternativeDestinationsResponse:
    """
    Handles POST /api/recommendations/alternatives request.
    Finds source destination by ID or name and returns ranked alternatives.
    """
    from fastapi import HTTPException, status

    source_dest = None
    if request.preferred_destination_id:
        source_dest = db.scalar(select(Destination).where(Destination.id == request.preferred_destination_id))
    elif request.preferred_destination_name:
        term = f"%{request.preferred_destination_name.strip()}%"
        source_dest = db.scalar(
            select(Destination).where(
                or_(Destination.name.ilike(term), Destination.slug.ilike(term))
            )
        )

    if not source_dest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferred destination not found by ID or name",
        )

    return find_alternative_destinations(
        destination_id=source_dest.id,
        request=request.user_preferences,
        limit=request.limit,
        db=db,
    )
