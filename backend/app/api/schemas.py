"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Gold Price
# ---------------------------------------------------------------------------

class GoldPriceOut(BaseModel):
    id: int
    fetched_at: datetime
    price_24k: float
    price_22k: Optional[float]
    price_18k: Optional[float]
    change_24k_abs: Optional[float]
    change_24k_pct: Optional[float]
    source_url: str
    source_label: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Alert Rules
# ---------------------------------------------------------------------------

class AlertRuleCreate(BaseModel):
    rule_type: str = Field(
        ...,
        pattern="^(above|below|pct_change)$",
        description="above | below | pct_change",
    )
    threshold: float = Field(..., gt=0)
    purity: str = Field(default="24K", pattern="^(24K|22K|18K)$")
    label: Optional[str] = Field(default=None, max_length=200)


class AlertRuleUpdate(BaseModel):
    rule_type: Optional[str] = Field(default=None, pattern="^(above|below|pct_change)$")
    threshold: Optional[float] = Field(default=None, gt=0)
    purity: Optional[str] = Field(default=None, pattern="^(24K|22K|18K)$")
    label: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = None


class AlertRuleOut(BaseModel):
    id: int
    created_at: datetime
    rule_type: str
    threshold: float
    purity: str
    is_active: bool
    label: Optional[str]
    last_triggered_at: Optional[datetime]
    last_triggered_price: Optional[float]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Manual trigger response
# ---------------------------------------------------------------------------

class TriggerResponse(BaseModel):
    success: bool
    message: str
    record: Optional[GoldPriceOut] = None
