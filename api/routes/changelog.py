"""Changelog routes for GitHappy API."""


from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.auth import TokenData, get_current_user
from core.logger import logger
from core.sentiment import enrich_entry

from core.db import changelog_db
from models import ChangelogEntry, ChangelogEntryCreate, ChangelogEntryUpdate, Role, PyObjectId
from datetime import datetime
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
    user_entries = changelog_db.find_by("user_id", PyObjectId(current_user.user_id))

    paginated_entries = user_entries[skip : skip + limit]

    logger.info(f"Retrieved {len(paginated_entries)} changelog entries for user {current_user.username}")
    return paginated_entries


@router.get("/{entry_id}", response_model=ChangelogEntry)
async def get_changelog_entry(
        entry_id: str, current_user: TokenData = Depends(get_current_user)
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
    entry_id_obj = PyObjectId(entry_id)
    entry = changelog_db.get(entry_id_obj)

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
        entry_data: ChangelogEntryCreate, current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new changelog entry.

    Parameters
    ----------
    entry_data : ChangelogEntryCreate
        Data for the new entry
    current_user : TokenData
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
    # Check if user has write permission
    if current_user.role == Role.VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create entries",
        )

    # Create a new ChangelogEntry from the provided data
    entry = ChangelogEntry(
        user_id=PyObjectId(current_user.user_id),
        content=entry_data.content,
        entry_type=entry_data.entry_type,
        mood=entry_data.mood,
        tags=entry_data.tags,
        week_number=datetime.now().isocalendar()[1],  # Current ISO week number
    )

    entry = enrich_entry(entry)

    # Create the entry
    created_entry = changelog_db.create(entry)
    logger.info(f"Created changelog entry with ID {created_entry.id}")

    return created_entry


@router.put("/{entry_id}", response_model=ChangelogEntry)
async def update_changelog_entry(
        entry_id: str,
        entry_data: ChangelogEntryUpdate,
        current_user: TokenData = Depends(get_current_user),
):
    """
    Update a changelog entry.

    Parameters
    ----------
    entry_id : str
        Entry ID
    entry_data : ChangelogEntryUpdate
        Updated data
    current_user : TokenData
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
    entry_id_obj = PyObjectId(entry_id)
    # Check if entry exists
    existing_entry = changelog_db.get(entry_id_obj)
    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    # Check if the entry belongs to the user or user is admin
    if str(existing_entry.user_id) != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this entry",
        )

    # Check if user has write permission
    if current_user.role == Role.VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update entries",
        )

    # Update the entry with the provided data, keeping existing values where no update is provided
    updated_data = existing_entry.model_dump()

    # Update only the fields that are provided
    update_data = {k: v for k, v in entry_data.model_dump(exclude_unset=True).items() if v is not None}
    updated_data.update(update_data)

    # Create a new entry with the updated data
    updated_entry = ChangelogEntry(**updated_data)
    updated_entry.updated_at = datetime.now()

    # Re-analyze sentiment and gitmojis if content was updated
    if "content" in update_data:
        updated_entry = enrich_entry(updated_entry)

    # Update the entry
    result = changelog_db.update(entry_id_obj, updated_entry)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    logger.info(f"Updated changelog entry with ID {entry_id}")
    return result


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_changelog_entry(
        entry_id: str, current_user: TokenData = Depends(get_current_user)
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
    entry_id_obj = PyObjectId(entry_id)
    existing_entry = changelog_db.get(entry_id_obj)
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

    success = changelog_db.delete(entry_id_obj)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    logger.info(f"Deleted changelog entry with ID {entry_id}")
    return None

@router.get("/week/{week_number}", response_model=list[ChangelogEntry])
async def get_entries_by_week(
        week_number: int,
        year: int = Query(datetime.now().year, description="Year for the week number"),
        current_user: TokenData = Depends(get_current_user),
):
    """
    Get all changelog entries for a specific week.

    Parameters
    ----------
    week_number : int
        Week number
    year : int
        Year for the week number
    current_user : TokenData
        Current authenticated user

    Returns
    -------
    List[ChangelogEntry]
        List of changelog entries for the week
    """
    # Get all entries for the user
    user_entries = changelog_db.find_by("user_id", PyObjectId(current_user.user_id))

    # Filter entries by week number
    week_entries = [entry for entry in user_entries if entry.week_number == week_number]

    logger.info(f"Retrieved {len(week_entries)} changelog entries for week {week_number}")
    return week_entries

@router.get("/{entry_id}/formatted", response_model=dict)
async def get_formatted_entry(
        entry_id: str, current_user: TokenData = Depends(get_current_user)
):
    """
    Get formatted content of an entry.

    Parameters
    ----------
    entry_id : str
        Entry ID
    current_user : TokenData
        Current authenticated user

    Returns
    -------
    dict
        Formatted entry content

    Raises
    ------
    HTTPException
        404 if entry not found
        403 if user doesn't have permission
    """
    entry_id_obj = PyObjectId(entry_id)
    entry = changelog_db.get(entry_id_obj)

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

    return {
        "id": str(entry.id),
        "formatted_content": entry.formatted_content(),
        "entry_type": entry.entry_type,
        "gitmojis": [gitmoji.value for gitmoji in entry.gitmojis],
        "sentiment_score": entry.sentiment_score,
        "created_at": entry.created_at
    }