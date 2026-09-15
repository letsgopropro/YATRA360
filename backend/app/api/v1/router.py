from fastapi import APIRouter
from app.api.routes import api_router

api_v1_router = APIRouter()

# Register all routes into v1 router
api_v1_router.include_router(api_router)
