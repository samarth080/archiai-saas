from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.user import User
from app.schemas.project import ActivityLogOut
from app.schemas.workspace import (
    AddWorkspaceMemberRequest,
    TeamMemberOut,
    UpdateWorkspaceMemberRoleRequest,
    WorkspaceCreate,
    WorkspaceOut,
    WorkspaceUpdate,
)
from app.services.auth_service import get_current_user
from app.services.workspace_service import (
    add_member,
    create_workspace,
    delete_workspace,
    get_workspace_for_member,
    list_members,
    list_workspace_activity,
    list_workspaces,
    remove_member,
    update_member_role,
    update_workspace,
)

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])
bearer = HTTPBearer(auto_error=False)


async def _current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await get_current_user(db, credentials.credentials)
    return user.id


def _workspace_out(workspace, member) -> WorkspaceOut:
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        current_user_role=member.role,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


def _member_out(member, user: User) -> TeamMemberOut:
    return TeamMemberOut(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        email=user.email,
        name=user.name,
        role=member.role,
        created_at=member.created_at,
    )


@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
async def create_workspace_endpoint(
    data: WorkspaceCreate,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    workspace, member = await create_workspace(db, user_id, data.name, data.description)
    return _workspace_out(workspace, member)


@router.get("", response_model=list[WorkspaceOut])
async def list_workspaces_endpoint(
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    workspaces = await list_workspaces(db, user_id)
    return [_workspace_out(workspace, member) for workspace, member in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace_endpoint(
    workspace_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    workspace, member = await get_workspace_for_member(db, user_id, workspace_id)
    return _workspace_out(workspace, member)


@router.put("/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace_endpoint(
    workspace_id: str,
    data: WorkspaceUpdate,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    workspace, member = await update_workspace(
        db,
        user_id,
        workspace_id,
        name=data.name,
        description=data.description,
    )
    return _workspace_out(workspace, member)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_endpoint(
    workspace_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_workspace(db, user_id, workspace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{workspace_id}/members", response_model=list[TeamMemberOut])
async def list_members_endpoint(
    workspace_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    members = await list_members(db, user_id, workspace_id)
    return [_member_out(member, user) for member, user in members]


@router.post(
    "/{workspace_id}/members",
    response_model=TeamMemberOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_member_endpoint(
    workspace_id: str,
    data: AddWorkspaceMemberRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    member, user = await add_member(
        db,
        user_id,
        workspace_id,
        email=data.email,
        role=data.role,
    )
    return _member_out(member, user)


@router.put("/{workspace_id}/members/{member_id}/role", response_model=TeamMemberOut)
async def update_member_role_endpoint(
    workspace_id: str,
    member_id: str,
    data: UpdateWorkspaceMemberRoleRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    member = await update_member_role(
        db,
        user_id,
        workspace_id,
        member_id,
        role=data.role,
    )
    user = await db.get(User, member.user_id)
    return _member_out(member, user)


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    workspace_id: str,
    member_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await remove_member(db, user_id, workspace_id, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{workspace_id}/activity", response_model=list[ActivityLogOut])
async def list_workspace_activity_endpoint(
    workspace_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    activity = await list_workspace_activity(db, user_id, workspace_id)
    return [ActivityLogOut.model_validate(entry) for entry in activity]
