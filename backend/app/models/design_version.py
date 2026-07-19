import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class DesignVersion(Base):
    __tablename__ = "design_versions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    design_id: Mapped[str] = mapped_column(
        String, ForeignKey("designs.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    version_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Additive MVP-pipeline artifacts. ``layout_json`` remains the legacy
    # center-based canvas snapshot so existing editor/version/share flows keep
    # working; the canonical NW-origin LayoutPlan is stored separately.
    requirements_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    canonical_layout_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quality_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prompt_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
