"""add workspaces and team members

Revision ID: 007
Revises: 006
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspaces_owner_id"), "workspaces", ["owner_id"])

    op.create_table(
        "team_members",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_team_members_workspace_user",
        ),
    )
    op.create_index(
        op.f("ix_team_members_workspace_id"),
        "team_members",
        ["workspace_id"],
    )
    op.create_index(op.f("ix_team_members_user_id"), "team_members", ["user_id"])

    op.add_column("projects", sa.Column("workspace_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_projects_workspace_id_workspaces",
        "projects",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_index(op.f("ix_projects_workspace_id"), "projects", ["workspace_id"])

    op.add_column("activity_logs", sa.Column("workspace_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_activity_logs_workspace_id"),
        "activity_logs",
        ["workspace_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_logs_workspace_id"), table_name="activity_logs")
    op.drop_column("activity_logs", "workspace_id")

    op.drop_index(op.f("ix_projects_workspace_id"), table_name="projects")
    op.drop_constraint(
        "fk_projects_workspace_id_workspaces",
        "projects",
        type_="foreignkey",
    )
    op.drop_column("projects", "workspace_id")

    op.drop_index(op.f("ix_team_members_user_id"), table_name="team_members")
    op.drop_index(op.f("ix_team_members_workspace_id"), table_name="team_members")
    op.drop_table("team_members")

    op.drop_index(op.f("ix_workspaces_owner_id"), table_name="workspaces")
    op.drop_table("workspaces")
