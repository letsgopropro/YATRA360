from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None
    reported_crowd_level: Optional[str] = Field(default=None, max_length=20)


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    destination_id: int
    rating: int
    comment: Optional[str] = None
    reported_crowd_level: Optional[str] = None
    created_at: datetime
    user_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
