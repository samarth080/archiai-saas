"""Entitlements & usage enforcement (Phase 3).

Backend-verified plan limits and feature flags. The frontend never decides
entitlement — every gate resolves the effective limits server-side from the
user's active Subscription (falling back to free-tier defaults), applies any
per-user Entitlement override, then enforces. Admins bypass all gates (the
manual override escape hatch).
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Entitlement, Plan, Subscription, UsageCounter
from app.models.project import Project
from app.models.user import User

# Feature flag keys (stubs default False on free; a paid plan/override flips them).
FEATURE_DXF_EXPORT = "dxf_export"
FEATURE_BIM_EXPORT = "bim_export"
FEATURE_TEAM_WORKSPACES = "team_workspaces"
FEATURE_ADVANCED_FURNITURE = "advanced_furniture"
FEATURE_COMMERCIAL_TEMPLATES = "commercial_templates"

METRIC_GENERATIONS = "generations"

# Built-in defaults so the app enforces sane quotas even with an empty `plans`
# table — existing (unsubscribed) users are treated as free tier.
DEFAULT_PLAN_LIMITS: dict[str, dict] = {
    "free": {
        "max_projects": 3,
        "max_generations_per_period": 50,
        "layout_candidates": 3,
        "features": {
            FEATURE_DXF_EXPORT: False,
            FEATURE_BIM_EXPORT: False,
            FEATURE_TEAM_WORKSPACES: False,
            FEATURE_ADVANCED_FURNITURE: False,
            FEATURE_COMMERCIAL_TEMPLATES: False,
        },
    },
    "pro": {
        "max_projects": 200,
        "max_generations_per_period": 5000,
        "layout_candidates": 12,
        "features": {
            FEATURE_DXF_EXPORT: True,
            FEATURE_BIM_EXPORT: True,
            FEATURE_TEAM_WORKSPACES: True,
            FEATURE_ADVANCED_FURNITURE: True,
            FEATURE_COMMERCIAL_TEMPLATES: True,
        },
    },
}
DEFAULT_PLAN_CODE = "free"


def current_window(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m")


async def _is_admin(db: AsyncSession, user_id: str) -> bool:
    return bool(await db.scalar(select(User.is_admin).where(User.id == user_id)))


async def _active_plan_code(db: AsyncSession, user_id: str) -> str:
    sub = await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return sub.plan_code if sub else DEFAULT_PLAN_CODE


async def get_effective_limits(db: AsyncSession, user_id: str) -> dict:
    """Resolve the user's limits: plan defaults (DB Plan row or built-in), with
    per-user Entitlement rows layered on top."""
    plan_code = await _active_plan_code(db, user_id)

    plan = await db.scalar(select(Plan).where(Plan.code == plan_code))
    base = dict(plan.limits) if plan and plan.limits else DEFAULT_PLAN_LIMITS.get(plan_code, DEFAULT_PLAN_LIMITS[DEFAULT_PLAN_CODE])
    limits = {
        "plan_code": plan_code,
        "max_projects": base.get("max_projects", 3),
        "max_generations_per_period": base.get("max_generations_per_period", 50),
        "layout_candidates": base.get("layout_candidates", 3),
        "features": dict(base.get("features", {})),
    }

    overrides = await db.execute(
        select(Entitlement).where(
            Entitlement.subject_type == "user",
            Entitlement.subject_id == user_id,
        )
    )
    for row in overrides.scalars():
        value = row.value.get("value") if isinstance(row.value, dict) else row.value
        if row.feature in ("max_projects", "max_generations_per_period", "layout_candidates"):
            limits[row.feature] = value
        else:
            limits["features"][row.feature] = value
    return limits


async def require_within_project_limit(db: AsyncSession, user_id: str) -> None:
    """Raise 402 if creating another personal project would exceed the plan."""
    if await _is_admin(db, user_id):
        return
    limits = await get_effective_limits(db, user_id)
    max_projects = limits["max_projects"]
    count = await db.scalar(
        select(func.count()).select_from(Project).where(Project.user_id == user_id)
    )
    if count is not None and count >= max_projects:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Your {limits['plan_code']} plan allows {max_projects} projects. "
                "Upgrade to create more."
            ),
        )


async def require_feature(db: AsyncSession, user_id: str, feature: str) -> None:
    """Raise 403 if the user's plan/override does not include the feature."""
    if await _is_admin(db, user_id):
        return
    limits = await get_effective_limits(db, user_id)
    if not limits["features"].get(feature, False):
        raise HTTPException(
            status_code=403,
            detail=f"The '{feature}' feature is not available on your {limits['plan_code']} plan.",
        )


async def enforce_and_increment_usage(
    db: AsyncSession,
    user_id: str,
    metric: str,
    limit_key: str,
) -> None:
    """Enforce a metered quota, then increment the counter for this window.
    Raises 402 when the limit is reached."""
    if await _is_admin(db, user_id):
        return
    limits = await get_effective_limits(db, user_id)
    limit = limits.get(limit_key, 0)
    window = current_window()

    counter = await db.scalar(
        select(UsageCounter).where(
            UsageCounter.subject_type == "user",
            UsageCounter.subject_id == user_id,
            UsageCounter.metric == metric,
            UsageCounter.window == window,
        )
    )
    used = counter.count if counter else 0
    if used >= limit:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Your {limits['plan_code']} plan allows {limit} {metric} per month "
                f"(used {used}). Upgrade for more."
            ),
        )

    if counter is None:
        counter = UsageCounter(
            subject_type="user",
            subject_id=user_id,
            metric=metric,
            window=window,
            count=1,
        )
        db.add(counter)
    else:
        counter.count = used + 1
    await db.commit()


async def get_usage(db: AsyncSession, user_id: str, metric: str) -> int:
    window = current_window()
    counter = await db.scalar(
        select(UsageCounter).where(
            UsageCounter.subject_type == "user",
            UsageCounter.subject_id == user_id,
            UsageCounter.metric == metric,
            UsageCounter.window == window,
        )
    )
    return counter.count if counter else 0
