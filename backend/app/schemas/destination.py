from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DestinationBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=220)
    description: str
    category: str = Field(..., max_length=50)
    state: str = Field(..., max_length=100)
    city: str = Field(..., max_length=100)
    latitude: float
    longitude: float
    entry_fee: float = Field(default=0.0, ge=0.0)
    safety_rating: float = Field(default=4.0, ge=1.0, le=5.0)
    is_hidden_gem: bool = False
    base_crowd_level: str = Field(default="moderate", max_length=20)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    district: Optional[str] = Field(default=None, max_length=100)
    best_time_to_visit: Optional[str] = Field(default=None, max_length=150)
    budget_category: Optional[str] = Field(default=None, max_length=50)
    image_attribution: Optional[str] = None
    image_license: Optional[str] = Field(default=None, max_length=200)
    image_source_url: Optional[str] = Field(default=None, max_length=1000)
    is_active: bool = True
    accessibility_info: Optional[str] = None
    estimated_visit_duration: Optional[int] = None


class DestinationCreate(DestinationBase):
    pass


class DestinationResponse(DestinationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
