from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.session import get_db
from app.schemas.common import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, object]:
    return {
        "status": "running",
        "message": "TraffiSense AI Backend is running.",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "links": {
            "health": "/health",
            "docs": "/docs",
            "analytics": "/analytics",
            "frontend": "https://grid-lock-round-2.vercel.app/dashboard",
        },
    }


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        database="ok",
        timestamp=datetime.now(UTC),
    )

