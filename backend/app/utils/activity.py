import sys

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


async def log_activity(db: AsyncSession, user_id: str, action: str) -> None:
    try:
        entry = ActivityLog(user_id=user_id, action=action)
        db.add(entry)
        await db.commit()
    except Exception as exc:
        print(f"[activity log error] {exc}", file=sys.stderr)
