from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.file import FileNode
from app.models.user import utcnow


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    expenses: Mapped[list["Expense"]] = relationship(back_populates="category")
    recurrences: Mapped[list["ExpenseRecurrence"]] = relationship(back_populates="category")


Index(
    "uq_expense_categories_user_name",
    ExpenseCategory.user_id,
    func.lower(ExpenseCategory.name),
    unique=True,
)


class ExpenseRecurrence(Base):
    __tablename__ = "expense_recurrences"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("expense_categories.id", ondelete="RESTRICT"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    interval: Mapped[str] = mapped_column(String(16), default="monthly")
    day_of_month: Mapped[int] = mapped_column(Integer)
    start_on: Mapped[date] = mapped_column(Date)
    next_on: Mapped[date] = mapped_column(Date, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    category: Mapped[ExpenseCategory] = relationship(back_populates="recurrences")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="recurrence")


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (UniqueConstraint("recurrence_id", "spent_on", name="uq_expenses_recurrence_spent_on"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("expense_categories.id", ondelete="RESTRICT"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    spent_on: Mapped[date] = mapped_column(Date, index=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_file_id: Mapped[int | None] = mapped_column(
        ForeignKey("file_nodes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recurrence_id: Mapped[int | None] = mapped_column(
        ForeignKey("expense_recurrences.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    category: Mapped[ExpenseCategory] = relationship(back_populates="expenses")
    recurrence: Mapped[ExpenseRecurrence | None] = relationship(back_populates="expenses")
    receipt: Mapped[FileNode | None] = relationship()
