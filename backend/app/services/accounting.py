from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import extract, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.expense import Expense
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas.accounting import (
    AccountingClientRow,
    AccountingExpenseCategoryRow,
    AccountingExpenseRow,
    AccountingInvoiceRow,
    AccountingMonthRow,
    AccountingOut,
)
from app.services.expenses import materialize_recurrences


def _utc_year(value: datetime | None) -> int | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).year
    return value.year


def _utc_month(value: datetime | None) -> int | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).month
    return value.month


def available_years(db: Session, user: User) -> list[int]:
    current = date.today().year
    years = {current}
    issue_years = db.scalars(
        select(extract("year", Invoice.issue_date))
        .where(
            Invoice.created_by_id == user.id,
            Invoice.status.in_((InvoiceStatus.sent.value, InvoiceStatus.paid.value)),
        )
        .distinct()
    ).all()
    years.update(int(y) for y in issue_years if y is not None)
    paid_years = db.scalars(
        select(extract("year", Invoice.paid_at))
        .where(Invoice.created_by_id == user.id, Invoice.status == InvoiceStatus.paid.value, Invoice.paid_at.is_not(None))
        .distinct()
    ).all()
    years.update(int(y) for y in paid_years if y is not None)
    expense_years = db.scalars(
        select(extract("year", Expense.spent_on)).where(Expense.created_by_id == user.id).distinct()
    ).all()
    years.update(int(y) for y in expense_years if y is not None)
    return sorted(years, reverse=True)


def _in_register(invoice: Invoice, year: int) -> bool:
    billed = invoice.status in (InvoiceStatus.sent.value, InvoiceStatus.paid.value) and invoice.issue_date.year == year
    collected = invoice.status == InvoiceStatus.paid.value and _utc_year(invoice.paid_at) == year
    return billed or collected


def build_accounting(db: Session, user: User, year: int) -> AccountingOut:
    materialize_recurrences(db, user)
    invoices = list(
        db.scalars(
            select(Invoice)
            .options(selectinload(Invoice.client))
            .where(
                Invoice.created_by_id == user.id,
                Invoice.status.in_((InvoiceStatus.sent.value, InvoiceStatus.paid.value)),
                or_(
                    extract("year", Invoice.issue_date) == year,
                    extract("year", Invoice.paid_at) == year,
                ),
            )
            .order_by(Invoice.issue_date.desc(), Invoice.number.desc())
        ).all()
    )
    register = [inv for inv in invoices if _in_register(inv, year)]

    billed = Decimal("0.00")
    collected = Decimal("0.00")
    outstanding = Decimal("0.00")
    per_client: dict[int, AccountingClientRow] = {}
    monthly = [
        AccountingMonthRow(month=m, revenue=Decimal("0.00"), expenses=Decimal("0.00")) for m in range(1, 13)
    ]

    def row_for(inv: Invoice) -> AccountingClientRow:
        existing = per_client.get(inv.client_id)
        if existing is None:
            existing = AccountingClientRow(
                client_id=inv.client_id,
                client_name=inv.client.name,
                billed_total=Decimal("0.00"),
                collected_total=Decimal("0.00"),
                outstanding_total=Decimal("0.00"),
                invoice_count=0,
            )
            per_client[inv.client_id] = existing
        return existing

    seen: set[int] = set()
    for inv in register:
        client_row = row_for(inv)
        if inv.id not in seen:
            client_row.invoice_count += 1
            seen.add(inv.id)
        total = Decimal(inv.total)
        if inv.status in (InvoiceStatus.sent.value, InvoiceStatus.paid.value) and inv.issue_date.year == year:
            billed += total
            client_row.billed_total += total
        if inv.status == InvoiceStatus.sent.value and inv.issue_date.year == year:
            outstanding += total
            client_row.outstanding_total += total
        if inv.status == InvoiceStatus.paid.value and _utc_year(inv.paid_at) == year:
            collected += total
            client_row.collected_total += total
            month = _utc_month(inv.paid_at)
            if month:
                monthly[month - 1].revenue += total

    year_expenses = list(
        db.scalars(
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.created_by_id == user.id, extract("year", Expense.spent_on) == year)
            .order_by(Expense.spent_on.desc(), Expense.id.desc())
        ).all()
    )
    expense_total = Decimal("0.00")
    per_cat: dict[int, AccountingExpenseCategoryRow] = {}
    for exp in year_expenses:
        amount = Decimal(exp.amount)
        expense_total += amount
        monthly[exp.spent_on.month - 1].expenses += amount
        cat = per_cat.get(exp.category_id)
        if cat is None:
            cat = AccountingExpenseCategoryRow(
                category_id=exp.category_id,
                category_name=exp.category.name,
                total=Decimal("0.00"),
                expense_count=0,
            )
            per_cat[exp.category_id] = cat
        cat.total += amount
        cat.expense_count += 1

    by_client = sorted(per_client.values(), key=lambda row: row.client_name.lower())
    by_category = sorted(per_cat.values(), key=lambda row: row.category_name.lower())
    return AccountingOut(
        year=year,
        years=available_years(db, user),
        billed_total=billed,
        collected_total=collected,
        outstanding_total=outstanding,
        invoice_count=len(register),
        expense_total=expense_total,
        net_collected=collected - expense_total,
        by_client=by_client,
        invoices=[
            AccountingInvoiceRow(
                id=inv.id,
                number=inv.number,
                client_id=inv.client_id,
                client_name=inv.client.name,
                issue_date=inv.issue_date,
                paid_at=inv.paid_at,
                status=inv.status,
                total=inv.total,
            )
            for inv in register
        ],
        by_expense_category=by_category,
        expenses=[
            AccountingExpenseRow(
                id=exp.id,
                spent_on=exp.spent_on,
                category_id=exp.category_id,
                category_name=exp.category.name,
                vendor=exp.vendor,
                amount=exp.amount,
                receipt_file_id=exp.receipt_file_id,
            )
            for exp in year_expenses
        ],
        by_month=monthly,
    )
