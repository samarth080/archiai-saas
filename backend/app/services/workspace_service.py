from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.project import Project
from app.models.team_member import TeamMember
from app.models.user import User
from app.models.workspace import Workspace
from app.utils.activity import log_activity

WORKSPACE_ROLES = {"owner", "admin", "editor", "viewer"}
WORKSPACE_ADMIN_ROLES = {"owner", "admin"}


async def get_workspace(db: AsyncSession, workspace_id: str) -> Workspace:
    workspace = await db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


async def get_workspace_member(
    db: AsyncSession,
    workspace_id: str,
    user_id: str,
) -> TeamMember:
    await get_workspace(db, workspace_id)
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.workspace_id == workspace_id,
            TeamMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return member


async def require_workspace_role(
    db: AsyncSession,
    workspace_id: str,
    user_id: str,
    allowed_roles: set[str],
) -> TeamMember:
    member = await get_workspace_member(db, workspace_id, user_id)
    if member.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return member


async def create_workspace(
    db: AsyncSession,
    user_id: str,
    name: str,
    description: str | None,
) -> tuple[Workspace, TeamMember]:
    workspace = Workspace(
        name=name,
        description=description,
        owner_id=user_id,
    )
    db.add(workspace)
    await db.flush()
    owner = TeamMember(
        workspace_id=workspace.id,
        user_id=user_id,
        role="owner",
    )
    db.add(owner)
    await db.commit()
    await db.refresh(workspace)
    await db.refresh(owner)
    await log_activity(
        db,
        user_id,
        "workspace.created",
        workspace_id=workspace.id,
    )
    return workspace, owner


async def list_workspaces(
    db: AsyncSession,
    user_id: str,
) -> list[tuple[Workspace, TeamMember]]:
    result = await db.execute(
        select(Workspace, TeamMember)
        .join(TeamMember, TeamMember.workspace_id == Workspace.id)
        .where(TeamMember.user_id == user_id)
        .order_by(desc(Workspace.updated_at))
    )
    return list(result.all())


async def get_workspace_for_member(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
) -> tuple[Workspace, TeamMember]:
    workspace = await get_workspace(db, workspace_id)
    member = await get_workspace_member(db, workspace_id, user_id)
    return workspace, member


async def update_workspace(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
) -> tuple[Workspace, TeamMember]:
    member = await require_workspace_role(
        db,
        workspace_id,
        user_id,
        WORKSPACE_ADMIN_ROLES,
    )
    workspace = await get_workspace(db, workspace_id)
    if name is not None:
        workspace.name = name
    if description is not None:
        workspace.description = description
    workspace.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(workspace)
    await log_activity(
        db,
        user_id,
        "workspace.updated",
        workspace_id=workspace.id,
    )
    return workspace, member


async def delete_workspace(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
) -> None:
    await require_workspace_role(db, workspace_id, user_id, {"owner"})
    await db.execute(
        update(Project)
        .where(Project.workspace_id == workspace_id)
        .values(workspace_id=None)
    )
    await db.execute(delete(TeamMember).where(TeamMember.workspace_id == workspace_id))
    workspace = await get_workspace(db, workspace_id)
    await db.delete(workspace)
    await db.commit()
    await log_activity(
        db,
        user_id,
        "workspace.deleted",
        workspace_id=workspace_id,
    )


async def list_members(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
) -> list[tuple[TeamMember, User]]:
    await get_workspace_member(db, workspace_id, user_id)
    result = await db.execute(
        select(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .where(TeamMember.workspace_id == workspace_id)
        .order_by(TeamMember.created_at)
    )
    return list(result.all())


async def add_member(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
    *,
    email: str,
    role: str,
) -> tuple[TeamMember, User]:
    await require_workspace_role(
        db,
        workspace_id,
        user_id,
        WORKSPACE_ADMIN_ROLES,
    )
    if role not in WORKSPACE_ROLES or role == "owner":
        raise HTTPException(status_code=422, detail="Invalid workspace role")
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    existing_result = await db.execute(
        select(TeamMember).where(
            TeamMember.workspace_id == workspace_id,
            TeamMember.user_id == user.id,
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="User is already a workspace member")

    member = TeamMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    await log_activity(
        db,
        user_id,
        "workspace.member_added",
        workspace_id=workspace_id,
    )
    return member, user


async def get_member(
    db: AsyncSession,
    workspace_id: str,
    member_id: str,
) -> TeamMember:
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.id == member_id,
            TeamMember.workspace_id == workspace_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=404, detail="Workspace member not found")
    return member


async def update_member_role(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
    member_id: str,
    *,
    role: str,
) -> TeamMember:
    await require_workspace_role(
        db,
        workspace_id,
        user_id,
        WORKSPACE_ADMIN_ROLES,
    )
    if role not in WORKSPACE_ROLES or role == "owner":
        raise HTTPException(status_code=422, detail="Invalid workspace role")
    member = await get_member(db, workspace_id, member_id)
    if member.role == "owner":
        raise HTTPException(status_code=422, detail="Workspace owner cannot be changed")
    member.role = role
    await db.commit()
    await db.refresh(member)
    await log_activity(
        db,
        user_id,
        "workspace.member_role_changed",
        workspace_id=workspace_id,
    )
    return member


async def remove_member(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
    member_id: str,
) -> None:
    await require_workspace_role(
        db,
        workspace_id,
        user_id,
        WORKSPACE_ADMIN_ROLES,
    )
    member = await get_member(db, workspace_id, member_id)
    if member.role == "owner":
        raise HTTPException(status_code=422, detail="Workspace owner cannot be removed")
    await db.delete(member)
    await db.commit()
    await log_activity(
        db,
        user_id,
        "workspace.member_removed",
        workspace_id=workspace_id,
    )


async def list_workspace_activity(
    db: AsyncSession,
    user_id: str,
    workspace_id: str,
) -> list[ActivityLog]:
    await get_workspace_member(db, workspace_id, user_id)
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.workspace_id == workspace_id)
        .order_by(desc(ActivityLog.timestamp))
        .limit(50)
    )
    return list(result.scalars().all())
