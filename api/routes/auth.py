# File: api/routes/auth.py (update)
"""Authentication routes for Githappy API."""

from datetime import timedelta
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.auth import authenticate_user, create_token, get_current_user, TokenData
from core.logger import logger
from models import Role, Token, TokenRequest, User

router = APIRouter()


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

    # For demo purposes, allow requesting a specific role
    # In a real application, roles would be stored in the user database
    role = form_data.requested_role if form_data.requested_role else Role.USER

    token_data = {
        "user_id": str(user.id),
        "username": user.username,
        "role": role.value
    }

    access_token = create_token(token_data, expires_delta)

    logger.info(f"User {form_data.username} logged in with role {role}")
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=60,  # 1 minute in seconds
        user_id=str(user.id),
        username=user.username,
        role=role
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

from db import user_db

@router.get("/demo-token/{role}")
async def get_demo_token(role: Role) -> Token:
    """
    Get a demo token with a specific role.
    For demonstration purposes only.

    Parameters
    ----------
    role : Role
        Role to include in the token

    Returns
    -------
    Token
        JWT token with specified role
    """
    # Create a token for the demo user
    demo_users = user_db.find_by("username", "demo")
    if not demo_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo user not found",
        )

    demo_user = demo_users[0]

    # Token expires in 5 minutes for demo purposes
    expires_delta = timedelta(minutes=5)

    token_data = {
        "user_id": str(demo_user.id),
        "username": demo_user.username,
        "role": role.value
    }

    access_token = create_token(token_data, expires_delta)

    logger.info(f"Created demo token with role {role}")
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=300,  # 5 minutes in seconds
        user_id=str(demo_user.id),
        username=demo_user.username,
        role=role
    )