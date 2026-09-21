"""
YATRA360 — Scoring Engine Schemas
Defines request and response models for destination suitability scoring.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TravelRequest(BaseModel):
    """
    Structured user travel request used to evaluate destination suitability.
    All fields are optional to handle partial or unspecified user preferences gracefully.
    """
    destination: Optional[str] = Field(
        default=None,
        description="Target destination, city, or region (e.g. 'Jaipur')"
    )
    preferred_destination: Optional[str] = Field(
        default=None,
        description="Alternative alias for target destination"
    )
    origin: Optional[str] = Field(
        default=None,
        description="Origin city or location name"
    )
    interests: Optional[List[str]] = Field(
        default_factory=list,
        description="Preferred categories or themes (e.g. ['Culture', 'Nature'])"
    )
    preferred_activities: Optional[List[str]] = Field(
        default_factory=list,
        description="Preferred specific activities (e.g. ['trekking', 'photography'])"
    )
    budget: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Available budget in INR (e.g. 2000)"
    )
    available_time: Optional[str] = Field(
        default=None,
        description="Human-readable available time duration (e.g. '1 day', 'Weekend')"
    )
    available_time_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Available visit time duration in minutes"
    )
    travel_group: Optional[str] = Field(
        default=None,
        description="Travel group composition: 'Solo', 'Couple', 'Family', 'Friends', 'Senior'"
    )
    user_latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="User starting latitude for distance calculation"
    )
    user_longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="User starting longitude for distance calculation"
    )
    max_distance_km: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Maximum travel radius in kilometers"
    )
    requires_accessibility: Optional[bool] = Field(
        default=False,
        description="True if step-free / wheelchair accessibility is needed"
    )
    accessibility_requirements: Optional[str] = Field(
        default=None,
        description="Specific accessibility requirement description"
    )
    preferred_crowd_level: Optional[str] = Field(
        default=None,
        description="Preferred crowd level: 'low', 'moderate', or 'high'"
    )
    prefer_hidden_gems: Optional[bool] = Field(
        default=None,
        description="Preference for offbeat/hidden gem destinations"
    )
    weather_preference: Optional[str] = Field(
        default=None,
        description="Weather/climate preference (e.g. 'cool', 'warm', 'pleasant')"
    )
    preferred_weather: Optional[str] = Field(
        default=None,
        description="Alias for weather preference"
    )

    model_config = ConfigDict(extra="ignore")


class CollectedDestination(BaseModel):
    """Destination attributes collected from the database for Step 2."""
    id: int
    name: str
    slug: str
    city: str
    state: str
    category: str
    latitude: float
    longitude: float
    entry_fee: float
    safety_rating: float
    base_crowd_level: str
    accessibility_info: Optional[str] = None
    estimated_visit_duration: Optional[int] = None
    is_hidden_gem: bool
    weather_condition: str = "Prototype baseline (moderate)"

    model_config = ConfigDict(from_attributes=True)


class DataCollectionResponse(BaseModel):
    """Verifies Step 1 (User Input) and Step 2 (Data Collection)."""
    step_1_user_input: TravelRequest
    step_2_data_collection: List[CollectedDestination]
    total_found: int
    status: str = "SUCCESS"


class ScoringComponents(BaseModel):
    """
    Normalized 0-100 score for each evaluation component.
    Can be None if data is genuinely unavailable and weight was renormalized.
    """
    preference_match: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    safety: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    crowd_suitability: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    accessibility_distance: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    cost_suitability: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    weather_condition: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class ScoringWeights(BaseModel):
    """Proposal weights assigned to each component (sum = 1.0)."""
    preference_match: float = 0.25
    safety: float = 0.20
    crowd_suitability: float = 0.20
    accessibility_distance: float = 0.15
    cost_suitability: float = 0.10
    weather_condition: float = 0.10


class ScoreBreakdown(BaseModel):
    """Standardized breakdown keys as requested in YATRA360 proposal."""
    preference: Optional[float] = None
    safety: Optional[float] = None
    crowd: Optional[float] = None
    accessibility: Optional[float] = None
    cost: Optional[float] = None
    weather: Optional[float] = None


class DestinationScoreResponse(BaseModel):
    """Complete scoring response detailing overall score, components, and explanations."""
    destination_id: int
    destination_name: str
    destination_slug: str
    overall_score: float = Field(..., ge=0.0, le=100.0)
    components: ScoringComponents
    score_breakdown: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Standardized component breakdown: preference, safety, crowd, accessibility, cost, weather"
    )
    weights: ScoringWeights
    applied_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Effective weights applied after dynamic weight renormalization"
    )
    data_quality: Dict[str, str] = Field(
        default_factory=dict,
        description="Source status for each component: 'real', 'fallback', or 'missing'"
    )
    explanations: Dict[str, str] = Field(
        default_factory=dict,
        description="Transparent breakdown explaining the score rationale"
    )

    model_config = ConfigDict(from_attributes=True)


class BatchDestinationScoreResponse(BaseModel):
    """Response containing a ranked list of scored destinations."""
    total: int
    results: List[DestinationScoreResponse]
