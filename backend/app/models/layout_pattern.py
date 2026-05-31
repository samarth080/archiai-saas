import uuid

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class LayoutPattern(Base):
    __tablename__ = "layout_patterns"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(
        String, ForeignKey("scraper_sources.id"), nullable=False, index=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    accessed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    building_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    layout_pattern: Mapped[str | None] = mapped_column(String(100), nullable=True)
    room_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    typical_area_sqm_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    typical_area_sqm_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    zone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    adjacent_to: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    avoid_adjacent_to: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    room_to_total_area_ratio_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    room_to_total_area_ratio_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    circulation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    door_window_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    egress_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    placement_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
