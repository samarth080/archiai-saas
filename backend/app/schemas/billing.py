from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PlanOut(BaseModel):
    code: str
    name: str
    price_paise: int
    currency: str
    interval: str

    model_config = {"from_attributes": True}


class CreateOrderRequest(BaseModel):
    plan_code: str


class OrderOut(BaseModel):
    razorpay_order_id: str
    amount_paise: int
    currency: str
    key_id: str  # public Razorpay key id — safe for the browser checkout


class SubscriptionStatusOut(BaseModel):
    plan_code: str
    status: str
    current_period_end: datetime | None = None
    limits: dict[str, Any]
    usage: dict[str, int]
