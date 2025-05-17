"""Admin-only routes for GitHappy API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.auth import TokenData, get_current_user, role_required
from core.logger import logger
from core.db import user_db, changelog_db, tag_db
from models import Role, User, ChangelogEntry, Tag, PyObjectId

router = APIRouter()

@router.get("/users", response_model=list[User])
async def get_all_users(
        skip: int = Query(0, description="Number of users to skip"),
        limit: int = Query(20, description="Number of users to return"),
        current_user: TokenData = Depends(role_required([Role.ADMIN])),
):
    """
    Get all users (admin only).

    Parameters
    ----------
    skip : int
        Number of users to skip
    limit : int
        Maximum number of users to return
    current_user : TokenData
        Current authenticated admin user

    Returns
    -------
    list[User]
        List of all users
    """
    users = user_db.list_all()[skip:skip+limit]
    # Hide password hashes
    for user in users:
        user.password_hash = "********"

    logger.info(f"Admin {current_user.username} retrieved {len(users)} users")
    return users

@router.get("/stats", response_model=dict)
async def get_system_stats(
        current_user: TokenData = Depends(role_required([Role.ADMIN])),
):
    """
    Get system statistics (admin only).

    Parameters
    ----------
    current_user : TokenData
        Current authenticated admin user

    Returns
    -------
    dict
        System statistics
    """
    user_count = user_db.count({})
    entry_count = changelog_db.count({})
    tag_count = tag_db.count({})

    stats = {
        "users": user_count,
        "entries": entry_count,
        "tags": tag_count,
        "entry_types": {},
    }

    entry_types = {}
    all_entries = changelog_db.list_all()
    for entry in all_entries:
        entry_type = entry.entry_type.value
        if entry_type not in entry_types:
            entry_types[entry_type] = 0
        entry_types[entry_type] += 1

    stats["entry_types"] = entry_types

    logger.info(f"Admin {current_user.username} retrieved system stats")
    return stats

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_id: str,
        current_user: TokenData = Depends(role_required([Role.ADMIN])),
):
    """
    Delete a user (admin only).

    Parameters
    ----------
    user_id : str
        User ID to delete
    current_user : TokenData
        Current authenticated admin user

    Returns
    -------
    None

    Raises
    ------
    HTTPException
        404 if user not found
    """
    user_id_obj = PyObjectId(user_id)
    user = user_db.get(user_id_obj)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Delete all user data
    user_db.delete(user_id_obj)

    # Delete user's entries and tags
    entries = changelog_db.find_by("user_id", user_id_obj)
    for entry in entries:
        changelog_db.delete(entry.id)

    tags = tag_db.find_by("user_id", user_id_obj)
    for tag in tags:
        tag_db.delete(tag.id)

    logger.warning(f"Admin {current_user.username} deleted user {user_id} and all their data")
    return None