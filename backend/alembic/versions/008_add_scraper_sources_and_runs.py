"""add scraper sources and runs

Revision ID: 008
Revises: 007
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scraper_sources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("robots_txt_url", sa.Text(), nullable=False),
        sa.Column("is_permitted", sa.Boolean(), nullable=False),
        sa.Column("data_type", sa.String(length=100), nullable=False),
        sa.Column("source_category", sa.String(length=100), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scraper_sources_created_by"),
        "scraper_sources",
        ["created_by"],
    )

    op.create_table(
        "scraper_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("records_collected", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["scraper_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scraper_runs_source_id"), "scraper_runs", ["source_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_scraper_runs_source_id"), table_name="scraper_runs")
    op.drop_table("scraper_runs")
    op.drop_index(op.f("ix_scraper_sources_created_by"), table_name="scraper_sources")
    op.drop_table("scraper_sources")
