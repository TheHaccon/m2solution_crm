from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_team, get_current_user
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus, InvoiceView
from app.models.meeting import Meeting
from app.models.team import Team
from app.models.user import User
from app.schemas.dashboard import DashboardInvoice, DashboardMeeting, DashboardOut, DashboardView

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team),
) -> DashboardOut:
    mine = Invoice.created_by_id == user.id
    unpaid_filter = mine & (Invoice.status == InvoiceStatus.sent.value)
    unpaid_count = db.scalar(select(func.count()).select_from(Invoice).where(unpaid_filter)) or 0
    unpaid_total = db.scalar(select(func.coalesce(func.sum(Invoice.total), 0)).where(unpaid_filter)) or Decimal("0")
    draft_count = db.scalar(
        select(func.count()).select_from(Invoice).where(mine, Invoice.status == InvoiceStatus.draft.value)
    ) or 0
    paid_count = db.scalar(
        select(func.count()).select_from(Invoice).where(mine, Invoice.status == InvoiceStatus.paid.value)
    ) or 0

    recent_invoices = db.scalars(
        select(Invoice)
        .options(selectinload(Invoice.client))
        .where(mine)
        .order_by(Invoice.created_at.desc())
        .limit(8)
    ).all()
    recent_meetings = db.scalars(
        select(Meeting)
        .options(selectinload(Meeting.client))
        .join(Client)
        .where(Client.team_id == team.id)
        .order_by(Meeting.scheduled_at.desc())
        .limit(6)
    ).all()
    recent_views = db.scalars(
        select(InvoiceView)
        .join(Invoice)
        .options(selectinload(InvoiceView.invoice).selectinload(Invoice.client))
        .where(Invoice.created_by_id == user.id)
        .order_by(InvoiceView.viewed_at.desc())
        .limit(8)
    ).all()

    return DashboardOut(
        unpaid_count=unpaid_count,
        unpaid_total=unpaid_total,
        draft_count=draft_count,
        paid_count=paid_count,
        recent_invoices=[
            DashboardInvoice(
                id=inv.id,
                number=inv.number,
                client_name=inv.client.name,
                status=inv.status,
                total=inv.total,
                view_count=inv.view_count,
                due_date=inv.due_date,
                issue_date=inv.issue_date,
            )
            for inv in recent_invoices
        ],
        recent_meetings=[
            DashboardMeeting(
                id=m.id,
                title=m.title,
                client_name=m.client.name,
                scheduled_at=m.scheduled_at,
            )
            for m in recent_meetings
        ],
        recent_views=[
            DashboardView(
                invoice_id=v.invoice_id,
                invoice_number=v.invoice.number,
                client_name=v.invoice.client.name,
                viewed_at=v.viewed_at,
            )
            for v in recent_views
        ],
    )
