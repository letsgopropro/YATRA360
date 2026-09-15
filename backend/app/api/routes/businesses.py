from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.business import Business
from app.schemas.business import BusinessResponse

router = APIRouter(prefix="/businesses", tags=["Businesses"])


@router.get("", response_model=List[BusinessResponse])
def list_businesses(
    category: Optional[str] = Query(None, description="Filter by category (e.g. restaurant, guide, artisan)"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """
    List verified local businesses and artisans with category, city, and state filtering.
    """
    stmt = select(Business).where(Business.is_active == True)

    if category:
        stmt = stmt.where(Business.category.ilike(f"%{category.strip()}%"))
    if city:
        stmt = stmt.where(Business.city.ilike(f"%{city.strip()}%"))
    if state:
        stmt = stmt.where(Business.state.ilike(f"%{state.strip()}%"))
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where((Business.name.ilike(term)) | (Business.description.ilike(term)))

    stmt = stmt.offset(skip).limit(limit)
    businesses = db.scalars(stmt).all()
    return businesses


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business_by_id(
    business_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve single business profile by ID.
    """
    business = db.scalar(select(Business).where(Business.id == business_id))
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} not found"
        )
    return business
