from app.schemas.auth import LoginRequest, Token, TokenPayload
from app.schemas.business import BusinessBase, BusinessCreate, BusinessResponse
from app.schemas.crowd import CrowdMetricResponse
from app.schemas.destination import DestinationBase, DestinationCreate, DestinationResponse
from app.schemas.health import HealthResponse
from app.schemas.itinerary import (
    ItineraryBase,
    ItineraryCreate,
    ItineraryItemBase,
    ItineraryItemCreate,
    ItineraryItemResponse,
    ItineraryResponse,
)
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.safety import SafetyResponse
from app.schemas.user import UserBase, UserCreate, UserResponse

from app.schemas.scoring import (
    BatchDestinationScoreResponse,
    CollectedDestination,
    DataCollectionResponse,
    DestinationScoreResponse,
    ScoringComponents,
    ScoringWeights,
    TravelRequest,
)
from app.schemas.recommendation import (
    AlternativeDestinationsResponse,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)

__all__ = [
    "LoginRequest",
    "Token",
    "TokenPayload",
    "HealthResponse",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "DestinationBase",
    "DestinationCreate",
    "DestinationResponse",
    "BusinessBase",
    "BusinessCreate",
    "BusinessResponse",
    "CrowdMetricResponse",
    "SafetyResponse",
    "ReviewCreate",
    "ReviewResponse",
    "ItineraryBase",
    "ItineraryCreate",
    "ItineraryResponse",
    "ItineraryItemBase",
    "ItineraryItemCreate",
    "ItineraryItemResponse",
    "TravelRequest",
    "ScoringComponents",
    "ScoringWeights",
    "DestinationScoreResponse",
    "BatchDestinationScoreResponse",
    "CollectedDestination",
    "DataCollectionResponse",
    "RecommendationRequest",
    "RecommendationItem",
    "RecommendationResponse",
    "AlternativeDestinationsResponse",
]
