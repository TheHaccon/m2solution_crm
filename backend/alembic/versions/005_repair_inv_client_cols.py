"""Repair missing clients.team_id and invoices.created_by_id

Revision ID: 005_repair_inv_client_cols
Revises: 004_expenses
Create Date: 2026-09-27

Stamp-ahead databases may be at 004_expenses without the 002_teams column
alters. This revision re-applies only those missing alters (existence-checked).
It does not create teams / team_members tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_repair_inv_client_cols"
down_revision: Union[str, Sequence[str], None] = "004_expenses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(insp: sa.Inspector, table: str, col: str) -> bool:
    return col in {c["name"] for c in insp.get_columns(table)}


def _has_index(insp: sa.Inspector, table: str, name: str) -> bool:
    return name in {i["name"] for i in insp.get_indexes(table)}


def _has_fk(insp: sa.Inspector, table: str, name: str) -> bool:
    return name in {fk["name"] for fk in insp.get_foreign_keys(table)}


def upgrade() -> None:
    conn = op.get_bind()

    team_id = conn.execute(sa.text("SELECT id FROM teams ORDER BY id LIMIT 1")).scalar()
    if team_id is None:
        team_id = conn.execute(
            sa.text("INSERT INTO teams (name, created_at) VALUES ('M2 Solution', NOW()) RETURNING id")
        ).scalar()
    conn.execute(
        sa.text(
            "INSERT INTO team_members (team_id, user_id, created_at) "
            "SELECT :team_id, u.id, NOW() FROM users u "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM team_members m WHERE m.team_id = :team_id AND m.user_id = u.id"
            ")"
        ),
        {"team_id": team_id},
    )

    insp = sa.inspect(conn)
    if not _has_column(insp, "clients", "team_id"):
        op.add_column("clients", sa.Column("team_id", sa.Integer(), nullable=True))
        conn.execute(sa.text("UPDATE clients SET team_id = :team_id"), {"team_id": team_id})
        op.alter_column("clients", "team_id", existing_type=sa.Integer(), nullable=False)
        insp = sa.inspect(conn)
    if not _has_fk(insp, "clients", "fk_clients_team_id"):
        op.create_foreign_key(
            "fk_clients_team_id",
            "clients",
            "teams",
            ["team_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    if not _has_index(insp, "clients", "ix_clients_team_id"):
        op.create_index("ix_clients_team_id", "clients", ["team_id"])

    insp = sa.inspect(conn)
    if not _has_column(insp, "invoices", "created_by_id"):
        op.add_column("invoices", sa.Column("created_by_id", sa.Integer(), nullable=True))
        conn.execute(sa.text("UPDATE invoices SET created_by_id = (SELECT id FROM users ORDER BY id LIMIT 1)"))
        op.alter_column("invoices", "created_by_id", existing_type=sa.Integer(), nullable=False)
        insp = sa.inspect(conn)
    if not _has_fk(insp, "invoices", "fk_invoices_created_by_id"):
        op.create_foreign_key(
            "fk_invoices_created_by_id",
            "invoices",
            "users",
            ["created_by_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    if not _has_index(insp, "invoices", "ix_invoices_created_by_id"):
        op.create_index("ix_invoices_created_by_id", "invoices", ["created_by_id"])


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if _has_index(insp, "invoices", "ix_invoices_created_by_id"):
        op.drop_index("ix_invoices_created_by_id", table_name="invoices")
    if _has_fk(insp, "invoices", "fk_invoices_created_by_id"):
        op.drop_constraint("fk_invoices_created_by_id", "invoices", type_="foreignkey")
    if _has_column(insp, "invoices", "created_by_id"):
        op.drop_column("invoices", "created_by_id")

    insp = sa.inspect(conn)
    if _has_index(insp, "clients", "ix_clients_team_id"):
        op.drop_index("ix_clients_team_id", table_name="clients")
    if _has_fk(insp, "clients", "fk_clients_team_id"):
        op.drop_constraint("fk_clients_team_id", "clients", type_="foreignkey")
    if _has_column(insp, "clients", "team_id"):
        op.drop_column("clients", "team_id")
