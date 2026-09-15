from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.api.v1.router import api_v1_router
from app.api.routes import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers (supports both /api/v1 and /api)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


@app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
def redirect_v1_docs():
    return RedirectResponse(url="/docs")


@app.get(f"{settings.API_V1_STR}/openapi.json", include_in_schema=False)
def redirect_v1_openapi():
    return RedirectResponse(url="/openapi.json")
