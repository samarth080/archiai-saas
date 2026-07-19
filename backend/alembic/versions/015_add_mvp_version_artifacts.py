"""add canonical MVP artifacts to design versions

Revision ID: 015
Revises: 014
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "design_versions",
        sa.Column("requirements_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "design_versions",
        sa.Column("canonical_layout_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "design_versions",
        sa.Column("quality_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("design_versions", "quality_json")
    op.drop_column("design_versions", "canonical_layout_json")
    op.drop_column("design_versions", "requirements_json")
