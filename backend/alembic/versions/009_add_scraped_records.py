"""add scraped records

Revision ID: 009
Revises: 008
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scraped_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "accessed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("raw_metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["scraper_runs.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["scraper_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scraped_records_run_id"), "scraped_records", ["run_id"])
    op.create_index(
        op.f("ix_scraped_records_source_id"),
        "scraped_records",
        ["source_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_scraped_records_source_id"), table_name="scraped_records")
    op.drop_index(op.f("ix_scraped_records_run_id"), table_name="scraped_records")
    op.drop_table("scraped_records")
