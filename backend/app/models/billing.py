"""Billing / monetization models (Phase 3).

Razorpay-ready but provider-agnostic in shape. IMPORTANT: we never store card,
bank, UPI, or PAN data — only Razorpay's opaque order/payment/subscription ids
and our own plan/usage bookkeeping. Payment status is only ever set from a
signature-verified webhook, never from a client-reported value.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Plan(Base):
    """A subscription tier. `limits` is a JSON blob of quotas + feature flags,
    e.g. {"max_projects": 3, "max_generations_per_period": 50,
          "features": {"dxf_export": false, "team_workspaces": false}}."""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    interval: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    limits: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True, nullable=False)
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    razorpay_subscription_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True, nullable=False)
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False)
    razorpay_order_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )


class PaymentEvent(Base):
    """Raw, signature-verified webhook events. `event_id` is unique so a
    re-delivered webhook is a no-op (idempotency)."""

    __tablename__ = "payment_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    event_id: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )


class Entitlement(Base):
    """A per-subject feature override on top of the plan defaults (e.g. a manual
    admin grant). Value is JSON so it can hold a bool flag or a numeric limit."""

    __tablename__ = "entitlements"
    __table_args__ = (
        UniqueConstraint("subject_type", "subject_id", "feature", name="uq_entitlement_subject_feature"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    subject_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    subject_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    feature: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )


class UsageCounter(Base):
    """A metered usage counter within a window (e.g. metric='generations',
    window='2026-07'). Enforced against the plan limit before incrementing."""

    __tablename__ = "usage_counters"
    __table_args__ = (
        UniqueConstraint("subject_type", "subject_id", "metric", "window", name="uq_usage_subject_metric_window"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    subject_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    subject_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    metric: Mapped[str] = mapped_column(String(80), nullable=False)
    window: Mapped[str] = mapped_column(String(20), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )
