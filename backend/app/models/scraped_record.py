import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ScrapedRecord(Base):
    __tablename__ = "scraped_records"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(
        String, ForeignKey("scraper_sources.id"), nullable=False, index=True
    )
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("scraper_runs.id"), nullable=False, index=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    accessed_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
