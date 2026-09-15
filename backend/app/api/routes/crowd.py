from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.crowd_metric import CrowdMetric
from app.models.destination import Destination
from app.schemas.crowd import CrowdMetricResponse

router = APIRouter(prefix="/crowd", tags=["Crowd Information"])


@router.get("/{destination_id}", response_model=CrowdMetricResponse)
def get_crowd_by_destination_id(
    destination_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get latest crowd indicators for a destination.
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
        return CrowdMetricResponse(
            id=0,
            destination_id=destination.id,
            crowd_level=destination.base_crowd_level,
            visitor_count=None,
            recorded_at=destination.created_at
        )

    return metric
