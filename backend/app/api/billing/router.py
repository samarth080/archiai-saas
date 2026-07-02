from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.connection import get_db
from app.models.billing import Plan, Subscription
from app.schemas.billing import (
    CreateOrderRequest,
    OrderOut,
    PlanOut,
    SubscriptionStatusOut,
)
from app.services.auth_service import get_current_user
from app.services.billing_service import create_order, handle_webhook
from app.services.entitlement_service import (
    METRIC_GENERATIONS,
    get_effective_limits,
    get_usage,
)
from app.utils.rate_limit import rate_limit

router = APIRouter(prefix="/api/billing", tags=["billing"])
_bearer = HTTPBearer(auto_error=False)


async def _current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await get_current_user(db, credentials.credentials)
    return str(user.id)


@router.get("/plans", response_model=list[PlanOut])
async def plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.price_paise))
    return list(result.scalars().all())


@router.get("/subscription", response_model=SubscriptionStatusOut)
async def subscription(
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    limits = await get_effective_limits(db, user_id)
    sub = await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return SubscriptionStatusOut(
        plan_code=limits["plan_code"],
        status=sub.status if sub else "none",
        current_period_end=sub.current_period_end if sub else None,
        limits=limits,
        usage={"generations": await get_usage(db, user_id, METRIC_GENERATIONS)},
    )


@router.post(
    "/orders",
    response_model=OrderOut,
    dependencies=[Depends(rate_limit("billing_order", limit=10, window_seconds=60))],
)
async def create_order_endpoint(
    data: CreateOrderRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    order = await create_order(db, user_id, data.plan_code)
    return OrderOut(
        razorpay_order_id=order.razorpay_order_id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post(
    "/webhook",
    dependencies=[Depends(rate_limit("billing_webhook", limit=60, window_seconds=60))],
)
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    event_id = request.headers.get("X-Razorpay-Event-Id")
    return await handle_webhook(db, body, signature, event_id)
