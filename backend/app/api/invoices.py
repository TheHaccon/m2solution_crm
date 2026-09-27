from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, user_is_team_member
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus, InvoiceView
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceListOut, InvoiceOut, InvoiceUpdate, InvoiceViewOut
from app.services.invoice_files import delete_invoice_pdf, save_invoice_pdf
from app.services.invoices import (
    apply_line_items,
    ensure_draft,
    invoice_to_list_out,
    invoice_to_out,
    new_public_token,
    next_invoice_number,
)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _load_invoice(db: Session, invoice_id: int, user: User) -> Invoice:
    invoice = db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.client))
        .where(Invoice.id == invoice_id, Invoice.created_by_id == user.id)
    )
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


def _client_for_invoice(db: Session, client_id: int, user: User) -> Client:
    client = db.get(Client, client_id)
    if client is None or not user_is_team_member(db, user.id, client.team_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


def _store_pdf(db: Session, invoice: Invoice, user: User) -> None:
    save_invoice_pdf(db, invoice, user)


@router.get("", response_model=list[InvoiceListOut])
def list_invoices(
    client_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[InvoiceListOut]:
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.client))
        .where(Invoice.created_by_id == user.id)
        .order_by(Invoice.created_at.desc())
    )
    if client_id is not None:
        stmt = stmt.where(Invoice.client_id == client_id)
    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter)
    return [invoice_to_list_out(inv) for inv in db.scalars(stmt).all()]


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    body: InvoiceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    client = _client_for_invoice(db, body.client_id, user)
    invoice = Invoice(
        client_id=body.client_id,
        created_by_id=user.id,
        number=next_invoice_number(db, body.issue_date),
        status=InvoiceStatus.draft.value,
        issue_date=body.issue_date,
        due_date=body.due_date,
        notes=body.notes,
    )
    invoice.client = client
    apply_line_items(invoice, body.line_items)
    db.add(invoice)
    db.flush()
    _store_pdf(db, invoice, user)
    db.commit()
    return invoice_to_out(_load_invoice(db, invoice.id, user))


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    return invoice_to_out(_load_invoice(db, invoice_id, user))


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    body: InvoiceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = _load_invoice(db, invoice_id, user)
    ensure_draft(invoice)
    data = body.model_dump(exclude_unset=True)
    line_items = data.pop("line_items", None)
    for key, value in data.items():
        setattr(invoice, key, value)
    if line_items is not None:
        apply_line_items(invoice, body.line_items or [])
    db.flush()
    _store_pdf(db, invoice, user)
    db.commit()
    return invoice_to_out(_load_invoice(db, invoice.id, user))


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    invoice = _load_invoice(db, invoice_id, user)
    ensure_draft(invoice)
    delete_invoice_pdf(db, invoice, user)
    db.delete(invoice)
    db.commit()


@router.post("/{invoice_id}/send", response_model=InvoiceOut)
def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = _load_invoice(db, invoice_id, user)
    if invoice.status == InvoiceStatus.void.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send a voided invoice")
    if invoice.status == InvoiceStatus.draft.value:
        invoice.status = InvoiceStatus.sent.value
        invoice.sent_at = datetime.now(timezone.utc)
    if not invoice.public_token:
        invoice.public_token = new_public_token()
    db.flush()
    _store_pdf(db, invoice, user)
    db.commit()
    return invoice_to_out(_load_invoice(db, invoice.id, user))


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceOut)
def mark_paid(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = _load_invoice(db, invoice_id, user)
    if invoice.status not in (InvoiceStatus.sent.value, InvoiceStatus.paid.value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Send the invoice before marking it paid")
    invoice.status = InvoiceStatus.paid.value
    invoice.paid_at = datetime.now(timezone.utc)
    db.flush()
    _store_pdf(db, invoice, user)
    db.commit()
    return invoice_to_out(_load_invoice(db, invoice.id, user))


@router.post("/{invoice_id}/void", response_model=InvoiceOut)
def void_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = _load_invoice(db, invoice_id, user)
    if invoice.status == InvoiceStatus.paid.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Paid invoices cannot be voided")
    invoice.status = InvoiceStatus.void.value
    db.flush()
    _store_pdf(db, invoice, user)
    db.commit()
    return invoice_to_out(_load_invoice(db, invoice.id, user))


@router.post("/{invoice_id}/rotate-link", response_model=InvoiceOut)
def rotate_link(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = _load_invoice(db, invoice_id, user)
    if invoice.status not in (InvoiceStatus.sent.value, InvoiceStatus.paid.value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only sent or paid invoices have a share link")
    invoice.public_token = new_public_token()
    db.commit()
    return invoice_to_out(_load_invoice(db, invoice.id, user))


@router.get("/{invoice_id}/views", response_model=list[InvoiceViewOut])
def list_views(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[InvoiceView]:
    _load_invoice(db, invoice_id, user)
    stmt = (
        select(InvoiceView)
        .where(InvoiceView.invoice_id == invoice_id)
        .order_by(InvoiceView.viewed_at.desc())
        .limit(100)
    )
    return list(db.scalars(stmt).all())
