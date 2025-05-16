"""Authentication routes for GitHappy API."""

from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import authenticate_user, create_token, get_current_user, TokenData, get_password_hash
from core.logger import logger
from models import Role, Token, TokenRequest, User, UserCreate

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

    token_data = {
        "user_id": str(user.id),
        "username": user.username,
        "role": Role.USER
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

@router.post("/issue_cli_token", response_model=Token)
async def issue_cli_token(form_data: TokenRequest) -> Token:
    """
    Issue a long-term (24 days) CLI Bearer token for the user.

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


    expires_delta = timedelta(days=24)  # Long-term token for CLI usage

    role = Role.USER

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
        expires_in=60*60*24,  # 24 days in seconds
        user_id=str(user.id),
        username=user.username,
        role=role
    )

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    # Check if username already exists
    existing_users = user_db.find_by("username", user_data.username)
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    hashed_password = get_password_hash(user_data.password)
    user = User(username=user_data.username, password_hash=hashed_password)
    created_user = user_db.create(user)

    return User(id=created_user.id, username=created_user.username, password_hash="********")  # Don't return the password hash