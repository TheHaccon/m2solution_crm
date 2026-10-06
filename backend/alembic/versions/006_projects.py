"""projects and time_entries

Revision ID: 006_projects
Revises: 005_repair_inv_client_cols
Create Date: 2026-10-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_projects"
down_revision: Union[str, Sequence[str], None] = "005_repair_inv_client_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(insp: sa.Inspector, name: str) -> bool:
    return name in insp.get_table_names()


def _has_index(insp: sa.Inspector, table: str, name: str) -> bool:
    return name in {i["name"] for i in insp.get_indexes(table)}


def _has_fk(insp: sa.Inspector, table: str, name: str) -> bool:
    return name in {fk["name"] for fk in insp.get_foreign_keys(table)}


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not _has_table(insp, "projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("team_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        insp = sa.inspect(conn)

    if _has_table(insp, "projects") and not _has_fk(insp, "projects", "fk_projects_team_id"):
        op.create_foreign_key(
            "fk_projects_team_id",
            "projects",
            "teams",
            ["team_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    if _has_table(insp, "projects") and not _has_index(insp, "projects", "ix_projects_team_id"):
        op.create_index("ix_projects_team_id", "projects", ["team_id"])
    if _has_table(insp, "projects") and not _has_index(insp, "projects", "ix_projects_name"):
        op.create_index("ix_projects_name", "projects", ["name"], unique=False)

    insp = sa.inspect(conn)
    if not _has_table(insp, "time_entries"):
        op.create_table(
            "time_entries",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("source", sa.String(16), nullable=False),
            sa.Column("work_date", sa.Date(), nullable=True),
            sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("segment_started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        insp = sa.inspect(conn)

    if _has_table(insp, "time_entries") and not _has_fk(insp, "time_entries", "fk_time_entries_user_id"):
        op.create_foreign_key(
            "fk_time_entries_user_id",
            "time_entries",
            "users",
            ["user_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    if _has_table(insp, "time_entries") and not _has_fk(insp, "time_entries", "fk_time_entries_project_id"):
        op.create_foreign_key(
            "fk_time_entries_project_id",
            "time_entries",
            "projects",
            ["project_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    if _has_table(insp, "time_entries") and not _has_index(insp, "time_entries", "ix_time_entries_user_id"):
        op.create_index("ix_time_entries_user_id", "time_entries", ["user_id"])
    if _has_table(insp, "time_entries") and not _has_index(insp, "time_entries", "ix_time_entries_project_id"):
        op.create_index("ix_time_entries_project_id", "time_entries", ["project_id"])
    if _has_table(insp, "time_entries") and not _has_index(insp, "time_entries", "uq_time_entries_one_running"):
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX uq_time_entries_one_running ON time_entries (user_id) "
                "WHERE segment_started_at IS NOT NULL AND ended_at IS NULL"
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if _has_table(insp, "time_entries"):
        op.drop_table("time_entries")
    insp = sa.inspect(conn)
    if _has_table(insp, "projects"):
        op.drop_table("projects")
