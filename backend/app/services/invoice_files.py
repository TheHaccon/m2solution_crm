from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.file import FileKind, FileNode, FileSpace
from app.models.invoice import Invoice
from app.models.user import User, utcnow
from app.services.file_storage import get_storage
from app.services.invoice_pdf import build_invoice_pdf

INVOICES_FOLDER = "Invoices"


def ensure_personal_invoices_folder(db: Session, user: User) -> FileNode:
    folder = db.scalar(
        select(FileNode).where(
            FileNode.space == FileSpace.personal.value,
            FileNode.owner_id == user.id,
            FileNode.parent_id.is_(None),
            FileNode.kind == FileKind.folder.value,
            func.lower(FileNode.name) == INVOICES_FOLDER.lower(),
        )
    )
    if folder is not None:
        return folder
    folder = FileNode(
        kind=FileKind.folder.value,
        name=INVOICES_FOLDER,
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


def _pdf_name(invoice: Invoice) -> str:
    return f"{invoice.number}.pdf"


def save_invoice_pdf(db: Session, invoice: Invoice, user: User) -> FileNode:
    folder = ensure_personal_invoices_folder(db, user)
    data = build_invoice_pdf(invoice)
    name = _pdf_name(invoice)
    storage = get_storage()
    node = db.scalar(
        select(FileNode).where(
            FileNode.parent_id == folder.id,
            FileNode.kind == FileKind.file.value,
            FileNode.name == name,
        )
    )
    if node is None:
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
            mime_type="application/pdf",
            size_bytes=len(data),
            storage_backend="local",
            created_by_id=user.id,
        )
        db.add(node)
        db.flush()
        return node
    if not node.storage_key:
        node.storage_key = storage.new_key()
    storage.put(node.storage_key, data)
    node.mime_type = "application/pdf"
    node.size_bytes = len(data)
    node.updated_at = utcnow()
    return node


def delete_invoice_pdf(db: Session, invoice: Invoice, user: User) -> None:
    folder = db.scalar(
        select(FileNode).where(
            FileNode.space == FileSpace.personal.value,
            FileNode.owner_id == user.id,
            FileNode.parent_id.is_(None),
            FileNode.kind == FileKind.folder.value,
            func.lower(FileNode.name) == INVOICES_FOLDER.lower(),
        )
    )
    if folder is None:
        return
    node = db.scalar(
        select(FileNode).where(
            FileNode.parent_id == folder.id,
            FileNode.kind == FileKind.file.value,
            FileNode.name == _pdf_name(invoice),
        )
    )
    if node is None:
        return
    key = node.storage_key
    db.delete(node)
    db.flush()
    if key:
        get_storage().delete(key)
