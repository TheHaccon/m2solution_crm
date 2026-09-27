from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class AccountingClientRow(BaseModel):
    client_id: int
    client_name: str
    billed_total: Decimal
    collected_total: Decimal
    outstanding_total: Decimal
    invoice_count: int


class AccountingInvoiceRow(BaseModel):
    id: int
    number: str
    client_id: int
    client_name: str
    issue_date: date
    paid_at: datetime | None
    status: str
    total: Decimal


class AccountingExpenseCategoryRow(BaseModel):
    category_id: int
    category_name: str
    total: Decimal
    expense_count: int


class AccountingExpenseRow(BaseModel):
    id: int
    spent_on: date
    category_id: int
    category_name: str
    vendor: str | None
    amount: Decimal
    receipt_file_id: int | None


class AccountingMonthRow(BaseModel):
    month: int
    revenue: Decimal
    expenses: Decimal


class AccountingOut(BaseModel):
    year: int
    years: list[int]
    billed_total: Decimal
    collected_total: Decimal
    outstanding_total: Decimal
    invoice_count: int
    expense_total: Decimal
    net_collected: Decimal
    by_client: list[AccountingClientRow]
    invoices: list[AccountingInvoiceRow]
    by_expense_category: list[AccountingExpenseCategoryRow]
    expenses: list[AccountingExpenseRow]
    by_month: list[AccountingMonthRow]
