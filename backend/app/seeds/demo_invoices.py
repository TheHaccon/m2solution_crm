from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus, InvoiceView
from app.schemas.invoice import LineItemIn
from app.seeds.context import DEV_PUBLIC_INVOICE_TOKEN, DevSeedContext
from app.services.invoices import apply_line_items


def _line_items() -> list[LineItemIn]:
    return [
        LineItemIn(description="Consulting (dev seed)", quantity=Decimal("3"), unit_price=Decimal("125.00")),
        LineItemIn(description="Materials", quantity=Decimal("1"), unit_price=Decimal("50.00")),
    ]


def _add_invoice(
    db: Session,
    ctx: DevSeedContext,
    *,
    key: str,
    status: InvoiceStatus,
    number: str,
    issue: date,
    public_token: str | None = None,
    view_count: int = 0,
) -> Invoice:
    client = ctx.clients[0]
    assert ctx.primary_user
    inv = Invoice(
        client_id=client.id,
        created_by_id=ctx.primary_user.id,
        number=number,
        status=status.value,
        issue_date=issue,
        due_date=date(issue.year, issue.month, min(issue.day + 15, 28)),
        notes="Dev seed invoice",
        public_token=public_token,
        view_count=view_count,
    )
    apply_line_items(inv, _line_items())
    if status == InvoiceStatus.sent:
        inv.sent_at = datetime(issue.year, issue.month, issue.day, 12, 0, tzinfo=timezone.utc)
    if status == InvoiceStatus.paid:
        inv.sent_at = datetime(issue.year, issue.month, issue.day, 12, 0, tzinfo=timezone.utc)
        inv.public_token = public_token or DEV_PUBLIC_INVOICE_TOKEN
        inv.paid_at = datetime(issue.year, issue.month, min(issue.day + 5, 28), 9, 0, tzinfo=timezone.utc)
    db.add(inv)
    db.flush()
    ctx.invoices[key] = inv
    return inv


def seed_demo_invoices(db: Session, ctx: DevSeedContext) -> None:
    if not ctx.clients or ctx.primary_user is None:
        return
    y = ctx.seed_year
    _add_invoice(
        db,
        ctx,
        key="draft",
        status=InvoiceStatus.draft,
        number=f"INV-{y}-0001",
        issue=date(y, 1, 10),
    )
    sent = _add_invoice(
        db,
        ctx,
        key="sent",
        status=InvoiceStatus.sent,
        number=f"INV-{y}-0002",
        issue=date(y, 4, 2),
        public_token=DEV_PUBLIC_INVOICE_TOKEN,
        view_count=2,
    )
    db.add(
        InvoiceView(
            invoice_id=sent.id,
            viewed_at=datetime(y, 4, 3, 10, 0, tzinfo=timezone.utc),
            viewer_cookie="dev-viewer-a",
            user_agent="DevSeed/1.0",
        )
    )
    db.add(
        InvoiceView(
            invoice_id=sent.id,
            viewed_at=datetime(y, 4, 5, 14, 0, tzinfo=timezone.utc),
            viewer_cookie="dev-viewer-b",
            user_agent="DevSeed/1.0",
        )
    )
    _add_invoice(
        db,
        ctx,
        key="paid",
        status=InvoiceStatus.paid,
        number=f"INV-{y}-0003",
        issue=date(y, 2, 15),
        public_token="dev-paid-invoice-token-for-accounting-demo",
    )
    _add_invoice(
        db,
        ctx,
        key="void",
        status=InvoiceStatus.void,
        number=f"INV-{y}-0004",
        issue=date(y, 5, 1),
    )
