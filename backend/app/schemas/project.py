from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    workspace_id: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Title is required")
        return title

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        description = value.strip()
        return description or None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    workspace_id: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        if not title:
            raise ValueError("Title is required")
        return title

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        description = value.strip()
        return description or None


class ProjectOut(BaseModel):
    id: str
    user_id: str
    workspace_id: str | None = None
    title: str
    description: str | None
    thumbnail_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectVersionOut(BaseModel):
    id: str
    design_id: str
    project_id: str
    version_number: int
    version_name: str | None = None
    version_type: str | None = None
    change_summary: str | None = None
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogOut(BaseModel):
    id: str
    action: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ExportRecordOut(BaseModel):
    id: str
    project_id: str
    user_id: str
    export_type: str
    file_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectShareOut(BaseModel):
    id: str
    project_id: str
    token: str
    share_url: str
    access_type: str
    is_active: bool
    created_at: datetime
    revoked_at: datetime | None = None


class PublicProjectSummary(BaseModel):
    id: str
    title: str
    description: str | None = None


class PublicSharedProjectOut(BaseModel):
    project: PublicProjectSummary
    layout: dict[str, Any] | None = None
