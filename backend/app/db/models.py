"""
SQLAlchemy ORM models for Gold Price Watcher (multi-user).
"""

import secrets
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    """
    Registered user of the service.
    Telegram connection is optional — users can browse the dashboard without it,
    but won't receive Telegram alerts until they connect.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    email = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Telegram connection
    # telegram_chat_id is populated when the user clicks the connect link
    # and sends /start <token> to the bot.
    telegram_chat_id = Column(String(32), nullable=True, unique=True, index=True)
    telegram_link_token = Column(String(64), nullable=True, unique=True, index=True)
    telegram_connected_at = Column(DateTime(timezone=True), nullable=True)

    # Notification schedule — how often to receive the periodic summary.
    # Stored in hours; default 48 (every 2 days).
    notify_interval_hours = Column(Integer, nullable=False, default=48)

    # Track when the last periodic summary was sent to this user.
    last_notified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    alert_rules = relationship("AlertRule", back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Gold Price (shared / global — one record per fetch, not per user)
# ---------------------------------------------------------------------------

class GoldPrice(Base):
    """
    One row per scheduled price fetch. Shared across all users.
    """

    __tablename__ = "gold_prices"

    id = Column(Integer, primary_key=True, index=True)
    fetched_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    price_24k = Column(Float, nullable=False)
    price_22k = Column(Float, nullable=True)
    price_18k = Column(Float, nullable=True)

    change_24k_abs = Column(Float, nullable=True)
    change_24k_pct = Column(Float, nullable=True)

    source_url = Column(String(512), nullable=False)
    source_label = Column(Text, nullable=False)


# ---------------------------------------------------------------------------
# Alert Rule (per user)
# ---------------------------------------------------------------------------

class AlertRule(Base):
    """
    User-defined alert condition. Belongs to one user.
    Evaluated after every price fetch; fires a Telegram message to that user.

    rule_type values:
      "above"       — trigger when purity price > threshold
      "below"       — trigger when purity price < threshold
      "pct_change"  — trigger when |change_pct| >= threshold
    """

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="alert_rules")

    rule_type = Column(String(20), nullable=False)   # above | below | pct_change
    threshold = Column(Float, nullable=False)
    purity = Column(String(4), nullable=False, default="24K")

    is_active = Column(Boolean, nullable=False, default=True)
    label = Column(String(200), nullable=True)

    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_triggered_price = Column(Float, nullable=True)


# ---------------------------------------------------------------------------
# Helper: generate a Telegram link token
# ---------------------------------------------------------------------------

def generate_telegram_link_token() -> str:
    """Cryptographically random token used in the /start deep-link."""
    return secrets.token_urlsafe(32)
