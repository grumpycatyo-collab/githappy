"""Core data models for GitHappy API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4
from bson import ObjectId

from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(cls.validate),
            json_schema=core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def validate(cls, v, _info=None):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler: GetJsonSchemaHandler):
        schema = handler(core_schema)
        schema.update(type="string")
        return schema


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
    id : PyObjectId
        Unique identifier
    username : str
        Username
    password_hash : str
        Hashed password
    """

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    password_hash: str


class Tag(BaseModel):
    """
    Tag model.

    Attributes
    ----------
    id : PyObjectId
        Unique identifier
    name : str
        Tag name
    user_id : PyObjectId
        Owner user ID
    """

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    user_id: PyObjectId


class ChangelogEntry(BaseModel):
    """
    Changelog entry model - similar to a Git commit.

    Attributes
    ----------
    id : PyObjectId
        Unique identifier
    user_id : PyObjectId
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
    tags : List[PyObjectId]
        List of tag IDs
    created_at : datetime
        Creation timestamp
    updated_at : Optional[datetime]
        Last update timestamp
    """

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    content: str
    entry_type: EntryType
    mood: Optional[Mood] = None
    week_number: int
    gitmojis: List[Gitmoji] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    tags: List[PyObjectId] = Field(default_factory=list)
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
    tags: List[PyObjectId] = Field(default_factory=list)


class ChangelogEntryUpdate(BaseModel):
    """
    Model for updating a changelog entry.

    All fields are optional since users may want to update only specific fields.
    """
    content: Optional[str] = None
    entry_type: Optional[EntryType] = None
    mood: Optional[Mood] = None
    tags: Optional[List[PyObjectId]] = None

class TagCreate(BaseModel):
    """
    Model for creating a tag.

    Only includes fields that need to be provided by the user.
    """
    name: str

class UserCreate(BaseModel):
    username: str
    password: str