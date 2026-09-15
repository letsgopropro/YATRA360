from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health() -> HealthResponse:
    """
    Health check endpoint reporting application version, timestamp,
    and PostgreSQL database connectivity.
    """
    db_connected, db_status = check_database_connection()

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        database_connected=db_connected,
        database_status=db_status,
        timestamp=datetime.now(timezone.utc),
    )
