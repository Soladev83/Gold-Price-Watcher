"""
Scheduled jobs for Gold Price Watcher (multi-user).

Single job: fetch_and_notify
  Runs every FETCH_INTERVAL_HOURS (default 48 — every 2 days).

  Steps:
    1. Fetch latest gold prices from the scraper.
    2. Save snapshot to the shared GoldPrice table.
    3. For every user with a connected Telegram:
         a. If their personal notify_interval_hours has elapsed since
            last_notified_at → send periodic summary.
         b. Evaluate their alert rules → send alert messages for any that fire.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.database import SessionLocal
from app.db.models import GoldPrice, User
from app.services.analyzer import evaluate_rules_for_user, save_snapshot
from app.services.scraper import fetch_gold_prices
from app.services.telegram_bot import send_alert_to_user, send_summary_to_user

logger = logging.getLogger(__name__)

# How often the job itself runs (controls price data resolution).
# Can be lower than any user's notify_interval so we always have fresh data.
# Default: every 12 hours — summaries still go out per-user at their own interval.
FETCH_INTERVAL_HOURS: int = int(os.getenv("FETCH_INTERVAL_HOURS", "12"))


# ---------------------------------------------------------------------------
# Core job
# ---------------------------------------------------------------------------

async def fetch_and_notify() -> None:
    logger.info("Scheduled job: fetch_and_notify starting.")

    # 1. Fetch prices
    try:
        snapshot = await fetch_gold_prices()
    except RuntimeError as exc:
        logger.error("Price fetch failed: %s", exc)
        return

    db = SessionLocal()
    try:
        # 2. Save snapshot
        record: GoldPrice = save_snapshot(db, snapshot)
        now = datetime.now(timezone.utc)

        # 3. Process each connected user
        users: list[User] = (
            db.query(User)
            .filter(User.is_active == True, User.telegram_chat_id != None)  # noqa: E711,E712
            .all()
        )

        logger.info("Processing %d connected user(s).", len(users))

        for user in users:
            # ── Periodic summary ────────────────────────────────────────────
            # Send summary if the user's interval has elapsed.
            interval = timedelta(hours=user.notify_interval_hours)
            should_summarise = (
                user.last_notified_at is None
                or (now - user.last_notified_at) >= interval
            )

            if should_summarise:
                sent = await send_summary_to_user(record, user)
                if sent:
                    user.last_notified_at = now
                    db.commit()
                    logger.info(
                        "Summary sent to user=%d (interval=%dh).",
                        user.id, user.notify_interval_hours,
                    )

            # ── Per-user alert rules ─────────────────────────────────────────
            fired_rules = evaluate_rules_for_user(db, record, user)
            for rule in fired_rules:
                await send_alert_to_user(record, rule, user)

    except Exception as exc:
        logger.exception("Error in fetch_and_notify: %s", exc)
    finally:
        db.close()

    logger.info("Scheduled job: fetch_and_notify complete.")


# ---------------------------------------------------------------------------
# Scheduler factory
# ---------------------------------------------------------------------------

def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        fetch_and_notify,
        trigger=IntervalTrigger(hours=FETCH_INTERVAL_HOURS),
        id="fetch_and_notify",
        name=f"Fetch prices every {FETCH_INTERVAL_HOURS}h & notify users",
        replace_existing=True,
        max_instances=1,
    )
    logger.info(
        "Scheduler configured: fetch_and_notify every %dh. "
        "User summaries sent per their own notify_interval_hours (default 48h).",
        FETCH_INTERVAL_HOURS,
    )
    return scheduler
