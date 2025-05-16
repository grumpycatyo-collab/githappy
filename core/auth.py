"""Authentication utilities for ReleaseJoy API."""

from datetime import datetime, timedelta
from typing import Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from core.config import get_settings
from core.logger import logger
from db import user_db
from models import Role, User

settings = get_settings()
security = HTTPBearer()


class TokenData(BaseModel):
    """
    Token data model.

    Attributes
    ----------
    user_id : str
        User ID
    role : Role
        User role
    username : str
        Username
    """

    user_id: str
    role: Role = Role.USER
    username: str


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Parameters
    ----------
    password : str
        Password to hash

    Returns
    -------
    str
        Hashed password
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Parameters
    ----------
    plain_password : str
        Plain password
    hashed_password : str
        Hashed password

    Returns
    -------
    bool
        True if password matches hash
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.

    Parameters
    ----------
    username : str
        Username
    password : str
        Password

    Returns
    -------
    Optional[User]
        User if authenticated, None otherwise
    """
    users = user_db.find_by("username", username)
    if not users:
        return None
    user = users[0]
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token.

    Parameters
    ----------
    data : Dict
        Token data
    expires_delta : Optional[timedelta], optional
        Token expiration time, by default None (1 minute)

    Returns
    -------
    str
        JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=1)  # 1 minute expiration

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Get the current user from JWT token.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials, optional
        HTTP authorization credentials

    Returns
    -------
    TokenData
        Token data with user info

    Raises
    ------
    HTTPException
        401 error if token is invalid
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role", Role.USER.value)

        if user_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token content",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(
            user_id=user_id,
            role=Role(role),
            username=username
        )
        return token_data
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

