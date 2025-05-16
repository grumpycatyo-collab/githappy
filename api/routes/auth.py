"""Authentication routes for ReleaseJoy API."""

from datetime import timedelta
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.auth import authenticate_user, create_token, get_current_user, TokenData
from core.logger import logger
from models import User

router = APIRouter()


class TokenRequest(BaseModel):
    """
    Token request model.

    Attributes
    ----------
    username : str
        Username
    password : str
        Password
    """

    username: str
    password: str


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
    """

    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    username: str


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: TokenRequest) -> Token:
    """
    Authenticate user and return access token.

    Parameters
    ----------
    form_data : TokenRequest
        Authentication data

    Returns
    -------
    Token
        JWT token and user info

    Raises
    ------
    HTTPException
        401 error if authentication fails
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token expires in 1 minute for demo purposes
    expires_delta = timedelta(minutes=1)

    token_data = {
        "user_id": str(user.id),
        "username": user.username,
        "role": "WRITER"  # Default role for demo user
    }

    access_token = create_token(token_data, expires_delta)

    logger.info(f"User {form_data.username} logged in")
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=60,  # 1 minute in seconds
        user_id=str(user.id),
        username=user.username
    )


@router.get("/me")
async def read_users_me(current_user: TokenData = Depends(get_current_user)) -> Dict:
    """
    Get current user info.

    Parameters
    ----------
    current_user : TokenData
        Current authenticated user

    Returns
    -------
    Dict
        User info
    """
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role
    }