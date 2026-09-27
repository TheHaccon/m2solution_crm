# Feature: Accounting (annual report)

Date: 2026-09-02

## What it does

Staff year-end view of **your** invoices and **your** deductible expenses (`created_by_id`). Calendar year only. Totals are CAD. There is **no tax** on invoices or expenses in v1.

## Behavior

- **Billed** — invoices `sent` or `paid` whose **issue date** falls in the year. Drafts and void are excluded.
- **Collected** — invoices `paid` whose **`paid_at`** (UTC) falls in the year (cash).
- **Outstanding** — still `sent`, issue date in the year.
- **Expenses** — rows whose **`spent_on`** falls in the year. Recurrences are materialized first (same as the Expenses page).
- **Net collected** — collected minus expenses (can be negative).
- Year picker lists the current calendar year plus any year on your invoices or expenses.
- Invoice register includes any invoice that counts toward billed or collected for that year.
- Expense register lists deductible rows; manage them on `/expenses`.
- Charts: monthly **revenue (collected) vs expenses** bars; **donut** of expenses by category (CAD + %).
- CSV: invoices section, blank line, expenses section. Invoice PDFs stay in Files → Personal → Invoices; receipts in Personal → Expenses → {category}. No report PDF.
- Team switcher does not change the numbers (`X-Team-Id` is ignored).

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/accounting?year=2026` | staff | Totals, by-client, expenses, `by_month`, registers |
| GET | `/api/accounting/export?year=2026` | staff | CSV `text/csv` |

Year defaults to the current calendar year. Values outside 2000–2100 return 400.

## UI

- Sidebar **Accounting** → `/accounting`
- Cards: Billed, Collected, Outstanding, Expenses, Net collected
- Charts, tables by client and expense category, invoice + expense registers, **Export CSV**

## Files

- `backend/app/api/accounting.py`
- `backend/app/models/invoice.py`
- `backend/app/models/expense.py`
- `backend/app/services/accounting.py`
- `frontend/src/pages/AccountingPage.tsx`
- `frontend/src/layouts/StaffLayout.tsx`
- `frontend/src/App.tsx`

## Follow-ups / out of scope

- **Taxes (TPS/TVQ)** on invoices and expenses, then tax columns on this report
- Non-calendar fiscal year, multi-currency, billed series on the chart, Dashboard charts
- General ledger, auto-email to the accountant, report PDF
