"""
YATRA360 — Personalized Recommendation Engine
Step 3: Content-based recommendation and ranking service.

Core principles:
1. Strictly calls and reuses calculate_destination_score() from scoring_engine.py.
2. Applies conservative category diversity (10-point threshold) and time constraint handling.
3. Generates 3-5 factual, transparent explainability reasons per recommendation.
4. Provides reusable foundation scaffolding for alternative-destination discovery (Step 4).
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.schemas.recommendation import (
    AlternativeDestinationsResponse,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.scoring import DestinationScoreResponse, TravelRequest
from app.services.scoring_engine import calculate_destination_score


# ============================================================================
# Explainability Reason Generator
# ============================================================================

def generate_recommendation_reasons(
    destination: Destination,
    score_response: DestinationScoreResponse,
    travel_request: TravelRequest,
    time_penalty: float = 0.0,
) -> List[str]:
    """
    Generate 3 to 5 concise, truthful, factual reasons explaining why the destination
    was recommended, directly supported by scoring components and user criteria.
    """
    reasons: List[str] = []
    components = score_response.components

    # 1. Interest & Category Alignment
    if components.preference_match >= 85.0:
        matching_interest = None
        if travel_request.interests:
            dest_cat = (destination.category or "").lower()
            for interest in travel_request.interests:
                if interest.lower() in dest_cat or dest_cat in interest.lower():
                    matching_interest = interest
                    break
        if matching_interest:
            reasons.append(f"Strong match for your interest '{matching_interest.title()}' in the {destination.category} category.")
        else:
            reasons.append(f"High affinity with your travel interests in {destination.category}.")
    elif components.preference_match >= 45.0:
        reasons.append(f"Relevant themes in the destination overview match your travel interests.")
    else:
        reasons.append(f"Well-rounded tourist destination in {destination.state} offering rich sightseeing.")

    # 2. Hidden-Gem Status & Preference
    if destination.is_hidden_gem:
        if travel_request.prefer_hidden_gems is True:
            reasons.append("Authentic offbeat hidden gem aligned with your preference for lesser-known spots.")
        else:
            reasons.append("Lesser-known hidden gem offering unique cultural and natural appeal.")
    else:
        reasons.append(f"Renowned iconic landmark recognized across {destination.state}.")

    # 3. Crowd Atmosphere & Preference
    dest_crowd = (destination.base_crowd_level or "moderate").lower()
    if travel_request.preferred_crowd_level:
        user_pref = travel_request.preferred_crowd_level.lower()
        if dest_crowd == user_pref:
            reasons.append(f"Matches your preferred {user_pref} crowd level.")
        elif dest_crowd == "low":
            reasons.append("Low crowd pressure providing a calm, uncrowded atmosphere.")
        else:
            reasons.append(f"Features a lively, energetic atmosphere ({dest_crowd} crowd baseline).")
    else:
        if dest_crowd == "low":
            reasons.append("Low visitor footfall providing a serene, peaceful experience.")
        elif dest_crowd == "moderate":
            reasons.append("Balanced visitor presence with comfortable crowd conditions.")
        else:
            reasons.append(f"Popular high-footfall attraction in {destination.city}.")

    # 4. Budget & Cost Suitability
    fee = destination.entry_fee or 0.0
    if fee == 0.0:
        reasons.append("Free public entry with zero admission cost.")
    elif travel_request.budget and travel_request.budget > 0:
        if fee <= travel_request.budget:
            reasons.append(f"Entry fee of ₹{fee:.0f} is well within your budget of ₹{travel_request.budget:.0f}.")
        else:
            reasons.append(f"Entry fee of ₹{fee:.0f} requires a minor budget adjustment.")
    else:
        reasons.append(f"Standard domestic admission fee of ₹{fee:.0f}.")

    # 5. Visit Duration / Schedule Suitability
    duration = destination.estimated_visit_duration
    avail = travel_request.available_time_minutes
    if duration and avail:
        if duration <= avail:
            reasons.append(f"Estimated visit time ({duration} mins) comfortably fits within your available schedule ({avail} mins).")
        elif time_penalty > 0:
            reasons.append(f"Estimated visit time ({duration} mins) exceeds your available window ({avail} mins).")

    # Limit to top 3-5 high-relevance reasons
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
    - If a category already has `max_per_category` picks in the selection, look ahead for a
      different category candidate.
    - Promote the diverse candidate ONLY if its score is within `diversity_threshold` points
      of the competing same-category candidate.
    - If no diverse candidate is within the threshold, retain the higher-scoring item.
    - Never sacrifices high-relevance candidates for artificial variety.
    """
    if len(scored_items) <= 2 or limit <= 1:
        return scored_items[:limit]

    selected: List[Dict[str, Any]] = []
    pool = list(scored_items)
    category_counts: Dict[str, int] = {}

    while pool and len(selected) < limit:
        candidate = pool[0]
        cat = candidate["destination"].category

        if category_counts.get(cat, 0) < max_per_category:
            # Category has room; accept candidate
            selected.append(candidate)
            category_counts[cat] = category_counts.get(cat, 0) + 1
            pool.pop(0)
        else:
            # Category has reached saturation; look ahead for a diverse candidate
            promoted_idx = None
            for idx in range(1, len(pool)):
                competing = pool[idx]
                comp_cat = competing["destination"].category
                if comp_cat != cat and category_counts.get(comp_cat, 0) < max_per_category:
                    score_gap = candidate["adjusted_score"] - competing["adjusted_score"]
                    if score_gap <= diversity_threshold:
                        promoted_idx = idx
                        break

            if promoted_idx is not None:
                # Promote diverse alternative
                promoted = pool.pop(promoted_idx)
                selected.append(promoted)
                p_cat = promoted["destination"].category
                category_counts[p_cat] = category_counts.get(p_cat, 0) + 1
            else:
                # No suitable diverse alternative within margin; accept original candidate
                selected.append(candidate)
                category_counts[cat] = category_counts.get(cat, 0) + 1
                pool.pop(0)

    return selected


