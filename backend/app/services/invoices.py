from decimal import Decimal
from datetime import date
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.schemas.invoice import LineItemIn


def next_invoice_number(db: Session, issue_date: date) -> str:
    prefix = f"INV-{issue_date.year}-"
    last = db.scalar(select(func.max(Invoice.number)).where(Invoice.number.like(f"{prefix}%")))
    if last:
        seq = int(last.rsplit("-", 1)[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def new_public_token() -> str:
    return secrets.token_urlsafe(32)


def share_url(token: str | None) -> str | None:
    if not token:
        return None
    base = settings.public_app_url.rstrip("/")
    return f"{base}/i/{token}"


def apply_line_items(invoice: Invoice, items: list[LineItemIn]) -> None:
    invoice.line_items.clear()
    subtotal = Decimal("0.00")
    for item in items:
        amount = (item.quantity * item.unit_price).quantize(Decimal("0.01"))
        subtotal += amount
        invoice.line_items.append(
            InvoiceLineItem(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=amount,
            )
        )
    invoice.subtotal = subtotal
    invoice.total = subtotal


def invoice_to_out(invoice: Invoice):
    from app.schemas.invoice import InvoiceOut

    return InvoiceOut(
        id=invoice.id,
        client_id=invoice.client_id,
        client_name=invoice.client.name,
        client_email=invoice.client.email,
        client_address=invoice.client.address,
        number=invoice.number,
        status=invoice.status,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        notes=invoice.notes,
        subtotal=invoice.subtotal,
        total=invoice.total,
        public_token=invoice.public_token,
        share_url=share_url(invoice.public_token),
        view_count=invoice.view_count,
        last_viewed_at=invoice.last_viewed_at,
        sent_at=invoice.sent_at,
        paid_at=invoice.paid_at,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        line_items=invoice.line_items,
    )


def invoice_to_list_out(invoice: Invoice):
    from app.schemas.invoice import InvoiceListOut

    return InvoiceListOut(
        id=invoice.id,
        client_id=invoice.client_id,
        client_name=invoice.client.name,
        number=invoice.number,
        status=invoice.status,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        total=invoice.total,
        view_count=invoice.view_count,
        last_viewed_at=invoice.last_viewed_at,
        public_token=invoice.public_token,
        share_url=share_url(invoice.public_token),
        created_at=invoice.created_at,
    )


def meeting_to_out(meeting):
    from app.schemas.meeting import MeetingOut

    return MeetingOut(
        id=meeting.id,
        client_id=meeting.client_id,
        client_name=meeting.client.name,
        title=meeting.title,
        scheduled_at=meeting.scheduled_at,
        attendees=meeting.attendees,
        body=meeting.body,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


def ensure_draft(invoice: Invoice) -> None:
    if invoice.status != InvoiceStatus.draft.value:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft invoices can be edited",
        )
