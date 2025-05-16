"""REST API routes for GitHappy API."""

from fastapi import APIRouter

from api.routes.auth import router as auth_router
# from api.routes.changelog import router as changelog_router
# from api.routes.tags import router as tags_router
from api.health import router as health_router

router = APIRouter()

router.include_router(health_router)
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# router.include_router(changelog_router, prefix="/changelog", tags=["Changelog"])
# router.include_router(tags_router, prefix="/tags", tags=["Tags"])
from models import User
from db import user_db
from core.logger import logger
from core.auth import get_password_hash
demo_user = User(
    username="demo",
    password_hash=get_password_hash("password123")
)
user_db.create(demo_user)
logger.info(f"Created demo user with ID {demo_user.id}")