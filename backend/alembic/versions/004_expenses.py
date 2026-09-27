"""expense_categories, expense_recurrences, expenses

Revision ID: 004_expenses
Revises: 003_files
Create Date: 2026-09-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_expenses"
down_revision: Union[str, Sequence[str], None] = "003_files"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(insp: sa.Inspector, name: str) -> bool:
    return name in insp.get_table_names()


def _has_index(insp: sa.Inspector, table: str, name: str) -> bool:
    return name in {i["name"] for i in insp.get_indexes(table)}


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not _has_table(insp, "expense_categories"):
        op.create_table(
            "expense_categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        insp = sa.inspect(conn)

    if _has_table(insp, "expense_categories") and not _has_index(insp, "expense_categories", "ix_expense_categories_user_id"):
        op.create_index("ix_expense_categories_user_id", "expense_categories", ["user_id"])
    if _has_table(insp, "expense_categories") and not _has_index(insp, "expense_categories", "uq_expense_categories_user_name"):
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX uq_expense_categories_user_name ON expense_categories (user_id, lower(name))"
            )
        )

    insp = sa.inspect(conn)
    if not _has_table(insp, "expense_recurrences"):
        op.create_table(
            "expense_recurrences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column(
                "category_id",
                sa.Integer(),
                sa.ForeignKey("expense_categories.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("vendor", sa.String(255), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("interval", sa.String(16), nullable=False, server_default="monthly"),
            sa.Column("day_of_month", sa.Integer(), nullable=False),
            sa.Column("start_on", sa.Date(), nullable=False),
            sa.Column("next_on", sa.Date(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        insp = sa.inspect(conn)

    if _has_table(insp, "expense_recurrences") and not _has_index(
        insp, "expense_recurrences", "ix_expense_recurrences_created_by_id"
    ):
        op.create_index("ix_expense_recurrences_created_by_id", "expense_recurrences", ["created_by_id"])
    if _has_table(insp, "expense_recurrences") and not _has_index(
        insp, "expense_recurrences", "ix_expense_recurrences_category_id"
    ):
        op.create_index("ix_expense_recurrences_category_id", "expense_recurrences", ["category_id"])
    if _has_table(insp, "expense_recurrences") and not _has_index(
        insp, "expense_recurrences", "ix_expense_recurrences_next_on"
    ):
        op.create_index("ix_expense_recurrences_next_on", "expense_recurrences", ["next_on"])

    insp = sa.inspect(conn)
    if not _has_table(insp, "expenses"):
        op.create_table(
            "expenses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column(
                "category_id",
                sa.Integer(),
                sa.ForeignKey("expense_categories.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("spent_on", sa.Date(), nullable=False),
            sa.Column("vendor", sa.String(255), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("receipt_file_id", sa.Integer(), sa.ForeignKey("file_nodes.id", ondelete="SET NULL"), nullable=True),
            sa.Column(
                "recurrence_id",
                sa.Integer(),
                sa.ForeignKey("expense_recurrences.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        insp = sa.inspect(conn)

    if _has_table(insp, "expenses") and not _has_index(insp, "expenses", "ix_expenses_created_by_id"):
        op.create_index("ix_expenses_created_by_id", "expenses", ["created_by_id"])
    if _has_table(insp, "expenses") and not _has_index(insp, "expenses", "ix_expenses_category_id"):
        op.create_index("ix_expenses_category_id", "expenses", ["category_id"])
    if _has_table(insp, "expenses") and not _has_index(insp, "expenses", "ix_expenses_spent_on"):
        op.create_index("ix_expenses_spent_on", "expenses", ["spent_on"])
    if _has_table(insp, "expenses") and not _has_index(insp, "expenses", "ix_expenses_receipt_file_id"):
        op.create_index("ix_expenses_receipt_file_id", "expenses", ["receipt_file_id"])
    if _has_table(insp, "expenses") and not _has_index(insp, "expenses", "ix_expenses_recurrence_id"):
        op.create_index("ix_expenses_recurrence_id", "expenses", ["recurrence_id"])
    if _has_table(insp, "expenses") and not _has_index(insp, "expenses", "uq_expenses_recurrence_spent_on"):
        op.create_index(
            "uq_expenses_recurrence_spent_on",
            "expenses",
            ["recurrence_id", "spent_on"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index("uq_expenses_recurrence_spent_on", table_name="expenses")
    op.drop_index("ix_expenses_recurrence_id", table_name="expenses")
    op.drop_index("ix_expenses_receipt_file_id", table_name="expenses")
    op.drop_index("ix_expenses_spent_on", table_name="expenses")
    op.drop_index("ix_expenses_category_id", table_name="expenses")
    op.drop_index("ix_expenses_created_by_id", table_name="expenses")
    op.drop_table("expenses")
    op.drop_index("ix_expense_recurrences_next_on", table_name="expense_recurrences")
    op.drop_index("ix_expense_recurrences_category_id", table_name="expense_recurrences")
    op.drop_index("ix_expense_recurrences_created_by_id", table_name="expense_recurrences")
    op.drop_table("expense_recurrences")
    op.drop_index("uq_expense_categories_user_name", table_name="expense_categories")
    op.drop_index("ix_expense_categories_user_id", table_name="expense_categories")
    op.drop_table("expense_categories")
