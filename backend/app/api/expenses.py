from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.expense import ExpenseRecurrence
from app.models.file import FileNode
from app.models.user import User, utcnow
from app.schemas.expense import (
    ExpenseCategoryCreate,
    ExpenseCategoryOut,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseOut,
    ExpenseRecurrenceOut,
    ExpenseRecurrenceUpdate,
    ExpenseUpdate,
)
from app.services.expense_files import delete_expense_receipt, ensure_all_category_folders, ensure_category_folder, rename_category_folder, save_expense_receipt
from app.services.expenses import (
    category_in_use,
    create_category,
    create_expense,
    expense_to_out,
    list_expenses,
    load_category,
    load_expense,
    load_recurrence,
    materialize_recurrences,
    normalize_category_name,
    recurrence_to_out,
    seed_categories,
    update_expense,
)

router = APIRouter(tags=["expenses"])


def _year_param(year: int | None) -> int:
    value = year if year is not None else date.today().year
    if value < 2000 or value > 2100:
        raise HTTPException(status_code=400, detail="year must be between 2000 and 2100")
    return value


@router.get("/api/expense-categories", response_model=list[ExpenseCategoryOut])
def get_categories(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ExpenseCategoryOut]:
    rows = seed_categories(db, user)
    ensure_all_category_folders(db, user)
    db.commit()
    return [ExpenseCategoryOut.model_validate(row) for row in rows]


@router.post("/api/expense-categories", response_model=ExpenseCategoryOut, status_code=status.HTTP_201_CREATED)
def post_category(
    body: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExpenseCategoryOut:
    row = create_category(db, user, body.name)
    ensure_category_folder(db, user, row.name)
    db.commit()
    db.refresh(row)
    return ExpenseCategoryOut.model_validate(row)


@router.patch("/api/expense-categories/{category_id}", response_model=ExpenseCategoryOut)
def patch_category(
    category_id: int,
    body: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExpenseCategoryOut:
    row = load_category(db, user, category_id)
    old_name = row.name
    row.name = normalize_category_name(body.name)
    rename_category_folder(db, user, old_name, row.name)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with that name already exists") from exc
    db.refresh(row)
    return ExpenseCategoryOut.model_validate(row)


@router.delete("/api/expense-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = load_category(db, user, category_id)
    if category_in_use(db, row.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category is still in use")
    db.delete(row)
    db.commit()


@router.get("/api/expenses", response_model=list[ExpenseOut])
def get_expenses(
    year: int | None = Query(default=None),
    category_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ExpenseOut]:
    rows = list_expenses(db, user, _year_param(year), category_id)
    db.commit()
    return [expense_to_out(row) for row in rows]


@router.post("/api/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def post_expense(
    body: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExpenseOut:
    expense = create_expense(db, user, body)
    db.commit()
    expense = load_expense(db, user, expense.id)
    return expense_to_out(expense)


@router.patch("/api/expenses/{expense_id}", response_model=ExpenseOut)
def patch_expense(
    expense_id: int,
    body: ExpenseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExpenseOut:
    expense = load_expense(db, user, expense_id)
    expense = update_expense(db, user, expense, body)
    db.commit()
    return expense_to_out(expense)


@router.delete("/api/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    expense = load_expense(db, user, expense_id)
    receipt = expense.receipt
    expense.receipt_file_id = None
    db.flush()
    delete_expense_receipt(db, receipt)
    db.delete(expense)
    db.commit()


@router.post("/api/expenses/{expense_id}/receipt", response_model=ExpenseOut)
async def post_receipt(
    expense_id: int,
    file: Annotated[UploadFile, File()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExpenseOut:
    expense = load_expense(db, user, expense_id)
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.files_max_bytes:
            raise HTTPException(status_code=413, detail="File too large (max 25 MB)")
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    existing = db.get(FileNode, expense.receipt_file_id) if expense.receipt_file_id else None
    mime = file.content_type or "application/octet-stream"
    node = save_expense_receipt(
        db, user, expense.id, expense.category.name, file.filename or "receipt", data, mime, existing
    )
    expense.receipt_file_id = node.id
    expense.updated_at = utcnow()
    db.commit()
    expense = load_expense(db, user, expense.id)
    return expense_to_out(expense)


@router.get("/api/expense-recurrences", response_model=list[ExpenseRecurrenceOut])
def get_recurrences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ExpenseRecurrenceOut]:
    materialize_recurrences(db, user)
    rows = list(
        db.scalars(
            select(ExpenseRecurrence)
            .options(selectinload(ExpenseRecurrence.category))
            .where(ExpenseRecurrence.created_by_id == user.id)
            .order_by(ExpenseRecurrence.active.desc(), ExpenseRecurrence.next_on)
        ).all()
    )
    db.commit()
    return [recurrence_to_out(row) for row in rows]


@router.patch("/api/expense-recurrences/{recurrence_id}", response_model=ExpenseRecurrenceOut)
def patch_recurrence(
    recurrence_id: int,
    body: ExpenseRecurrenceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ExpenseRecurrenceOut:
    row = load_recurrence(db, user, recurrence_id)
    data = body.model_dump(exclude_unset=True)
    if "category_id" in data and data["category_id"] is not None:
        load_category(db, user, data["category_id"])
        row.category_id = data["category_id"]
    if "amount" in data and data["amount"] is not None:
        row.amount = data["amount"]
    if "vendor" in data:
        row.vendor = (data["vendor"] or "").strip() or None
    if "notes" in data:
        row.notes = (data["notes"] or "").strip() or None
    if "active" in data and data["active"] is not None:
        row.active = data["active"]
    row.updated_at = utcnow()
    db.commit()
    row = load_recurrence(db, user, row.id)
    return recurrence_to_out(row)


@router.delete("/api/expense-recurrences/{recurrence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurrence(
    recurrence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = load_recurrence(db, user, recurrence_id)
    db.delete(row)
    db.commit()
