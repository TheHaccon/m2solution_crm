from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import extract, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.expense import Expense, ExpenseCategory, ExpenseRecurrence
from app.models.user import User, utcnow
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseRecurrenceOut, ExpenseUpdate
from app.services.expense_files import place_receipt

DEFAULT_CATEGORIES = ("Gas", "Purchase", "Auto", "Subscription", "Other")
MAX_CATCH_UP = 36


def add_one_month(d: date, day_of_month: int) -> date:
    if d.month == 12:
        year, month = d.year + 1, 1
    else:
        year, month = d.year, d.month + 1
    day = min(max(day_of_month, 1), monthrange(year, month)[1])
    return date(year, month, day)


def normalize_category_name(name: str) -> str:
    cleaned = " ".join(name.split())
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name is required")
    if len(cleaned) > 80:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name is too long")
    return cleaned


def seed_categories(db: Session, user: User) -> list[ExpenseCategory]:
    existing = list(
        db.scalars(select(ExpenseCategory).where(ExpenseCategory.user_id == user.id).order_by(ExpenseCategory.name)).all()
    )
    have = {c.name.lower() for c in existing}
    added = False
    for name in DEFAULT_CATEGORIES:
        if name.lower() in have:
            continue
        db.add(ExpenseCategory(user_id=user.id, name=name))
        have.add(name.lower())
        added = True
    if added:
        db.flush()
        existing = list(
            db.scalars(
                select(ExpenseCategory).where(ExpenseCategory.user_id == user.id).order_by(ExpenseCategory.name)
            ).all()
        )
    return existing


def load_category(db: Session, user: User, category_id: int) -> ExpenseCategory:
    category = db.scalar(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id, ExpenseCategory.user_id == user.id)
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def load_expense(db: Session, user: User, expense_id: int) -> Expense:
    expense = db.scalar(
        select(Expense)
        .options(selectinload(Expense.category), selectinload(Expense.receipt))
        .where(Expense.id == expense_id, Expense.created_by_id == user.id)
    )
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


