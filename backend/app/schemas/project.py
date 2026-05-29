from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ProjectOut(BaseModel):
    id: str
    user_id: str
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
