import sys
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


async def log_activity(
    db: AsyncSession,
    user_id: str,
    action: str,
    project_id: str | None = None,
    workspace_id: str | None = None,
) -> None:
    try:
        entry = ActivityLog(
            user_id=user_id,
            action=action,
            project_id=project_id,
            workspace_id=workspace_id,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(entry)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        print(f"[activity log error] {exc}", file=sys.stderr)
