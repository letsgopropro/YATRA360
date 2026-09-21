from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.crowd_metric import CrowdMetric
from app.models.destination import Destination
from app.models.review import Review
from app.models.safety import Safety
from app.models.user import User
from app.schemas.crowd import CrowdMetricResponse
from app.schemas.destination import DestinationResponse
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.safety import SafetyResponse
from app.schemas.scoring import (
    CollectedDestination,
    DataCollectionResponse,
    DestinationScoreResponse,
    TravelRequest,
)
from app.services.scoring_engine import calculate_destination_score

router = APIRouter(prefix="/destinations", tags=["Destinations"])


@router.post(
    "/collect",
    response_model=DataCollectionResponse,
    summary="Step 1 & Step 2: Validate User Input and Collect Destination Data",
)
def collect_destination_data(
    travel_request: TravelRequest = Body(
        ...,
        openapi_examples={
            "jaipur_friends": {
                "summary": "Jaipur Trip Sample (Step 1)",
                "description": "Realistic sample request from project proposal",
                "value": {
                    "destination": "Jaipur",
                    "budget": 2000.0,
                    "available_time": "1 day",
                    "interests": ["Culture", "Nature"],
                    "travel_group": "Friends",
                },
            }
        },
    ),
    db: Session = Depends(get_db),
) -> Any:
    """
    Workflow verification endpoint for Step 1 (User Input) and Step 2 (Data Collection):
    1. Validates and parses the user's travel request (destination, budget, time, interests, travel group).
    2. Queries the database and retrieves matching destination data (name, coordinates, crowd, safety, cost, accessibility).
    """
    stmt = select(Destination)

    # Filter by destination/city/state if provided
    if travel_request.destination:
        term = f"%{travel_request.destination.strip()}%"
        stmt = stmt.where(
            or_(
                Destination.city.ilike(term),
                Destination.state.ilike(term),
                Destination.name.ilike(term),
            )
        )

    # Filter by category if interests provided and not filtering by a single specific monument
    if travel_request.interests and not travel_request.destination:
        category_clauses = [
            Destination.category.ilike(f"%{interest.strip()}%")
            for interest in travel_request.interests
            if interest.strip()
        ]
        if category_clauses:
            stmt = stmt.where(or_(*category_clauses))

    destinations = db.scalars(stmt.limit(50)).all()

    # If strict search yielded 0 results, fallback to broader state or all destinations
    if not destinations and travel_request.destination:
        destinations = db.scalars(select(Destination).limit(10)).all()

    collected = [
        CollectedDestination(
            id=d.id,
            name=d.name,
            slug=d.slug,
            city=d.city,
            state=d.state,
            category=d.category,
            latitude=d.latitude,
            longitude=d.longitude,
            entry_fee=d.entry_fee,
            safety_rating=d.safety_rating,
            base_crowd_level=d.base_crowd_level,
            accessibility_info=d.accessibility_info,
            estimated_visit_duration=d.estimated_visit_duration,
            is_hidden_gem=d.is_hidden_gem,
            weather_condition="Prototype baseline (moderate / clear)",
        )
        for d in destinations
    ]

    return DataCollectionResponse(
        step_1_user_input=travel_request,
        step_2_data_collection=collected,
        total_found=len(collected),
        status="SUCCESS",
    )


