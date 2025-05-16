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
    Changelog entry model - similar to a Git commit.

    Attributes
    ----------
    id : UUID
        Unique identifier
    user_id : UUID
        Owner user ID
    content : str
        Entry content (may include prefixed gitmojis)
    entry_type : EntryType
        Type of entry (HIGHLIGHT, BUG, REFLECTION)
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
    created_at : datetime
        Creation timestamp
    updated_at : Optional[datetime]
        Last update timestamp
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    content: str
    entry_type: EntryType
    mood: Optional[Mood] = None
    week_number: int
    gitmojis: List[Gitmoji] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    tags: List[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def formatted_content(self) -> str:
        """
        Get formatted content with gitmojis.

        Returns
        -------
        str
            Formatted content string
        """
        gitmoji_prefix = " ".join([gitmoji.value for gitmoji in self.gitmojis])
        if gitmoji_prefix:
            return f"{gitmoji_prefix} {self.content}"
        return self.content


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

class ChangelogEntryCreate(BaseModel):
    """
    Model for creating a changelog entry.

    Only includes fields that need to be provided by the user.
    """
    content: str
    entry_type: EntryType
    mood: Optional[Mood] = None
    tags: List[UUID] = Field(default_factory=list)


class ChangelogEntryUpdate(BaseModel):
    """
    Model for updating a changelog entry.

    All fields are optional since users may want to update only specific fields.
    """
    content: Optional[str] = None
    entry_type: Optional[EntryType] = None
    mood: Optional[Mood] = None
    tags: Optional[List[UUID]] = None

class TagCreate(BaseModel):
    """
    Model for creating a tag.

    Only includes fields that need to be provided by the user.
    """
    name: str