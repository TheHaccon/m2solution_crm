from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.expense import Expense, ExpenseCategory
from app.models.file import FileKind, FileNode, FileSpace
from app.models.user import User, utcnow
from app.services.file_storage import get_storage

EXPENSES_FOLDER = "Expenses"


def _safe_name(name: str) -> str:
    cleaned = " ".join((name or "receipt").split())
    cleaned = cleaned.replace("/", "-").replace("\\", "-").replace("\x00", "")
    if not cleaned or cleaned in {".", ".."}:
        cleaned = "receipt"
    return cleaned[:255]


def ensure_personal_expenses_folder(db: Session, user: User) -> FileNode:
    folder = db.scalar(
        select(FileNode).where(
            FileNode.space == FileSpace.personal.value,
            FileNode.owner_id == user.id,
            FileNode.parent_id.is_(None),
            FileNode.kind == FileKind.folder.value,
            func.lower(FileNode.name) == EXPENSES_FOLDER.lower(),
        )
    )
    if folder is not None:
        return folder
    folder = FileNode(
        kind=FileKind.folder.value,
        name=EXPENSES_FOLDER,
        parent_id=None,
        space=FileSpace.personal.value,
        team_id=None,
        owner_id=user.id,
        storage_backend="local",
        created_by_id=user.id,
    )
    db.add(folder)
    db.flush()
    return folder


def _child_folder(db: Session, parent: FileNode, name: str) -> FileNode | None:
    return db.scalar(
        select(FileNode).where(
            FileNode.parent_id == parent.id,
            FileNode.kind == FileKind.folder.value,
            FileNode.owner_id == parent.owner_id,
            func.lower(FileNode.name) == name.lower(),
        )
    )


def ensure_category_folder(db: Session, user: User, category_name: str) -> FileNode:
    root = ensure_personal_expenses_folder(db, user)
    name = _safe_name(category_name)
    existing = _child_folder(db, root, name)
    if existing is not None:
        return existing
    folder = FileNode(
        kind=FileKind.folder.value,
        name=name,
        parent_id=root.id,
        space=FileSpace.personal.value,
        team_id=None,
        owner_id=user.id,
        storage_backend="local",
        created_by_id=user.id,
    )
    db.add(folder)
    db.flush()
    return folder


def ensure_all_category_folders(db: Session, user: User) -> FileNode:
    root = ensure_personal_expenses_folder(db, user)
    categories = db.scalars(select(ExpenseCategory).where(ExpenseCategory.user_id == user.id)).all()
    for category in categories:
        ensure_category_folder(db, user, category.name)
    relocate_receipts(db, user)
    return root


def rename_category_folder(db: Session, user: User, old_name: str, new_name: str) -> FileNode:
    root = ensure_personal_expenses_folder(db, user)
    dest_name = _safe_name(new_name)
    old = _child_folder(db, root, _safe_name(old_name))
    dest = _child_folder(db, root, dest_name)
    if old is None:
        return dest if dest is not None else ensure_category_folder(db, user, new_name)
    if dest is not None and dest.id != old.id:
        for child in db.scalars(select(FileNode).where(FileNode.parent_id == old.id)).all():
            child.parent_id = dest.id
            child.updated_at = utcnow()
        db.flush()
        leftover = db.scalar(select(FileNode.id).where(FileNode.parent_id == old.id).limit(1))
        if leftover is None:
            db.delete(old)
            db.flush()
        return dest
    old.name = dest_name
    old.updated_at = utcnow()
    db.flush()
    return old


def place_receipt(db: Session, user: User, node: FileNode, category_name: str) -> FileNode:
    folder = ensure_category_folder(db, user, category_name)
    if node.parent_id != folder.id:
        node.parent_id = folder.id
        node.updated_at = utcnow()
        db.flush()
    return node


def relocate_receipts(db: Session, user: User) -> None:
    expenses = db.scalars(
        select(Expense)
        .options(selectinload(Expense.category), selectinload(Expense.receipt))
        .where(Expense.created_by_id == user.id, Expense.receipt_file_id.is_not(None))
    ).all()
    for expense in expenses:
        if expense.receipt is None:
            continue
        place_receipt(db, user, expense.receipt, expense.category.name)


def save_expense_receipt(
    db: Session,
    user: User,
    expense_id: int,
    category_name: str,
    filename: str,
    data: bytes,
    mime_type: str,
    existing_node: FileNode | None,
) -> FileNode:
    folder = ensure_category_folder(db, user, category_name)
    storage = get_storage()
    name = f"expense-{expense_id}-{_safe_name(filename)}"
    if existing_node is not None and existing_node.owner_id == user.id:
        if not existing_node.storage_key:
            existing_node.storage_key = storage.new_key()
        storage.put(existing_node.storage_key, data)
        existing_node.name = name
        existing_node.mime_type = mime_type
        existing_node.size_bytes = len(data)
        existing_node.parent_id = folder.id
        existing_node.updated_at = utcnow()
        db.flush()
        return existing_node
    key = storage.new_key()
    storage.put(key, data)
    node = FileNode(
        kind=FileKind.file.value,
        name=name,
        parent_id=folder.id,
        space=FileSpace.personal.value,
        team_id=None,
        owner_id=user.id,
        storage_key=key,
        mime_type=mime_type,
        size_bytes=len(data),
        storage_backend="local",
        created_by_id=user.id,
    )
    db.add(node)
    db.flush()
    return node


def delete_expense_receipt(db: Session, node: FileNode | None) -> None:
    if node is None:
        return
    key = node.storage_key
    db.delete(node)
    db.flush()
    if key:
        get_storage().delete(key)
