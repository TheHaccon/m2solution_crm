# Feature: Staff dashboard

Date: 2026-08-31

## What it does

Home screen after login: unpaid totals, draft/paid counts, recent invoices, recent meetings, recent public invoice views.

Invoice numbers are **yours only**. Recent meetings are for the **active team**.

## Behavior

- **Unpaid** = invoices in status `sent` (awaiting staff to mark paid). Count and CAD total. Only the current user's invoices.
- Recent lists are small (invoices 8, meetings 6, views 8). Meetings filtered by `X-Team-Id`.

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/dashboard` | staff | Requires `X-Team-Id` |

## UI

- `/dashboard` (also `/` redirects here)

## Files

- `backend/app/api/dashboard.py`
- `frontend/src/pages/DashboardPage.tsx`

## Follow-ups / out of scope

No charts, date-range reports, or AR aging beyond this snapshot.
