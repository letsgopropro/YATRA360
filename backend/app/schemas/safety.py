from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SafetyResponse(BaseModel):
    id: int
    destination_id: int
    safety_level: str
    safety_rating: Optional[float] = None
    risk_description: Optional[str] = None
    emergency_information: Optional[str] = None
    source: Optional[str] = None
    updated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