def load_recurrence(db: Session, user: User, recurrence_id: int) -> ExpenseRecurrence:
    row = db.scalar(
        select(ExpenseRecurrence)
        .options(selectinload(ExpenseRecurrence.category))
        .where(ExpenseRecurrence.id == recurrence_id, ExpenseRecurrence.created_by_id == user.id)
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurrence not found")
    return row


def expense_to_out(expense: Expense) -> ExpenseOut:
    receipt = expense.receipt
    return ExpenseOut(
        id=expense.id,
        category_id=expense.category_id,
        category_name=expense.category.name,
        amount=expense.amount,
        spent_on=expense.spent_on,
        vendor=expense.vendor,
        notes=expense.notes,
        receipt_file_id=expense.receipt_file_id,
        receipt_name=receipt.name if receipt is not None else None,
        recurrence_id=expense.recurrence_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


def recurrence_to_out(row: ExpenseRecurrence) -> ExpenseRecurrenceOut:
    return ExpenseRecurrenceOut(
        id=row.id,
        category_id=row.category_id,
        category_name=row.category.name,
        amount=row.amount,
        vendor=row.vendor,
        notes=row.notes,
        interval=row.interval,
        day_of_month=row.day_of_month,
        start_on=row.start_on,
        next_on=row.next_on,
        active=row.active,
        created_at=row.created_at,
    )


def materialize_recurrences(db: Session, user: User, today: date | None = None) -> int:
    today = today or date.today()
    recurrences = list(
        db.scalars(
            select(ExpenseRecurrence).where(
                ExpenseRecurrence.created_by_id == user.id,
                ExpenseRecurrence.active.is_(True),
                ExpenseRecurrence.next_on <= today,
            )
        ).all()
    )
    created = 0
    for rec in recurrences:
        steps = 0
        while rec.active and rec.next_on <= today and steps < MAX_CATCH_UP:
            exists = db.scalar(
                select(Expense.id).where(Expense.recurrence_id == rec.id, Expense.spent_on == rec.next_on)
            )
            if exists is None:
                db.add(
                    Expense(
                        created_by_id=user.id,
                        category_id=rec.category_id,
                        amount=rec.amount,
                        spent_on=rec.next_on,
                        vendor=rec.vendor,
                        notes=rec.notes,
                        recurrence_id=rec.id,
                    )
                )
                created += 1
            rec.next_on = add_one_month(rec.next_on, rec.day_of_month)
            rec.updated_at = utcnow()
            steps += 1
        if steps >= MAX_CATCH_UP and rec.next_on <= today:
            rec.active = False
    if created:
        db.flush()
    return created


def list_expenses(db: Session, user: User, year: int, category_id: int | None) -> list[Expense]:
    materialize_recurrences(db, user)
    stmt = (
        select(Expense)
        .options(selectinload(Expense.category), selectinload(Expense.receipt))
        .where(Expense.created_by_id == user.id, extract("year", Expense.spent_on) == year)
        .order_by(Expense.spent_on.desc(), Expense.id.desc())
    )
    if category_id is not None:
        stmt = stmt.where(Expense.category_id == category_id)
    return list(db.scalars(stmt).all())


def create_expense(db: Session, user: User, body: ExpenseCreate) -> Expense:
    materialize_recurrences(db, user)
    category = load_category(db, user, body.category_id)
    amount = Decimal(body.amount).quantize(Decimal("0.01"))
    vendor = (body.vendor or "").strip() or None
    notes = (body.notes or "").strip() or None
    recurrence: ExpenseRecurrence | None = None
    if body.repeat_monthly:
        recurrence = ExpenseRecurrence(
            created_by_id=user.id,
            category_id=category.id,
            amount=amount,
            vendor=vendor,
            notes=notes,
            interval="monthly",
            day_of_month=body.spent_on.day,
            start_on=body.spent_on,
            next_on=add_one_month(body.spent_on, body.spent_on.day),
            active=True,
        )
        db.add(recurrence)
        db.flush()
    expense = Expense(
        created_by_id=user.id,
        category_id=category.id,
        amount=amount,
        spent_on=body.spent_on,
        vendor=vendor,
        notes=notes,
        recurrence_id=recurrence.id if recurrence is not None else None,
    )
    db.add(expense)
    db.flush()
    db.refresh(expense, attribute_names=["category", "receipt"])
    return expense


def update_expense(db: Session, user: User, expense: Expense, body: ExpenseUpdate) -> Expense:
    data = body.model_dump(exclude_unset=True)
    if "category_id" in data and data["category_id"] is not None:
        load_category(db, user, data["category_id"])
        expense.category_id = data["category_id"]
    if "amount" in data and data["amount"] is not None:
        expense.amount = Decimal(data["amount"]).quantize(Decimal("0.01"))
    if "spent_on" in data and data["spent_on"] is not None:
        expense.spent_on = data["spent_on"]
    if "vendor" in data:
        expense.vendor = (data["vendor"] or "").strip() or None
    if "notes" in data:
        expense.notes = (data["notes"] or "").strip() or None
    expense.updated_at = utcnow()
    db.flush()
    updated = load_expense(db, user, expense.id)
    if updated.receipt is not None:
        place_receipt(db, user, updated.receipt, updated.category.name)
    return updated


def category_in_use(db: Session, category_id: int) -> bool:
    if db.scalar(select(func.count()).select_from(Expense).where(Expense.category_id == category_id)):
        return True
    if db.scalar(select(func.count()).select_from(ExpenseRecurrence).where(ExpenseRecurrence.category_id == category_id)):
        return True
    return False


def create_category(db: Session, user: User, name: str) -> ExpenseCategory:
    seed_categories(db, user)
    cleaned = normalize_category_name(name)
    row = ExpenseCategory(user_id=user.id, name=cleaned)
    db.add(row)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with that name already exists") from exc
    return row
