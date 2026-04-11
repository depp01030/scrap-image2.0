from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, object]:
    return {
        "success": True,
        "service": "scrap-image2.0-local-service",
        "port": settings.port,
    }

