# File: models.py (update)
"""Core data models for Githappy API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Role(str, Enum):
    """User role enum."""

    ADMIN = "ADMIN"  # Admin can do everything
    USER = "WRITER"  # Regular user can create and edit entries
    VISITOR = "VISITOR"  # Visitor can only view entries


class EntryType(str, Enum):
    """Changelog entry type."""

    HIGHLIGHT = "HIGHLIGHT"
    BUG = "BUG"
    REFLECTION = "REFLECTION"


class Mood(str, Enum):
    """Mood enum for entries."""

    HAPPY = "HAPPY"
    NEUTRAL = "NEUTRAL"
    SAD = "SAD"
    EXCITED = "EXCITED"
    STRESSED = "STRESSED"
    TIRED = "TIRED"


class Gitmoji(str, Enum):
    """Gitmoji enum."""

    SPARKLES = "✨"  # New feature/idea
    BUG = "🐛"  # Bug fix
    BOOM = "💥"  # Breaking change
    ROCKET = "🚀"  # Performance improvement
    MEMO = "📝"  # Documentation
    BULB = "💡"  # New idea
    HEART = "❤️"  # Gratitude
    ZAP = "⚡"  # Energy
    TADA = "🎉"  # Celebration
    FIRE = "🔥"  # Removal
    LOCK = "🔒"  # Security
    CONSTRUCTION = "🚧"  # Work in progress
    RECYCLE = "♻️"  # Refactor
    WRENCH = "🔧"  # Configuration
    BRAIN = "🧠"  # Mental health
    EYES = "👀"  # Review


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
    entry_type : EntryType
        Type of entry
    content : str
        Entry content
    mood : Optional[Mood]
        User's mood
    week_number : int
        Week number
    gitmojis : List[Gitmoji]
        List of gitmojis assigned to the entry
    sentiment_score : Optional[float]
        Sentiment analysis score
    tags : List[UUID]
        List of tag IDs
    is_public : bool
        Whether the entry is public
    created_at : datetime
        Creation timestamp
    updated_at : Optional[datetime]
        Last update timestamp
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str
    entry_type: EntryType
    content: str
    mood: Optional[Mood] = None
    week_number: int
    gitmojis: list[Gitmoji] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    tags: List[UUID] = Field(default_factory=list)
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class TokenRequest(BaseModel):
    """
    Token request model.

    Attributes
    ----------
    username : str
        Username
    password : str
        Password
    requested_role : Optional[Role]
        Requested role (only for demo purposes)
    """

    username: str
    password: str
    requested_role: Optional[Role] = None


class Token(BaseModel):
    """
    Token response model.

    Attributes
    ----------
    access_token : str
        JWT access token
    token_type : str
        Token type (always "bearer")
    expires_in : int
        Token expiration time in seconds
    user_id : str
        User ID
    username : str
        Username
    role : Role
        User role
    """

    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    username: str
    role: Role