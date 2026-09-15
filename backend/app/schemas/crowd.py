from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CrowdMetricResponse(BaseModel):
    id: int
    destination_id: int
    crowd_level: str
    visitor_count: Optional[int] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
