from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.invoice import Invoice, InvoiceStatus, InvoiceView
from app.models.user import utcnow
from app.schemas.invoice import PublicInvoiceOut

VIEWER_COOKIE = "invoice_viewer"
DEDUP_SECONDS = 30

router = APIRouter(prefix="/api/public/invoices", tags=["public"])


def _hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


@router.get("/{token}", response_model=PublicInvoiceOut)
def get_public_invoice(
    token: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> PublicInvoiceOut:
    invoice = db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.client))
        .where(Invoice.public_token == token)
    )
    if invoice is None or invoice.status not in (InvoiceStatus.sent.value, InvoiceStatus.paid.value):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    cookie = request.headers.get("x-viewer-id") or request.cookies.get(VIEWER_COOKIE)
    if not cookie:
        cookie = secrets.token_urlsafe(16)
    response.set_cookie(
        VIEWER_COOKIE,
        cookie,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="lax",
        path="/",
    )

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=DEDUP_SECONDS)
    recent = db.scalar(
        select(InvoiceView).where(
            InvoiceView.invoice_id == invoice.id,
            InvoiceView.viewer_cookie == cookie,
            InvoiceView.viewed_at >= cutoff,
        )
    )
    if recent is None:
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
        ua = request.headers.get("user-agent")
        db.add(
            InvoiceView(
                invoice_id=invoice.id,
                viewed_at=utcnow(),
                viewer_cookie=cookie,
                ip_hash=_hash_ip(ip),
                user_agent=(ua[:512] if ua else None),
            )
        )
        invoice.view_count = (invoice.view_count or 0) + 1
        invoice.last_viewed_at = utcnow()
        db.commit()
        db.refresh(invoice)

    return PublicInvoiceOut(
        number=invoice.number,
        status=invoice.status,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        notes=invoice.notes,
        subtotal=invoice.subtotal,
        total=invoice.total,
        client_name=invoice.client.name,
        client_email=invoice.client.email,
        client_address=invoice.client.address,
        line_items=invoice.line_items,
        company_name=settings.company_name,
        company_email=settings.company_email,
        company_address=settings.company_address,
        company_phone=settings.company_phone,
    )
