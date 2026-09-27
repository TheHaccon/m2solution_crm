# Feature: Expenses

Date: 2026-09-02

## What it does

Staff track **personal** deductible costs (gas, purchases, auto, subscriptions, custom categories). Recurring monthly rows are created when you open Expenses or Accounting. Receipts live in Files → Personal → **Expenses** → **{category}** (for example `Expenses/Gas`).

## Behavior

- Scoped to the signed-in user (`created_by_id`). Team switcher is ignored.
- Default categories on first visit: Gas, Purchase, Auto, Subscription, Other. You can add, rename, or delete unused ones.
- Amount is CAD, `spent_on` is a calendar date. No TPS/TVQ in v1.
- **Repeat monthly** creates a recurrence. Catch-up (max 36 months) runs on `GET/POST` expenses and on Accounting. Future dates are not generated. Pause / resume / delete the recurrence; existing expense rows stay.
- One receipt per expense (max 25 MB), stored under Personal → Expenses → that category’s folder. Replacing overwrites the Files blob. Changing the expense category **moves** the receipt. Renaming a category renames (or merges into) that folder. Deleting the expense removes that receipt file. Deleting the file in Files sets `receipt_file_id` to null.

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET/POST | `/api/expense-categories` | staff | Seed defaults on GET |
| PATCH/DELETE | `/api/expense-categories/{id}` | staff | Delete 409 if in use |
| GET | `/api/expenses?year=&category_id=` | staff | Materializes recurrences |
| POST | `/api/expenses` | staff | `repeat_monthly` optional |
| PATCH/DELETE | `/api/expenses/{id}` | staff | |
| POST | `/api/expenses/{id}/receipt` | staff | Multipart `file` |
| GET | `/api/expense-recurrences` | staff | |
| PATCH/DELETE | `/api/expense-recurrences/{id}` | staff | `active` pauses |

## UI

- Sidebar **Expenses** → `/expenses`
- Year / category filters, create/edit form, receipt upload, recurring table

## Files

- `backend/app/models/expense.py`
- `backend/app/api/expenses.py`
- `backend/app/services/expenses.py`
- `backend/app/services/expense_files.py`
- `backend/app/schemas/expense.py`
- `backend/alembic/versions/004_expenses.py`
- `frontend/src/pages/ExpensesPage.tsx`

## Follow-ups / out of scope

Taxes / CTI, weekly/yearly recurrence, multi-receipts, OCR, bank sync, team expenses, budget vs actual.
