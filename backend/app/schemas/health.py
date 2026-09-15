from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    database_connected: bool
    database_status: str
    timestamp: datetime
