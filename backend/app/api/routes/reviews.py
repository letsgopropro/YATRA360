from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.review import Review
from app.schemas.review import ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review_by_id(
    review_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve an individual review by ID.
    """
    review = db.scalar(select(Review).where(Review.id == review_id))
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found"
        )
    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        destination_id=review.destination_id,
        rating=review.rating,
        comment=review.comment,
        reported_crowd_level=review.reported_crowd_level,
        created_at=review.created_at,
        user_name=review.user.full_name if review.user else None
    )
