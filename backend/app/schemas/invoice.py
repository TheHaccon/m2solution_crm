from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class LineItemIn(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class LineItemOut(BaseModel):
    id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    client_id: int
    issue_date: date
    due_date: date | None = None
    notes: str | None = None
    line_items: list[LineItemIn] = Field(min_length=1)


class InvoiceUpdate(BaseModel):
    issue_date: date | None = None
    due_date: date | None = None
    notes: str | None = None
    line_items: list[LineItemIn] | None = None


class InvoiceListOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    number: str
    status: str
    issue_date: date
    due_date: date | None
    total: Decimal
    view_count: int
    last_viewed_at: datetime | None
    public_token: str | None
    share_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    client_email: str | None = None
    client_address: str | None = None
    number: str
    status: str
    issue_date: date
    due_date: date | None
    notes: str | None
    subtotal: Decimal
    total: Decimal
    public_token: str | None
    share_url: str | None = None
    view_count: int
    last_viewed_at: datetime | None
    sent_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime
    line_items: list[LineItemOut]

    model_config = {"from_attributes": True}


class InvoiceViewOut(BaseModel):
    id: int
    viewed_at: datetime
    user_agent: str | None

    model_config = {"from_attributes": True}


class PublicInvoiceOut(BaseModel):
    number: str
    status: str
    issue_date: date
    due_date: date | None
    notes: str | None
    subtotal: Decimal
    total: Decimal
    client_name: str
    client_email: str | None
    client_address: str | None
    line_items: list[LineItemOut]
    company_name: str
    company_email: str
    company_address: str
    company_phone: str
