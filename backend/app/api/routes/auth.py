from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user account with hashed password and assigned role.
    Role defaults to 'tourist'; administrative role self-escalation is blocked.
    """
    # Enforce role safety
    role = user_in.role or "tourist"
    if role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot register as an administrator"
        )
    if role not in ("tourist", "business"):
        role = "tourist"

    # Enforce unique email
    existing_user = db.scalar(select(User).where(User.email == user_in.email.lower().strip()))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # Hash password before storage
    hashed_pwd = get_password_hash(user_in.password)

    user = User(
        email=user_in.email.lower().strip(),
        hashed_password=hashed_pwd,
        full_name=user_in.full_name.strip(),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate user with email and password, returning a JWT access token.
    """
    user = db.scalar(select(User).where(User.email == login_data.email.lower().strip()))
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(
        data=token_payload,
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve profile details for the currently authenticated user.
    """
    return current_user
