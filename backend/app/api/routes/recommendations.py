"""
YATRA360 — Recommendation Engine API Routes
Exposes personalized destination recommendation and alternative destination endpoints.
"""

from typing import Any
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.recommendation import (
    AlternativeDestinationsResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_engine import (
    find_alternative_destinations,
    get_recommendations,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personalized destination recommendations",
)
def create_recommendations(
    request: RecommendationRequest = Body(
        ...,
        openapi_examples={
            "nature_adventure": {
                "summary": "Nature & Adventure Explorer Sample",
                "description": "User seeking offbeat nature spots with low crowd preference",
                "value": {
                    "interests": ["Nature", "Adventure"],
                    "budget": 2000.0,
                    "available_time_minutes": 480,
                    "preferred_crowd_level": "low",
                    "prefer_hidden_gems": True,
                    "limit": 5,
                    "apply_diversity": True,
                },
            },
            "cultural_heritage": {
                "summary": "Cultural Heritage Sample",
                "description": "User seeking heritage destinations with moderate crowds",
                "value": {
                    "interests": ["Heritage", "Cultural"],
                    "budget": 1500.0,
                    "preferred_crowd_level": "moderate",
                    "prefer_hidden_gems": False,
                    "limit": 5,
                },
            },
        },
    ),
    db: Session = Depends(get_db),
) -> Any:
    """
    Generate personalized, transparent, ranked destination recommendations:
    - Reuses the proposal scoring engine (calculate_destination_score).
    - Applies user preferences, candidate filters, available time schedule constraints, and category diversity.
    - Returns up to requested limit with 3-5 factual explainability reasons per item.
    """
    return get_recommendations(request=request, db=db)


@router.get(
    "/alternatives/{destination_id}",
    response_model=AlternativeDestinationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Find alternative destinations for a specific site (Step 4 Scaffolding)",
)
def get_alternatives_for_destination(
    destination_id: int,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of alternative destinations"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Scaffolding endpoint: Retrieves lower-crowd or hidden-gem alternatives for a destination.
    Lays the foundation for future overcrowding-redirection workflows.
    """
    return find_alternative_destinations(destination_id=destination_id, limit=limit, db=db)
