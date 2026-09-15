"""
YATRA360 — Recommendation Engine Schemas
Defines request and response models for personalized destination recommendations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.scoring import ScoringComponents, TravelRequest


class RecommendationRequest(TravelRequest):
    """
    User recommendation request.
    Inherits all user preferences from TravelRequest and adds search/response controls.
    """
    # Search / Filter controls
    category: Optional[str] = Field(
        default=None,
        description="Filter candidates by specific category (e.g. 'Heritage', 'Nature')"
    )
    state: Optional[str] = Field(
        default=None,
        description="Filter candidates by state or union territory (e.g. 'Rajasthan', 'Kerala')"
    )
    is_hidden_gem: Optional[bool] = Field(
        default=None,
        description="Strictly filter candidates by hidden-gem status (True/False)"
    )

    # Response controls
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of recommendations to return (returns up to this count)"
    )
    apply_diversity: bool = Field(
        default=True,
        description="Whether to apply conservative category diversity balancing"
    )
    diversity_threshold: float = Field(
        default=10.0,
        ge=0.0,
        le=25.0,
        description="Score margin within which a diverse category candidate can be promoted"
    )


class RecommendationItem(BaseModel):
    """Individual recommended destination item with explainable reasons."""
    destination_id: int
    destination_name: str
    slug: str
    city: str
    state: str
    category: str
    is_hidden_gem: bool
    entry_fee: float
    safety_rating: float
    base_crowd_level: str
    estimated_visit_duration: Optional[int] = None
    overall_score: float = Field(..., ge=0.0, le=100.0)
    components: ScoringComponents
    reasons: List[str] = Field(
        default_factory=list,
        description="3-5 concise, transparent reasons explaining why this destination was recommended"
    )

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    """Top-level response containing ranked personalized recommendations."""
    total_candidates_evaluated: int
    recommendations_count: int
    recommendations: List[RecommendationItem]
    request_summary: TravelRequest
    applied_filters: Dict[str, Any]
    scoring_version: str = "1.0-weighted-content"


class AlternativeDestinationsResponse(BaseModel):
    """Scaffolding response containing alternatives for a specific destination."""
    source_destination_id: int
    source_destination_name: str
    source_crowd_level: str
    alternatives_count: int
    alternatives: List[RecommendationItem]