# ============================================================================
# Core Recommendation Service
# ============================================================================

def get_recommendations(
    request: RecommendationRequest,
    db: Session,
) -> RecommendationResponse:
    """
    Generate personalized destination recommendations:
    1. Select candidate destinations from DB using optional filters.
    2. Score each candidate using calculate_destination_score().
    3. Apply available-time schedule adjustment.
    4. Generate 3-5 factual explainability reasons.
    5. Apply conservative category diversity.
    6. Return up to requested limit.
    """
    # 1. Candidate Selection Query
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

    # 2. Score Candidates using the existing scoring engine
    scored_items: List[Dict[str, Any]] = []

    for dest in candidates:
        score_res = calculate_destination_score(destination=dest, travel_request=request)
        
        # 3. Available-Time Suitability Adjustment (separate from core scoring engine)
        time_penalty = 0.0
        avail_time = request.available_time_minutes
        visit_duration = dest.estimated_visit_duration

        if avail_time and avail_time > 0 and visit_duration:
            if visit_duration > 2.0 * avail_time:
                time_penalty = 20.0
            elif visit_duration > avail_time:
                overtime_ratio = (visit_duration - avail_time) / avail_time
                time_penalty = min(10.0, overtime_ratio * 10.0)

        adjusted_score = max(0.0, min(100.0, score_res.overall_score - time_penalty))
        reasons = generate_recommendation_reasons(dest, score_res, request, time_penalty)

        scored_items.append({
            "destination": dest,
            "score_response": score_res,
            "adjusted_score": round(adjusted_score, 1),
            "reasons": reasons,
        })

    # Sort candidates by adjusted score descending
    scored_items.sort(key=lambda x: x["adjusted_score"], reverse=True)

    # 4. Conservative Category Diversity Balancing
    if request.apply_diversity and not request.category:
        final_items = apply_category_diversity(
            scored_items=scored_items,
            limit=request.limit,
            diversity_threshold=request.diversity_threshold,
        )
    else:
        final_items = scored_items[:request.limit]

    # 5. Format Recommendation Items
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
            reasons=item["reasons"],
        )
        for item in final_items
    ]

    return RecommendationResponse(
        total_candidates_evaluated=total_evaluated,
        recommendations_count=len(recommendations),
        recommendations=recommendations,
        request_summary=request,
        applied_filters=applied_filters,
    )


# ============================================================================
# Alternative Destination Scaffolding (Step 4 Preparation)
# ============================================================================

def find_alternative_destinations(
    destination_id: int,
    request: Optional[TravelRequest] = None,
    limit: int = 5,
    db: Session = None,
) -> AlternativeDestinationsResponse:
    """
    Scaffolding service finding lower-crowd or hidden-gem alternatives for a destination.
    Provides reusable foundation code for the future overcrowding redirection workflow.
    """
    source_dest = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not source_dest:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source destination with ID {destination_id} not found",
        )

    # Search for alternatives in the same category or state with lower crowd or hidden-gem status
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

    req = request or TravelRequest()
    alternatives_scored: List[Dict[str, Any]] = []

    for dest in candidates:
        score_res = calculate_destination_score(dest, req)
        
        # Boost alternatives with lower crowd than source or hidden-gem status
        source_crowd = (source_dest.base_crowd_level or "moderate").lower()
        cand_crowd = (dest.base_crowd_level or "moderate").lower()

        is_better_crowd = (source_crowd == "high" and cand_crowd in {"low", "moderate"}) or (source_crowd == "moderate" and cand_crowd == "low")
        crowd_boost = 5.0 if is_better_crowd else 0.0
        gem_boost = 5.0 if dest.is_hidden_gem else 0.0

        alt_score = min(100.0, score_res.overall_score + crowd_boost + gem_boost)

        reasons = [
            f"Alternative in {dest.category} category located in {dest.state}.",
            f"Crowd profile: {dest.base_crowd_level} (compared to source {source_dest.base_crowd_level}).",
        ]
        if dest.is_hidden_gem:
            reasons.append("Offbeat hidden gem with serene surroundings.")
        reasons.append(f"Entry fee: ₹{dest.entry_fee:.0f}.")

        alternatives_scored.append({
            "destination": dest,
            "score_response": score_res,
            "overall_score": round(alt_score, 1),
            "reasons": reasons,
        })

    alternatives_scored.sort(key=lambda x: x["overall_score"], reverse=True)
    top_alts = alternatives_scored[:limit]

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
            overall_score=item["overall_score"],
            components=item["score_response"].components,
            reasons=item["reasons"],
        )
        for item in top_alts
    ]

    return AlternativeDestinationsResponse(
        source_destination_id=source_dest.id,
        source_destination_name=source_dest.name,
        source_crowd_level=source_dest.base_crowd_level,
        alternatives_count=len(alt_items),
        alternatives=alt_items,
    )
