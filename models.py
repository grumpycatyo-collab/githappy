"""Core data models for ReleaseJoy API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Role(str, Enum):
    """User role enum."""

    USER = "WRITER"  # Regular user can create and edit entries
    ADMIN = "ADMIN" # Admin can delete entries
    VISITOR = "VISITOR" # Visitor can only view entries


class User(BaseModel):
    """
    User model.

    Attributes
    ----------
    id : UUID
        Unique identifier
    username : str
        Username
    password_hash : str
        Hashed password
    """

    id: UUID = Field(default_factory=uuid4)
    username: str
    password_hash: str


class Tag(BaseModel):
    """
    Tag model.

    Attributes
    ----------
    id : UUID
        Unique identifier
    name : str
        Tag name
    user_id : UUID
        Owner user ID
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    user_id: UUID


class ChangelogEntry(BaseModel):
    """
    Changelog entry model.

    Attributes
    ----------
    id : UUID
        Unique identifier
    user_id : UUID
        Owner user ID
    title : str
        Entry title
    highlights : str
        Highlights of the week
    bugs : str
        Bugs or issues encountered
    reflections : str
        Reflections on the week
    week_number : int
        Week number
    tags : List[UUID]
        List of tag IDs
    is_public : bool
        Whether the entry is public
    created_at : datetime
        Creation timestamp
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str
    highlights: str
    bugs: str
    reflections: str
    week_number: int
    tags: List[UUID] = Field(default_factory=list)
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.now)