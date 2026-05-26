"""create designs and design_versions tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "designs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("layout_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_designs_project_id"), "designs", ["project_id"], unique=False)
    op.create_index(op.f("ix_designs_user_id"), "designs", ["user_id"], unique=False)

    op.create_table(
        "design_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("design_id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("layout_json", sa.JSON(), nullable=False),
        sa.Column("prompt_used", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["design_id"], ["designs.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_design_versions_design_id"),
        "design_versions",
        ["design_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_design_versions_project_id"),
        "design_versions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_design_versions_user_id"),
        "design_versions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_design_versions_user_id"), table_name="design_versions")
    op.drop_index(op.f("ix_design_versions_project_id"), table_name="design_versions")
    op.drop_index(op.f("ix_design_versions_design_id"), table_name="design_versions")
    op.drop_table("design_versions")
    op.drop_index(op.f("ix_designs_user_id"), table_name="designs")
    op.drop_index(op.f("ix_designs_project_id"), table_name="designs")
    op.drop_table("designs")
