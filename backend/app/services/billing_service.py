"""Razorpay-backed billing (Phase 3).

Order creation via Razorpay's REST API (httpx, no SDK) and a signature-verified,
idempotent webhook — the only place a payment/subscription is ever marked paid.
We store just Razorpay's opaque ids and our own bookkeeping; never card / bank /
UPI / PAN data.
"""
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.billing import PaymentEvent, PaymentOrder, Plan, Subscription

RAZORPAY_API = "https://api.razorpay.com/v1"

_PAID_EVENT_TYPES = {"order.paid", "payment.captured"}
_INTERVAL_DAYS = {"monthly": 30, "yearly": 365}


def verify_webhook_signature(body: bytes, signature: str | None) -> bool:
    """HMAC-SHA256 over the raw body with the webhook secret, constant-time
    compared. Returns False (never raises) on any missing input."""
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def create_order(db: AsyncSession, user_id: str, plan_code: str) -> PaymentOrder:
    plan = await db.scalar(select(Plan).where(Plan.code == plan_code, Plan.is_active.is_(True)))
    if plan is None or plan.price_paise <= 0:
        raise HTTPException(status_code=400, detail="That plan is not purchasable.")
    if not settings.razorpay_configured:
        raise HTTPException(status_code=503, detail="Payments are not configured.")

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{RAZORPAY_API}/orders",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            json={
                "amount": plan.price_paise,
                "currency": plan.currency,
                "notes": {"user_id": user_id, "plan_code": plan_code},
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Could not create a payment order.")
    data = response.json()

    order = PaymentOrder(
        user_id=user_id,
        plan_code=plan_code,
        razorpay_order_id=data["id"],
        amount_paise=plan.price_paise,
        currency=plan.currency,
        status="created",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


def _extract_order_id(payload: dict) -> str | None:
    entities = payload.get("payload", {}) or {}
    order = (entities.get("order") or {}).get("entity") or {}
    if order.get("id"):
        return order["id"]
    payment = (entities.get("payment") or {}).get("entity") or {}
    return payment.get("order_id")


async def _activate_subscription(db: AsyncSession, order: PaymentOrder) -> None:
    plan = await db.scalar(select(Plan).where(Plan.code == order.plan_code))
    interval = plan.interval if plan else "monthly"
    period_end = datetime.now(timezone.utc) + timedelta(days=_INTERVAL_DAYS.get(interval, 30))

    sub = await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == order.user_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    if sub is None:
        sub = Subscription(user_id=order.user_id, plan_code=order.plan_code)
        db.add(sub)
    sub.plan_code = order.plan_code
    sub.status = "active"
    sub.current_period_end = period_end


async def handle_webhook(db: AsyncSession, body: bytes, signature: str | None, event_id: str | None) -> dict:
    """Verify, de-duplicate, and process a Razorpay webhook. Idempotent on
    `event_id`. A bad signature is rejected before anything is persisted."""
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    try:
        payload = json.loads(body)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Malformed webhook body.")

    # Razorpay sends X-Razorpay-Event-Id for idempotency; fall back to a hash of
    # the body so a missing header still de-duplicates.
    resolved_event_id = event_id or hashlib.sha256(body).hexdigest()

    existing = await db.scalar(
        select(PaymentEvent).where(PaymentEvent.event_id == resolved_event_id)
    )
    if existing is not None:
        return {"status": "duplicate", "event_id": resolved_event_id}

    event_type = payload.get("event", "unknown")
    event = PaymentEvent(
        event_id=resolved_event_id,
        event_type=event_type,
        payload=payload,
        verified=True,
        processed=False,
    )
    db.add(event)

    if event_type in _PAID_EVENT_TYPES:
        order_id = _extract_order_id(payload)
        if order_id:
            order = await db.scalar(
                select(PaymentOrder).where(PaymentOrder.razorpay_order_id == order_id)
            )
            if order is not None:
                order.status = "paid"
                await _activate_subscription(db, order)
    event.processed = True
    await db.commit()
    return {"status": "processed", "event_id": resolved_event_id, "event_type": event_type}
