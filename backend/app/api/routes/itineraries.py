from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.destination import Destination
from app.models.itinerary import Itinerary
from app.models.itinerary_item import ItineraryItem
from app.models.user import User
from app.schemas.itinerary import (
    ItineraryCreate,
    ItineraryItemResponse,
    ItineraryResponse,
)

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])


def _format_itinerary_response(itinerary: Itinerary) -> ItineraryResponse:
    items = []
    for item in itinerary.items:
        items.append(
            ItineraryItemResponse(
                id=item.id,
                itinerary_id=item.itinerary_id,
                destination_id=item.destination_id,
                day_number=item.day_number,
                visit_order=item.visit_order,
                notes=item.notes,
                destination_name=item.destination.name if item.destination else None,
            )
        )
    return ItineraryResponse(
        id=itinerary.id,
        user_id=itinerary.user_id,
        title=itinerary.title,
        start_date=itinerary.start_date,
        end_date=itinerary.end_date,
        budget=itinerary.budget,
        created_at=itinerary.created_at,
        items=items,
    )


@router.get("", response_model=List[ItineraryResponse])
def list_my_itineraries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve all travel itineraries created by the authenticated user.
    """
    stmt = (
        select(Itinerary)
        .where(Itinerary.user_id == current_user.id)
        .order_by(desc(Itinerary.created_at))
    )
    itineraries = db.scalars(stmt).all()
    return [_format_itinerary_response(it) for it in itineraries]


@router.post("", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
def create_itinerary(
    itinerary_in: ItineraryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new travel itinerary for the authenticated user with optional stop items.
    """
    itinerary = Itinerary(
        user_id=current_user.id,
        title=itinerary_in.title.strip(),
        start_date=itinerary_in.start_date,
        end_date=itinerary_in.end_date,
        budget=itinerary_in.budget,
    )
    db.add(itinerary)
    db.flush()

    if itinerary_in.items:
        for item_data in itinerary_in.items:
            dest = db.scalar(select(Destination).where(Destination.id == item_data.destination_id))
            if not dest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination ID {item_data.destination_id} not found"
                )
            item = ItineraryItem(
                itinerary_id=itinerary.id,
                destination_id=item_data.destination_id,
                day_number=item_data.day_number,
                visit_order=item_data.visit_order,
                notes=item_data.notes,
            )
            db.add(item)

    db.commit()
    db.refresh(itinerary)
    return _format_itinerary_response(itinerary)


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
def get_itinerary_by_id(
    itinerary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve specific itinerary by ID. Enforces ownership: only owner or administrator can view.
    """
    itinerary = db.scalar(select(Itinerary).where(Itinerary.id == itinerary_id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Itinerary with ID {itinerary_id} not found"
        )

    if itinerary.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this itinerary"
        )

    return _format_itinerary_response(itinerary)
