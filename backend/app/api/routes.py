"""
Core API routes (multi-user, auth-required).

Public:
  GET  /api/prices          — paginated price history (visible to all)
  GET  /api/prices/latest   — latest price record (visible to all)
  GET  /api/health          — health check

Authenticated:
  POST /api/prices/fetch    — manual trigger (any logged-in user)

  GET    /api/alerts        — current user's alert rules
  POST   /api/alerts        — create rule for current user
  PUT    /api/alerts/{id}   — update current user's rule
  DELETE /api/alerts/{id}   — delete current user's rule
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    AlertRuleCreate,
    AlertRuleOut,
    AlertRuleUpdate,
    GoldPriceOut,
    TriggerResponse,
)
from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import AlertRule, GoldPrice, User
from app.services.analyzer import evaluate_rules_for_user, save_snapshot
from app.services.scraper import fetch_gold_prices
from app.services.telegram_bot import send_alert_to_user, send_summary_to_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Health (public)
# ---------------------------------------------------------------------------

@router.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Prices (public — gold price data is not sensitive)
# ---------------------------------------------------------------------------

@router.get("/prices", response_model=list[GoldPriceOut], tags=["prices"])
def get_prices(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Paginated price history, newest first. Public."""
    return (
        db.query(GoldPrice)
        .order_by(GoldPrice.fetched_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/prices/latest", response_model=Optional[GoldPriceOut], tags=["prices"])
def get_latest_price(db: Session = Depends(get_db)):
    """Most recent price record. Public."""
    record = db.query(GoldPrice).order_by(GoldPrice.fetched_at.desc()).first()
    if not record:
        raise HTTPException(status_code=404, detail="No price records found yet.")
    return record


@router.post("/prices/fetch", response_model=TriggerResponse, tags=["prices"])
async def manual_fetch(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger a price fetch outside the schedule.
    Auth required — sends alerts only to the requesting user.
    """
    try:
        snapshot = await fetch_gold_prices()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    record = save_snapshot(db, snapshot)
    fired_rules = evaluate_rules_for_user(db, record, current_user)

    await send_summary_to_user(record, current_user)
    for rule in fired_rules:
        await send_alert_to_user(record, rule, current_user)

    return TriggerResponse(
        success=True,
        message=f"Price fetched. {len(fired_rules)} alert rule(s) triggered.",
        record=GoldPriceOut.model_validate(record),
    )


# ---------------------------------------------------------------------------
# Alert Rules (auth required — scoped to current user)
# ---------------------------------------------------------------------------

@router.get("/alerts", response_model=list[AlertRuleOut], tags=["alerts"])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(AlertRule)
        .filter(AlertRule.user_id == current_user.id)
        .order_by(AlertRule.created_at.desc())
        .all()
    )


@router.post("/alerts", response_model=AlertRuleOut, status_code=201, tags=["alerts"])
def create_alert(
    payload: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = AlertRule(**payload.model_dump(), user_id=current_user.id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/alerts/{rule_id}", response_model=AlertRuleOut, tags=["alerts"])
def update_alert(
    rule_id: int,
    payload: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = (
        db.query(AlertRule)
        .filter(AlertRule.id == rule_id, AlertRule.user_id == current_user.id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/alerts/{rule_id}", status_code=204, tags=["alerts"])
def delete_alert(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = (
        db.query(AlertRule)
        .filter(AlertRule.id == rule_id, AlertRule.user_id == current_user.id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    db.delete(rule)
    db.commit()
