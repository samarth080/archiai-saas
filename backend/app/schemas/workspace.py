from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

WorkspaceRole = Literal["owner", "admin", "editor", "viewer"]
AssignableWorkspaceRole = Literal["admin", "editor", "viewer"]


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Workspace name is required")
        return name

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        description = value.strip()
        return description or None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if not name:
            raise ValueError("Workspace name is required")
        return name

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        description = value.strip()
        return description or None


class WorkspaceOut(BaseModel):
    id: str
    name: str
    description: str | None
    owner_id: str
    current_user_role: WorkspaceRole
    created_at: datetime
    updated_at: datetime


class AddWorkspaceMemberRequest(BaseModel):
    email: EmailStr
    role: AssignableWorkspaceRole = "editor"


class UpdateWorkspaceMemberRoleRequest(BaseModel):
    role: AssignableWorkspaceRole


class TeamMemberOut(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    email: str
    name: str
    role: WorkspaceRole
    created_at: datetime
