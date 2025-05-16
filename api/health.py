"""Health check endpoint."""

from fastapi import APIRouter, status
from core.db import user_db

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    mongodb_status = "healthy"
    try:
        user_db.db.command('ping')
    except Exception as e:
        mongodb_status = f"unhealthy: {str(e)}"
        logger.error(f"MongoDB health check failed: {str(e)}")

    return {
        "status": "healthy",
        "components": {
            "api": "healthy",
            "mongodb": mongodb_status
        }
    }

@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness():
    """Readiness endpoint."""
    return {"status": "ready"}
