"""
Authentication endpoints.

POST /api/auth/register  — create account
POST /api/auth/login     — get JWT token (OAuth2 password flow)
GET  /api/auth/me        — current user profile
PUT  /api/auth/me        — update profile / notification interval
GET  /api/auth/telegram/link    — generate / return Telegram deep-link
DELETE /api/auth/telegram/unlink — disconnect Telegram
"""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User, generate_telegram_link_token

router = APIRouter(prefix="/auth", tags=["auth"])

BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "YourGoldWatcherBot")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = Field(default=None, max_length=200)

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    telegram_chat_id: Optional[str]
    telegram_connected_at: Optional[datetime]
    notify_interval_hours: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=200)
    notify_interval_hours: Optional[int] = Field(default=None, ge=1, le=8760)


class TelegramLinkResponse(BaseModel):
    link: str          # full t.me deep-link the user should click
    token: str         # the raw token (useful for QR codes etc.)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Standard OAuth2 password flow. `username` field = email."""
    user = db.query(User).filter(User.email == form.username.strip().lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled.")
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.notify_interval_hours is not None:
        current_user.notify_interval_hours = payload.notify_interval_hours
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/telegram/link", response_model=TelegramLinkResponse)
def get_telegram_link(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate (or return existing) Telegram deep-link.
    User clicks the link → opens Telegram → sends /start <token> to the bot
    → bot registers the chat_id against this user account.
    """
    if not current_user.telegram_link_token:
        current_user.telegram_link_token = generate_telegram_link_token()
        db.commit()
        db.refresh(current_user)

    token = current_user.telegram_link_token
    link = f"https://t.me/{BOT_USERNAME}?start={token}"
    return TelegramLinkResponse(link=link, token=token)


@router.delete("/telegram/unlink", status_code=204)
def unlink_telegram(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disconnect Telegram from this account."""
    current_user.telegram_chat_id = None
    current_user.telegram_link_token = None
    current_user.telegram_connected_at = None
    db.commit()
