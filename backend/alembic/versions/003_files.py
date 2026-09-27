"""file_nodes for staff file manager

Revision ID: 003_files
Revises: 002_teams
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_files"
down_revision: Union[str, Sequence[str], None] = "002_teams"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(insp: sa.Inspector, name: str) -> bool:
    return name in insp.get_table_names()


def _has_index(insp: sa.Inspector, table: str, name: str) -> bool:
    return name in {i["name"] for i in insp.get_indexes(table)}


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not _has_table(insp, "file_nodes"):
        op.create_table(
            "file_nodes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kind", sa.String(16), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("file_nodes.id", ondelete="CASCADE"), nullable=True),
            sa.Column("space", sa.String(16), nullable=False),
            sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=True),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("storage_key", sa.String(32), nullable=True),
            sa.Column("mime_type", sa.String(127), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("storage_backend", sa.String(16), nullable=False, server_default="local"),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        insp = sa.inspect(conn)

    if _has_table(insp, "file_nodes") and not _has_index(insp, "file_nodes", "ix_file_nodes_kind"):
        op.create_index("ix_file_nodes_kind", "file_nodes", ["kind"])
    if _has_table(insp, "file_nodes") and not _has_index(insp, "file_nodes", "ix_file_nodes_parent_id"):
        op.create_index("ix_file_nodes_parent_id", "file_nodes", ["parent_id"])
    if _has_table(insp, "file_nodes") and not _has_index(insp, "file_nodes", "ix_file_nodes_space"):
        op.create_index("ix_file_nodes_space", "file_nodes", ["space"])
    if _has_table(insp, "file_nodes") and not _has_index(insp, "file_nodes", "ix_file_nodes_team_id"):
        op.create_index("ix_file_nodes_team_id", "file_nodes", ["team_id"])
    if _has_table(insp, "file_nodes") and not _has_index(insp, "file_nodes", "ix_file_nodes_owner_id"):
        op.create_index("ix_file_nodes_owner_id", "file_nodes", ["owner_id"])
    if _has_table(insp, "file_nodes") and not _has_index(insp, "file_nodes", "ix_file_nodes_storage_key"):
        op.create_index("ix_file_nodes_storage_key", "file_nodes", ["storage_key"], unique=True)

    insp = sa.inspect(conn)
    if _has_table(insp, "file_nodes") and not _has_index(insp, "file_nodes", "uq_file_nodes_sibling_name"):
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX uq_file_nodes_sibling_name ON file_nodes "
                "(space, COALESCE(team_id, 0), COALESCE(owner_id, 0), COALESCE(parent_id, 0), name)"
            )
        )


def downgrade() -> None:
    op.drop_index("uq_file_nodes_sibling_name", table_name="file_nodes")
    op.drop_index("ix_file_nodes_storage_key", table_name="file_nodes")
    op.drop_index("ix_file_nodes_owner_id", table_name="file_nodes")
    op.drop_index("ix_file_nodes_team_id", table_name="file_nodes")
    op.drop_index("ix_file_nodes_space", table_name="file_nodes")
    op.drop_index("ix_file_nodes_parent_id", table_name="file_nodes")
    op.drop_index("ix_file_nodes_kind", table_name="file_nodes")
    op.drop_table("file_nodes")