@router.get("", response_model=List[DestinationResponse])
def list_destinations(
    category: Optional[str] = Query(None, description="Filter by category (e.g. Heritage, Nature)"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    is_hidden_gem: Optional[bool] = Query(None, description="Filter hidden gems"),
    crowd_level: Optional[str] = Query(None, description="Filter by base crowd level"),
    search: Optional[str] = Query(None, description="Search keyword in name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    List destinations with filtering by category, city, state, hidden-gem status, and crowd level.
    """
    stmt = select(Destination)

    if category:
        stmt = stmt.where(Destination.category.ilike(f"%{category.strip()}%"))
    if city:
        stmt = stmt.where(Destination.city.ilike(f"%{city.strip()}%"))
    if state:
        stmt = stmt.where(Destination.state.ilike(f"%{state.strip()}%"))
    if is_hidden_gem is not None:
        stmt = stmt.where(Destination.is_hidden_gem == is_hidden_gem)
    if crowd_level:
        stmt = stmt.where(Destination.base_crowd_level.ilike(f"%{crowd_level.strip()}%"))
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            (Destination.name.ilike(term)) | (Destination.description.ilike(term))
        )

    stmt = stmt.offset(skip).limit(limit)
    destinations = db.scalars(stmt).all()
    return destinations


@router.get("/slug/{slug}", response_model=DestinationResponse)
def get_destination_by_slug(
    slug: str,
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve destination details by URL slug."""
    destination = db.scalar(select(Destination).where(Destination.slug == slug))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with slug '{slug}' not found"
        )
    return destination


@router.get("/{destination_id}", response_model=DestinationResponse)
def get_destination_by_id(
    destination_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve destination details by primary key ID."""
    destination = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with ID {destination_id} not found"
        )
    return destination


@router.get("/{destination_id}/crowd", response_model=CrowdMetricResponse)
def get_destination_crowd(
    destination_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve latest recorded crowd metric for a destination.
    Returns 404 if destination is not found.
    """
    destination = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with ID {destination_id} not found"
        )

    stmt = (
        select(CrowdMetric)
        .where(CrowdMetric.destination_id == destination_id)
        .order_by(desc(CrowdMetric.recorded_at))
        .limit(1)
    )
    metric = db.scalar(stmt)

    if not metric:
        # Fallback to base crowd level if no metric recorded yet
        return CrowdMetricResponse(
            id=0,
            destination_id=destination.id,
            crowd_level=destination.base_crowd_level,
            visitor_count=None,
            recorded_at=destination.created_at
        )

    return metric


@router.get("/{destination_id}/safety", response_model=SafetyResponse)
def get_destination_safety(
    destination_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve destination safety advisory and emergency contact information.
    Returns 404 if destination is not found.
    """
    destination = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with ID {destination_id} not found"
        )

    stmt = (
        select(Safety)
        .where(Safety.destination_id == destination_id)
        .order_by(desc(Safety.updated_at))
        .limit(1)
    )
    safety_record = db.scalar(stmt)

    if not safety_record:
        # Construct baseline safety advisory if specific record not yet authored
        return SafetyResponse(
            id=0,
            destination_id=destination.id,
            safety_level="safe" if destination.safety_rating >= 4.0 else "moderate_risk",
            safety_rating=destination.safety_rating,
            risk_description="Standard travel safety precautions advised.",
            emergency_information="National Tourist Helpline: 1363. Police: 112.",
            source="YATRA360 Safety Advisory",
            updated_at=destination.created_at,
            created_at=destination.created_at
        )

    return safety_record


@router.get("/{destination_id}/reviews", response_model=List[ReviewResponse])
def get_destination_reviews(
    destination_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve user reviews and crowd feedback for a specific destination.
    """
    destination = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with ID {destination_id} not found"
        )

    stmt = (
        select(Review)
        .where(Review.destination_id == destination_id)
        .order_by(desc(Review.created_at))
        .offset(skip)
        .limit(limit)
    )
    reviews = db.scalars(stmt).all()
    
    response = []
    for r in reviews:
        response.append(
            ReviewResponse(
                id=r.id,
                user_id=r.user_id,
                destination_id=r.destination_id,
                rating=r.rating,
                comment=r.comment,
                reported_crowd_level=r.reported_crowd_level,
                created_at=r.created_at,
                user_name=r.user.full_name if r.user else None
            )
        )
    return response


@router.post("/{destination_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_destination_review(
    destination_id: int,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Post a verified review with 1-5 rating for a destination (requires authentication).
    """
    destination = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with ID {destination_id} not found"
        )

    review = Review(
        user_id=current_user.id,
        destination_id=destination_id,
        rating=review_in.rating,
        comment=review_in.comment.strip() if review_in.comment else None,
        reported_crowd_level=review_in.reported_crowd_level,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        destination_id=review.destination_id,
        rating=review.rating,
        comment=review.comment,
        reported_crowd_level=review.reported_crowd_level,
        created_at=review.created_at,
        user_name=current_user.full_name
    )


@router.post(
    "/{destination_id}/score",
    response_model=DestinationScoreResponse,
    summary="Calculate suitability score for a destination",
)
def score_destination_endpoint(
    destination_id: int,
    travel_request: Optional[TravelRequest] = Body(default=None),
    db: Session = Depends(get_db),
) -> Any:
    """
    Calculate transparent multi-criteria suitability score for a single destination.
    Accepts user travel preferences or applies neutral prototype baselines / renormalization.
    """
    destination = db.scalar(select(Destination).where(Destination.id == destination_id))
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with ID {destination_id} not found",
        )
    req = travel_request or TravelRequest()
    return calculate_destination_score(destination=destination, travel_request=req)

