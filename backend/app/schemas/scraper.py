from datetime import datetime
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


def _validate_public_url(value: str) -> str:
    url = value.strip()
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("A valid HTTP or HTTPS URL is required")
    return url


class ScraperSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    base_url: str
    robots_txt_url: str
    data_type: str = Field(..., min_length=1, max_length=100)
    source_category: str = Field(..., min_length=1, max_length=100)

    @field_validator("name", "data_type", "source_category")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value is required")
        return cleaned

    @field_validator("base_url", "robots_txt_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _validate_public_url(value)


class ScraperSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = None
    robots_txt_url: str | None = None
    data_type: str | None = Field(default=None, min_length=1, max_length=100)
    source_category: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("name", "data_type", "source_category")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value is required")
        return cleaned

    @field_validator("base_url", "robots_txt_url")
    @classmethod
    def validate_optional_url(cls, value: str | None) -> str | None:
        return _validate_public_url(value) if value is not None else None


class ScraperSourceOut(BaseModel):
    id: str
    name: str
    base_url: str
    robots_txt_url: str
    is_permitted: bool
    data_type: str
    source_category: str
    added_at: datetime
    last_checked: datetime | None = None
    created_by: str

    model_config = {"from_attributes": True}


class ScraperRunRequest(BaseModel):
    source_id: str


class ScraperRunOut(BaseModel):
    id: str
    source_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    records_collected: int
    error_message: str | None = None

    model_config = {"from_attributes": True}


class LayoutPatternOut(BaseModel):
    id: str
    source_id: str
    source_url: str
    accessed_at: datetime
    building_type: str | None = None
    layout_pattern: str | None = None
    room_type: str | None = None
    typical_area_sqm_min: float | None = None
    typical_area_sqm_max: float | None = None
    zone: str | None = None
    adjacent_to: list[str]
    avoid_adjacent_to: list[str]
    room_to_total_area_ratio_min: float | None = None
    room_to_total_area_ratio_max: float | None = None
    circulation_notes: str | None = None
    door_window_notes: str | None = None
    accessibility_notes: str | None = None
    egress_notes: str | None = None
    placement_notes: str | None = None
    confidence: str
    created_at: datetime

    model_config = {"from_attributes": True}
