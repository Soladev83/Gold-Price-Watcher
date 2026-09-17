"""
Price Analyzer (multi-user).

1. save_snapshot()         — persist a GoldPriceSnapshot, calculate change vs previous.
2. evaluate_rules_for_user() — check one user's active alert rules against latest price.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import AlertRule, GoldPrice, User
from app.services.scraper import GoldPriceSnapshot

logger = logging.getLogger(__name__)


def _get_price_for_purity(record: GoldPrice, purity: str) -> Optional[float]:
    return {"24K": record.price_24k, "22K": record.price_22k, "18K": record.price_18k}.get(
        purity.upper()
    )


def _pct_change(new: float, old: float) -> Optional[float]:
    if old and old != 0:
        return round((new - old) / old * 100, 4)
    return None


# ---------------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------------

def save_snapshot(db: Session, snapshot: GoldPriceSnapshot) -> GoldPrice:
    previous: Optional[GoldPrice] = (
        db.query(GoldPrice).order_by(GoldPrice.fetched_at.desc()).first()
    )

    change_abs = change_pct = None
    if previous:
        change_abs = round(snapshot.price_24k - previous.price_24k, 2)
        change_pct = _pct_change(snapshot.price_24k, previous.price_24k)

    record = GoldPrice(
        fetched_at=snapshot.fetched_at,
        price_24k=snapshot.price_24k,
        price_22k=snapshot.price_22k,
        price_18k=snapshot.price_18k,
        change_24k_abs=change_abs,
        change_24k_pct=change_pct,
        source_url=snapshot.source_url,
        source_label=snapshot.source_label,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        "Saved price: 24K=%.2f ETB | Δ=%.2f ETB (%.4f%%)",
        record.price_24k, change_abs or 0, change_pct or 0,
    )
    return record


# ---------------------------------------------------------------------------
# Per-user alert rule evaluation
# ---------------------------------------------------------------------------

def evaluate_rules_for_user(
    db: Session, record: GoldPrice, user: User
) -> list[AlertRule]:
    """
    Evaluate the active alert rules belonging to `user` against `record`.
    Returns the list of rules that fired; updates their last_triggered metadata.
    """
    active_rules: list[AlertRule] = (
        db.query(AlertRule)
        .filter(AlertRule.user_id == user.id, AlertRule.is_active == True)  # noqa: E712
        .all()
    )

    fired: list[AlertRule] = []

    for rule in active_rules:
        current_price = _get_price_for_purity(record, rule.purity)
        if current_price is None:
            continue

        triggered = False

        if rule.rule_type == "above":
            triggered = current_price > rule.threshold
        elif rule.rule_type == "below":
            triggered = current_price < rule.threshold
        elif rule.rule_type == "pct_change":
            if record.change_24k_pct is not None:
                triggered = abs(record.change_24k_pct) >= rule.threshold

        if triggered:
            # Deduplicate: skip if price hasn't moved since last fire
            if rule.last_triggered_price == current_price:
                continue
            fired.append(rule)
            rule.last_triggered_at = datetime.now(timezone.utc)
            rule.last_triggered_price = current_price
            logger.info(
                "Alert fired: user=%d rule=%d type=%s price=%.2f",
                user.id, rule.id, rule.rule_type, current_price,
            )

    if fired:
        db.commit()

    return fired
