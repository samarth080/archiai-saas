"""add layout patterns

Revision ID: 010
Revises: 009
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "layout_patterns",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("building_type", sa.String(length=100), nullable=True),
        sa.Column("layout_pattern", sa.String(length=100), nullable=True),
        sa.Column("room_type", sa.String(length=100), nullable=True),
        sa.Column("typical_area_sqm_min", sa.Float(), nullable=True),
        sa.Column("typical_area_sqm_max", sa.Float(), nullable=True),
        sa.Column("zone", sa.String(length=100), nullable=True),
        sa.Column("adjacent_to", sa.JSON(), nullable=False),
        sa.Column("avoid_adjacent_to", sa.JSON(), nullable=False),
        sa.Column("room_to_total_area_ratio_min", sa.Float(), nullable=True),
        sa.Column("room_to_total_area_ratio_max", sa.Float(), nullable=True),
        sa.Column("circulation_notes", sa.Text(), nullable=True),
        sa.Column("door_window_notes", sa.Text(), nullable=True),
        sa.Column("accessibility_notes", sa.Text(), nullable=True),
        sa.Column("egress_notes", sa.Text(), nullable=True),
        sa.Column("placement_notes", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["source_id"], ["scraper_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_layout_patterns_source_id"), "layout_patterns", ["source_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_layout_patterns_source_id"), table_name="layout_patterns")
    op.drop_table("layout_patterns")
