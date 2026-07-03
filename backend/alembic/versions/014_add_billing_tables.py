"""add billing tables

Revision ID: 014
Revises: 013
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def _timestamps():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price_paise", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("interval", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plans_code"), "plans", ["code"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("plan_code", sa.String(length=50), nullable=False, server_default="free"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("razorpay_subscription_id", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"])

    op.create_table(
        "payment_orders",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("plan_code", sa.String(length=50), nullable=False),
        sa.Column("razorpay_order_id", sa.String(length=80), nullable=False),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_orders_user_id"), "payment_orders", ["user_id"])
    op.create_index(op.f("ix_payment_orders_razorpay_order_id"), "payment_orders", ["razorpay_order_id"], unique=True)

    op.create_table(
        "payment_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_events_event_id"), "payment_events", ["event_id"], unique=True)

    op.create_table(
        "entitlements",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("feature", sa.String(length=80), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_type", "subject_id", "feature", name="uq_entitlement_subject_feature"),
    )
    op.create_index(op.f("ix_entitlements_subject_id"), "entitlements", ["subject_id"])

    op.create_table(
        "usage_counters",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("metric", sa.String(length=80), nullable=False),
        sa.Column("window", sa.String(length=20), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_type", "subject_id", "metric", "window", name="uq_usage_subject_metric_window"),
    )
    op.create_index(op.f("ix_usage_counters_subject_id"), "usage_counters", ["subject_id"])


def downgrade() -> None:
    op.drop_table("usage_counters")
    op.drop_table("entitlements")
    op.drop_index(op.f("ix_payment_events_event_id"), table_name="payment_events")
    op.drop_table("payment_events")
    op.drop_index(op.f("ix_payment_orders_razorpay_order_id"), table_name="payment_orders")
    op.drop_index(op.f("ix_payment_orders_user_id"), table_name="payment_orders")
    op.drop_table("payment_orders")
    op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index(op.f("ix_plans_code"), table_name="plans")
    op.drop_table("plans")
