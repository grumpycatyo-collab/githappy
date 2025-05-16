"""Changelog routes for Githappy API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.auth import TokenData, get_current_user
from core.logger import logger
from core.sentiment import enrich_entry

from db import changelog_db, tag_db
from models import ChangelogEntry, Role

router = APIRouter()


@router.get("/", response_model=list[ChangelogEntry])
async def get_changelog_entries(
        skip: int = Query(0, description="Number of entries to skip for pagination"),
        limit: int = Query(10, description="Number of entries to return per page"),
        current_user: TokenData = Depends(get_current_user),
):
    """
    Get all changelog entries for the current user.

    Parameters
    ----------
    skip
        Number of entries to skip
    limit
        Maximum number of entries to return
    current_user
        Current authenticated user

    Returns
    -------
    list[ChangelogEntry]
        list of changelog entries
    """
    user_entries = changelog_db.find_by("user_id", UUID(current_user.user_id))

    paginated_entries = user_entries[skip : skip + limit]

    logger.info(f"Retrieved {len(paginated_entries)} changelog entries for user {current_user.username}")
    return paginated_entries


@router.get("/{entry_id}", response_model=ChangelogEntry)
async def get_changelog_entry(
        entry_id: UUID, current_user: TokenData = Depends(get_current_user)
):
    """
    Get a specific changelog entry.

    Parameters
    ----------
    entry_id
        Entry ID
    current_user
        Current authenticated user

    Returns
    -------
    ChangelogEntry
        Changelog entry

    Raises
    ------
    HTTPException
        404 if entry not found
        403 if user doesn't have permission
    """
    entry = changelog_db.get(entry_id)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    if str(entry.user_id) != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this entry",
        )

    return entry


@router.post("/", response_model=ChangelogEntry, status_code=status.HTTP_201_CREATED)
async def create_changelog_entry(
        entry: ChangelogEntry, current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new changelog entry.

    Parameters
    ----------
    entry
        Entry to create
    current_user
        Current authenticated user

    Returns
    -------
    ChangelogEntry
        Created entry

    Raises
    ------
    HTTPException
        403 if user doesn't have permission
    """
    if current_user.role == Role.VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create entries",
        )

    entry.user_id = UUID(current_user.user_id)
    entry = enrich_entry(entry)
    created_entry = changelog_db.create(entry)
    logger.info(f"Created changelog entry with ID {created_entry.id}")

    return created_entry


@router.put("/{entry_id}", response_model=ChangelogEntry)
async def update_changelog_entry(
        entry_id: UUID,
        updated_entry: ChangelogEntry,
        current_user: TokenData = Depends(get_current_user),
):
    """
    Update a changelog entry.

    Parameters
    ----------
    entry_id
        Entry ID
    updated_entry
        Updated entry
    current_user
        Current authenticated user

    Returns
    -------
    ChangelogEntry
        Updated entry

    Raises
    ------
    HTTPException
        404 if entry not found
        403 if user doesn't have permission
    """
    existing_entry = changelog_db.get(entry_id)
    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    if str(existing_entry.user_id) != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this entry",
        )

    if current_user.role == Role.VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update entries",
        )

    updated_entry.id = entry_id
    updated_entry.user_id = existing_entry.user_id

    updated_entry = enrich_entry(updated_entry)
    result = changelog_db.update(entry_id, updated_entry)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    logger.info(f"Updated changelog entry with ID {entry_id}")
    return result


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_changelog_entry(
        entry_id: UUID, current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a changelog entry.

    Parameters
    ----------
    entry_id
        Entry ID
    current_user
        Current authenticated user

    Raises
    ------
    HTTPException
        404 if entry not found
        403 if user doesn't have permission
    """
    existing_entry = changelog_db.get(entry_id)
    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    if current_user.role != Role.ADMIN and str(existing_entry.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this entry",
        )

    success = changelog_db.delete(entry_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    logger.info(f"Deleted changelog entry with ID {entry_id}")
    return None