from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ItineraryItemBase(BaseModel):
    destination_id: int
    day_number: int = Field(default=1, ge=1)
    visit_order: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class ItineraryItemCreate(ItineraryItemBase):
    pass


class ItineraryItemResponse(ItineraryItemBase):
    id: int
    itinerary_id: int
    destination_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ItineraryBase(BaseModel):
    title: str = Field(..., max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(default=None, ge=0.0)


class ItineraryCreate(ItineraryBase):
    items: Optional[List[ItineraryItemCreate]] = None


class ItineraryResponse(ItineraryBase):
    id: int
    user_id: int
    created_at: datetime
    items: List[ItineraryItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
