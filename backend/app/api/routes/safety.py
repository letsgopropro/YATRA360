from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.destination import Destination
from app.models.safety import Safety
from app.schemas.safety import SafetyResponse

router = APIRouter(prefix="/safety", tags=["Safety Advisory"])


@router.get("/{destination_id}", response_model=SafetyResponse)
def get_safety_by_destination_id(
    destination_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get safety advisory and emergency facility information for a destination.
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
