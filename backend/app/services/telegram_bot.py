"""
Telegram notification service (multi-user).

Core function: send_message(chat_id, text)
  — sends to a specific user's chat by their personal chat_id.

Higher-level helpers build the formatted message and call send_message.
"""

import logging
import os
from typing import Optional

import httpx

from app.db.models import AlertRule, GoldPrice, User

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def _get_token() -> Optional[str]:
    return os.getenv("TELEGRAM_BOT_TOKEN")


def _format_change(abs_change: Optional[float], pct_change: Optional[float]) -> str:
    if abs_change is None or pct_change is None:
        return "N/A (first record)"
    arrow = "▲" if abs_change >= 0 else "▼"
    sign = "+" if abs_change >= 0 else ""
    return f"{arrow} {sign}{abs_change:,.2f} ETB  ({sign}{pct_change:.2f}%)"


def _fmt(price: Optional[float]) -> str:
    if price is None:
        return "N/A"
    return f"{price:,.2f} ETB/g"


# ---------------------------------------------------------------------------
# Low-level send
# ---------------------------------------------------------------------------

async def send_message(chat_id: str, text: str) -> bool:
    """
    Send a Markdown message to a specific Telegram chat_id.
    Returns True on success, False on failure (logs error).
    """
    token = _get_token()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set.")
        return False

    url = TELEGRAM_API_BASE.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Telegram API error for chat_id=%s: %s %s",
            chat_id, exc.response.status_code, exc.response.text,
        )
    except Exception as exc:
        logger.error("Failed to send Telegram message to chat_id=%s: %s", chat_id, exc)

    return False


# ---------------------------------------------------------------------------
# Message builders
# ---------------------------------------------------------------------------

def build_summary_message(record: GoldPrice, user: User) -> str:
    date_str = record.fetched_at.strftime("%B %d, %Y  %H:%M UTC")
    name = user.full_name or user.email.split("@")[0]

    lines = [
        f"🟡 *GOLD PRICE ALERT — ETHIOPIA*",
        f"👤 {name}",
        f"📅 {date_str}",
        "",
        f"🔸 24K: `{_fmt(record.price_24k)}`",
        f"🔸 22K: `{_fmt(record.price_22k)}`",
        f"🔸 18K: `{_fmt(record.price_18k)}`",
        "",
        f"📊 Change from previous: `{_format_change(record.change_24k_abs, record.change_24k_pct)}`",
        "",
        f"ℹ️ _{record.source_label}_",
    ]
    return "\n".join(lines)


def build_alert_message(record: GoldPrice, rule: AlertRule, user: User) -> str:
    current_price = {
        "24K": record.price_24k,
        "22K": record.price_22k,
        "18K": record.price_18k,
    }.get(rule.purity, record.price_24k)

    rule_descriptions = {
        "above": f"{rule.purity} price rose *above* {rule.threshold:,.2f} ETB/g",
        "below": f"{rule.purity} price dropped *below* {rule.threshold:,.2f} ETB/g",
        "pct_change": f"Price moved by ≥ {rule.threshold:.1f}% since last check",
    }
    description = rule_descriptions.get(rule.rule_type, rule.rule_type)
    label_part = f" — _{rule.label}_" if rule.label else ""

    lines = [
        "🚨 *GOLD PRICE ALERT TRIGGERED*",
        "",
        f"📌 {description}{label_part}",
        f"💰 Current {rule.purity}: `{_fmt(current_price)}`",
        f"📊 Change: `{_format_change(record.change_24k_abs, record.change_24k_pct)}`",
        f"📅 {record.fetched_at.strftime('%B %d, %Y  %H:%M UTC')}",
        "",
        f"ℹ️ _{record.source_label}_",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dispatch helpers (used by scheduler)
# ---------------------------------------------------------------------------

async def send_summary_to_user(record: GoldPrice, user: User) -> bool:
    """Send periodic price summary to one user."""
    if not user.telegram_chat_id:
        return False
    return await send_message(user.telegram_chat_id, build_summary_message(record, user))


async def send_alert_to_user(record: GoldPrice, rule: AlertRule, user: User) -> bool:
    """Send a triggered-alert message to one user."""
    if not user.telegram_chat_id:
        return False
    return await send_message(user.telegram_chat_id, build_alert_message(record, rule, user))
