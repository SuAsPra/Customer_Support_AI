from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter(tags=["Health"])

@router.get("/health", summary="Health check endpoint")
def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV
    }
