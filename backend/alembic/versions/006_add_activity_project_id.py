"""add project_id to activity_logs

Revision ID: 006
Revises: 005
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("activity_logs", sa.Column("project_id", sa.String(), nullable=True))
    op.create_index(
        "ix_activity_logs_project_id",
        "activity_logs",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_project_id", table_name="activity_logs")
    op.drop_column("activity_logs", "project_id")
