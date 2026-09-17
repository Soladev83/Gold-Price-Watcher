"""
Telegram Bot webhook endpoint.

Telegram sends a POST to /api/telegram/webhook every time a user
messages the bot. We handle two cases:

  1. /start <token>  — user clicked the deep-link from the dashboard.
                       Match the token to a User, save their chat_id,
                       and send a welcome message.

  2. /start (no token) — user opened the bot directly without a link.
                         Send instructions.

Security: Telegram signs every update with a secret token passed as the
X-Telegram-Bot-Api-Secret-Token header. We verify it before processing.
Set TELEGRAM_WEBHOOK_SECRET in your environment to the same value you
pass when registering the webhook with setWebhook.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.services.telegram_bot import send_message

router = APIRouter(prefix="/telegram", tags=["telegram"])
logger = logging.getLogger(__name__)

WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "YourGoldWatcherBot")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_start_token(text: Optional[str]) -> Optional[str]:
    """
    Given a message text like '/start abc123' or '/start', return the
    token part or None.
    """
    if not text:
        return None
    parts = text.strip().split()
    if len(parts) >= 2 and parts[0] == "/start":
        return parts[1]
    return None


async def _welcome_message(chat_id: str, user: User) -> None:
    name = user.full_name or user.email.split("@")[0]
    text = (
        f"✅ *Telegram connected successfully!*\n\n"
        f"Welcome, {name}. Your account is now linked.\n\n"
        f"You will receive:\n"
        f"• 📊 Gold price summaries every *{user.notify_interval_hours} hours*\n"
        f"• 🚨 Instant alerts when your custom rules trigger\n\n"
        f"_Prices are reference rates — not dealer quotes. "
        f"Verify local prices before any transaction._"
    )
    await send_message(chat_id, text)


async def _instructions_message(chat_id: str) -> None:
    text = (
        "👋 *Welcome to Gold Price Watcher Ethiopia!*\n\n"
        "To connect your Telegram to your account:\n\n"
        "1. Visit the dashboard and register/log in\n"
        f"2. Go to *Settings → Connect Telegram*\n"
        "3. Click the generated link to activate alerts\n\n"
        "_This bot only works when linked to a registered account._"
    )
    await send_message(chat_id, text)


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
):
    # Verify the webhook secret to ensure the request is from Telegram
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook secret.",
        )

    body: dict[str, Any] = await request.json()
    message = body.get("message") or body.get("edited_message")
    if not message:
        # Telegram may send other update types (callback_query etc.) — ignore them
        return {"ok": True}

    chat_id = str(message.get("chat", {}).get("id", ""))
    text: Optional[str] = message.get("text")

    if not chat_id:
        return {"ok": True}

    token = _extract_start_token(text)

    if not token:
        # No token — send usage instructions
        await _instructions_message(chat_id)
        return {"ok": True}

    # Look up the user by their link token
    user: Optional[User] = (
        db.query(User).filter(User.telegram_link_token == token).first()
    )

    if not user:
        await send_message(
            chat_id,
            "❌ This link is invalid or has already been used.\n"
            "Please generate a new link from the dashboard.",
        )
        return {"ok": True}

    if user.telegram_chat_id and user.telegram_chat_id != chat_id:
        # Already connected to a different Telegram account
        await send_message(
            chat_id,
            "⚠️ This account is already connected to a different Telegram chat.\n"
            "Unlink it from the dashboard first.",
        )
        return {"ok": True}

    # Save the chat_id — clear the one-use link token
    user.telegram_chat_id = chat_id
    user.telegram_link_token = None
    user.telegram_connected_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    logger.info("User %d connected Telegram chat_id=%s", user.id, chat_id)
    await _welcome_message(chat_id, user)

    return {"ok": True}
