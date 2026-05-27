"""add sprint 7 project management fields

Revision ID: 005
Revises: 004
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("thumbnail_url", sa.Text(), nullable=True))
    op.add_column("design_versions", sa.Column("version_name", sa.String(length=200), nullable=True))
    op.add_column("design_versions", sa.Column("version_type", sa.String(length=50), nullable=True))
    op.add_column("design_versions", sa.Column("change_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("design_versions", "change_summary")
    op.drop_column("design_versions", "version_type")
    op.drop_column("design_versions", "version_name")
    op.drop_column("projects", "thumbnail_url")
