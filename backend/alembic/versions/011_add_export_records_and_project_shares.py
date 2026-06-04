"""add export records and project shares

Revision ID: 011
Revises: 010
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "export_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("export_type", sa.String(length=20), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_export_records_project_id"), "export_records", ["project_id"])
    op.create_index(op.f("ix_export_records_user_id"), "export_records", ["user_id"])

    op.create_table(
        "project_shares",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("token", sa.String(length=120), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("access_type", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_shares_created_by"), "project_shares", ["created_by"])
    op.create_index(op.f("ix_project_shares_project_id"), "project_shares", ["project_id"])
    op.create_index(op.f("ix_project_shares_token"), "project_shares", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_shares_token"), table_name="project_shares")
    op.drop_index(op.f("ix_project_shares_project_id"), table_name="project_shares")
    op.drop_index(op.f("ix_project_shares_created_by"), table_name="project_shares")
    op.drop_table("project_shares")
    op.drop_index(op.f("ix_export_records_user_id"), table_name="export_records")
    op.drop_index(op.f("ix_export_records_project_id"), table_name="export_records")
    op.drop_table("export_records")

