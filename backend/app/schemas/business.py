from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BusinessBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    latitude: float
    longitude: float
    contact_info: Optional[str] = Field(default=None, max_length=255)
    website: Optional[str] = Field(default=None, max_length=255)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True


class BusinessCreate(BusinessBase):
    pass


class BusinessResponse(BusinessBase):
    id: int
    owner_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
