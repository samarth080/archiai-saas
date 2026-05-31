import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ScraperSource(Base):
    __tablename__ = "scraper_sources"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    robots_txt_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_permitted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_category: Mapped[str] = mapped_column(String(100), nullable=False)
    added_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_checked: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
