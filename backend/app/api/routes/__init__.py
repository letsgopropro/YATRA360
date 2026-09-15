from fastapi import APIRouter
from app.api.routes import (
    auth,
    businesses,
    crowd,
    destinations,
    itineraries,
    reviews,
    safety,
    scoring,
    recommendations,
    users,
)
from app.api.v1.endpoints import health

api_router = APIRouter()

# Include all modular sub-routers
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(destinations.router)
api_router.include_router(scoring.router)
api_router.include_router(recommendations.router)
api_router.include_router(businesses.router)
api_router.include_router(crowd.router)
api_router.include_router(safety.router)
api_router.include_router(reviews.router)
api_router.include_router(itineraries.router)

__all__ = ["api_router"]
