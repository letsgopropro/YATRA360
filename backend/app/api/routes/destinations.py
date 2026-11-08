from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, or_, select
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
from app.services.preference_matcher import (
    THEMATIC_INTEREST_CORRELATIONS,
    resolve_canonical_category,
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
    stmt = select(Destination).where(Destination.is_active == True)

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
        resolved_categories = set()
        for interest in travel_request.interests:
            canon = resolve_canonical_category(interest)
            if canon:
                resolved_categories.add(canon)
            elif interest.strip().lower() in THEMATIC_INTEREST_CORRELATIONS:
                resolved_categories.update(
                    THEMATIC_INTEREST_CORRELATIONS[interest.strip().lower()]["correlated_categories"]
                )
            elif interest.strip():
                resolved_categories.add(interest.strip())
        if resolved_categories:
            stmt = stmt.where(Destination.category.in_(list(resolved_categories)))

    destinations = db.scalars(stmt.limit(50)).all()

    # If strict search yielded 0 results, fallback to broader state or all destinations
    if not destinations and travel_request.destination:
        destinations = db.scalars(select(Destination).where(Destination.is_active == True).limit(10)).all()

    collected = [
        CollectedDestination(
            id=d.id,
            name=d.name,
            slug=d.slug,
            city=d.city,
            district=d.district,
            state=d.state,
            category=d.category,
            latitude=d.latitude,
            longitude=d.longitude,
            entry_fee=d.entry_fee,
            budget_category=d.budget_category,
            safety_rating=d.safety_rating,
            base_crowd_level=d.base_crowd_level,
            image_url=d.image_url,
            image_attribution=d.image_attribution,
            image_license=d.image_license,
            image_source_url=d.image_source_url,
            best_time_to_visit=d.best_time_to_visit,
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


def _build_destination_filter_conditions(
    category: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    is_hidden_gem: Optional[bool] = None,
    crowd_level: Optional[str] = None,
    search: Optional[str] = None,
    include_inactive: bool = False,
) -> list:
    """Build reusable SQLAlchemy filter conditions for destination queries."""
    conditions = []
    if not include_inactive:
        conditions.append(Destination.is_active == True)

    if category and category.strip().lower() != "all":
        clean_cat = category.strip()
        canon = resolve_canonical_category(clean_cat)
        if canon:
            conditions.append(Destination.category.ilike(f"%{canon}%"))
        elif clean_cat.lower() in THEMATIC_INTEREST_CORRELATIONS:
            corr_cats = THEMATIC_INTEREST_CORRELATIONS[clean_cat.lower()]["correlated_categories"]
            conditions.append(Destination.category.in_(list(corr_cats)))
        else:
            conditions.append(Destination.category.ilike(f"%{clean_cat}%"))

    if city:
        conditions.append(Destination.city.ilike(f"%{city.strip()}%"))

    if state and state.strip().lower() not in ("all", "all states"):
        clean_state = state.strip()
        if "jammu" in clean_state.lower():
            conditions.append(
                (Destination.state.ilike("%Jammu & Kashmir%"))
                | (Destination.state.ilike("%Jammu and Kashmir%"))
            )
        elif "andaman" in clean_state.lower():
            conditions.append(
                (Destination.state.ilike("%Andaman & Nicobar%"))
                | (Destination.state.ilike("%Andaman and Nicobar%"))
            )
        else:
            conditions.append(Destination.state.ilike(f"%{clean_state}%"))

    if is_hidden_gem is not None:
        conditions.append(Destination.is_hidden_gem == is_hidden_gem)

    if crowd_level:
        conditions.append(Destination.base_crowd_level.ilike(f"%{crowd_level.strip()}%"))

    if search:
        term = f"%{search.strip()}%"
        conditions.append(
            (Destination.name.ilike(term)) | (Destination.description.ilike(term))
        )

    return conditions


@router.get("", response_model=List[DestinationResponse])
def list_destinations(
    category: Optional[str] = Query(None, description="Filter by category (e.g. Heritage, Nature)"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    is_hidden_gem: Optional[bool] = Query(None, description="Filter hidden gems"),
    crowd_level: Optional[str] = Query(None, description="Filter by base crowd level"),
    search: Optional[str] = Query(None, description="Search keyword in name or description"),
    sort_by: Optional[str] = Query("id", description="Sort field: id, name, safety_rating, entry_fee"),
    sort_order: Optional[str] = Query("asc", description="Sort direction: asc or desc"),
    include_inactive: bool = Query(False, description="Include inactive/test destinations"),
    skip: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=500),
    response: Response = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    List destinations with filtering, sorting, pagination, and total match count in X-Total-Count header.
    """
    conditions = _build_destination_filter_conditions(
        category=category,
        city=city,
        state=state,
        is_hidden_gem=is_hidden_gem,
        crowd_level=crowd_level,
        search=search,
        include_inactive=include_inactive,
    )

    # 1. Total matching count
    count_stmt = select(func.count(Destination.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total_count = db.scalar(count_stmt) or 0

    if response is not None:
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

    # 2. Query destinations
    stmt = select(Destination)
    if conditions:
        stmt = stmt.where(*conditions)

    # Sorting
    if sort_by == "name":
        order_col = desc(Destination.name) if sort_order == "desc" else asc(Destination.name)
    elif sort_by == "safety_rating":
        order_col = asc(Destination.safety_rating) if sort_order == "asc" else desc(Destination.safety_rating)
    elif sort_by == "entry_fee":
        order_col = desc(Destination.entry_fee) if sort_order == "desc" else asc(Destination.entry_fee)
    else:
        order_col = desc(Destination.id) if sort_order == "desc" else asc(Destination.id)

    stmt = stmt.order_by(order_col).offset(skip).limit(limit)
    destinations = db.scalars(stmt).all()
    return destinations


@router.get("/stats", summary="Get overall destination database statistics")
def get_destinations_stats(
    db: Session = Depends(get_db)
) -> Any:
    """Return platform-wide active destination counts and distribution metrics."""
    total_active = db.scalar(
        select(func.count(Destination.id)).where(Destination.is_active == True)
    ) or 0
    total_all = db.scalar(select(func.count(Destination.id))) or 0
    total_inactive = total_all - total_active
    hidden_gems = db.scalar(
        select(func.count(Destination.id)).where(
            Destination.is_active == True, Destination.is_hidden_gem == True
        )
    ) or 0
    states_count = db.scalar(
        select(func.count(func.distinct(Destination.state))).where(
            Destination.is_active == True
        )
    ) or 0
    categories_count = db.scalar(
        select(func.count(func.distinct(Destination.category))).where(
            Destination.is_active == True
        )
    ) or 0

    return {
        "total_active": total_active,
        "total_inactive": total_inactive,
        "total_all": total_all,
        "hidden_gems_count": hidden_gems,
        "states_count": states_count,
        "categories_count": categories_count,
    }


@router.get("/count", summary="Get count of destinations matching filters")
def get_destinations_count(
    category: Optional[str] = Query(None, description="Filter by category"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    is_hidden_gem: Optional[bool] = Query(None, description="Filter hidden gems"),
    crowd_level: Optional[str] = Query(None, description="Filter by crowd level"),
    search: Optional[str] = Query(None, description="Search keyword"),
    include_inactive: bool = Query(False, description="Include inactive/test destinations"),
    db: Session = Depends(get_db)
) -> Any:
    """Return total count of destinations matching specified query filters."""
    conditions = _build_destination_filter_conditions(
        category=category,
        city=city,
        state=state,
        is_hidden_gem=is_hidden_gem,
        crowd_level=crowd_level,
        search=search,
        include_inactive=include_inactive,
    )
    count_stmt = select(func.count(Destination.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total_count = db.scalar(count_stmt) or 0
    return {"total": total_count}


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

