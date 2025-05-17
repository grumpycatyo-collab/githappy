"""Tag routes for GitHappy API."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.auth import TokenData, get_current_user, role_required
from core.logger import logger
from core.db import tag_db
from models import Tag, TagCreate, Role, PyObjectId

router = APIRouter()


@router.get("/", response_model=List[Tag])
async def get_tags(
        skip: int = Query(0, description="Number of tags to skip for pagination"),
        limit: int = Query(50, description="Number of tags to return per page"),
        current_user: TokenData = Depends(get_current_user),
):
    """
    Get all tags for the current user.

    Parameters
    ----------
    skip : int
        Number of tags to skip
    limit : int
        Maximum number of tags to return
    current_user : TokenData
        Current authenticated user

    Returns
    -------
    List[Tag]
        List of tags
    """
    # Get all tags for the user
    user_tags = tag_db.find_by("user_id", PyObjectId(current_user.user_id))

    # Apply pagination
    paginated_tags = user_tags[skip : skip + limit]

    logger.info(f"Retrieved {len(paginated_tags)} tags for user {current_user.username}")
    return paginated_tags


@router.post("/", response_model=Tag, status_code=status.HTTP_201_CREATED)
async def create_tag(tag_data: TagCreate, current_user: TokenData = Depends(role_required([Role.USER, Role.ADMIN]))):
    """
    Create a new tag.

    Parameters
    ----------
    tag_data : TagCreate
        Data for the new tag
    current_user : TokenData
        Current authenticated user

    Returns
    -------
    Tag
        Created tag

    Raises
    ------
    HTTPException
        403 if user doesn't have permission
    """
    # Check if user has write permission
    print(current_user)
    if current_user.role == Role.VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create tags",
        )

    # Create a new Tag from the provided data
    tag = Tag(
        name=tag_data.name,
        user_id=PyObjectId(current_user.user_id)
    )

    # Create the tag
    created_tag = tag_db.create(tag)
    logger.info(f"Created tag with ID {created_tag.id}")

    return created_tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, current_user: TokenData = Depends(role_required([Role.USER, Role.ADMIN]))):
    """
    Delete a tag.

    Parameters
    ----------
    tag_id : str
        Tag ID
    current_user : TokenData
        Current authenticated user

    Raises
    ------
    HTTPException
        404 if tag not found
        403 if user doesn't have permission
    """
    # Check if tag exists
    tag_id_obj = PyObjectId(tag_id)
    existing_tag = tag_db.get(tag_id_obj)
    if not existing_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    # Only admin or the owner can delete tags
    if current_user.role != Role.ADMIN and str(existing_tag.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this tag",
        )

    # Delete the tag
    success = tag_db.delete(tag_id_obj)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    logger.info(f"Deleted tag with ID {tag_id}")
    return None