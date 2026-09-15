"""
YATRA360 — Scoring Engine API Routes
Exposes endpoints for calculating dynamic destination suitability scores.
"""

from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.destination import Destination
from app.schemas.scoring import (
    BatchDestinationScoreResponse,
    DestinationScoreResponse,
    TravelRequest,
)
from app.services.scoring_engine import calculate_destination_score

router = APIRouter(prefix="/scoring", tags=["Scoring Engine"])


@router.post(
    "/destination/{destination_id}",
    response_model=DestinationScoreResponse,
    summary="Calculate suitability score for a single destination",
)
def score_single_destination(
    destination_id: int,
    travel_request: Optional[TravelRequest] = Body(default=None),
    db: Session = Depends(get_db),
) -> Any:
    """
    Calculate the transparent weighted suitability score for a specific destination.
    Uses user preferences (interests, budget, crowd preference, accessibility, starting location)
    if provided, or applies neutral prototype baselines for omitted fields.
    """
    destination = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with ID {destination_id} not found",
        )

    req = travel_request or TravelRequest()
    result = calculate_destination_score(destination=destination, travel_request=req)
    return result


@router.post(
    "/destinations",
    response_model=BatchDestinationScoreResponse,
    summary="Calculate scores for multiple destinations and return ranked results",
)
def score_destinations_batch(
    travel_request: Optional[TravelRequest] = Body(default=None),
    category: Optional[str] = Query(None, description="Filter candidate destinations by category"),
    state: Optional[str] = Query(None, description="Filter candidate destinations by state"),
    is_hidden_gem: Optional[bool] = Query(None, description="Filter candidate destinations by hidden-gem status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of scored results to return"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Score destinations against the provided travel request and return them ranked by overall score descending.
    Lays the foundation for future AI recommendation engine pipelines.
    """
    req = travel_request or TravelRequest()

    stmt = select(Destination)
    if req.destination:
        term = f"%{req.destination.strip()}%"
        stmt = stmt.where(
            (Destination.city.ilike(term))
            | (Destination.state.ilike(term))
            | (Destination.name.ilike(term))
        )
    if category:
        stmt = stmt.where(Destination.category.ilike(f"%{category.strip()}%"))
    if state:
        stmt = stmt.where(Destination.state.ilike(f"%{state.strip()}%"))
    if is_hidden_gem is not None:
        stmt = stmt.where(Destination.is_hidden_gem == is_hidden_gem)

    destinations = db.scalars(stmt).all()

    scored_results = [
        calculate_destination_score(destination=dest, travel_request=req)
        for dest in destinations
    ]

    # Rank by overall score descending
    scored_results.sort(key=lambda r: r.overall_score, reverse=True)
    top_results = scored_results[:limit]

    return BatchDestinationScoreResponse(
        total=len(top_results),
        results=top_results,
    )
