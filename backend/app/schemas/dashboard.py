from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class DashboardInvoice(BaseModel):
    id: int
    number: str
    client_name: str
    status: str
    total: Decimal
    view_count: int
    due_date: date | None = None
    issue_date: date | None = None


class DashboardMeeting(BaseModel):
    id: int
    title: str
    client_name: str
    scheduled_at: datetime


class DashboardView(BaseModel):
    invoice_id: int
    invoice_number: str
    client_name: str
    viewed_at: datetime


class DashboardOut(BaseModel):
    unpaid_count: int
    unpaid_total: Decimal
    draft_count: int
    paid_count: int
    recent_invoices: list[DashboardInvoice]
    recent_meetings: list[DashboardMeeting]
    recent_views: list[DashboardView]
