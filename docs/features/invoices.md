# Feature: Invoices

Date: 2026-08-31

## What it does

Staff create QuickBooks-lite invoices (line items, totals, status). Payment is **not** collected in the app; staff mark paid by hand. Invoices are **personal**: a teammate who shares the client does not see your invoices in the CRM.

## Behavior

- New invoices are **draft**. Line items required. Totals are computed on the server (`qty × unit_price`).
- Numbers are sequential: `INV-{year}-0001`.
- **Send** sets status `sent`, stamps `sent_at`, and creates `public_token` if missing.
- **Mark paid** allowed from `sent` (or already `paid`). Sets `paid_at`.
- **Void** allowed unless already paid. Public link then 404s.
- **Rotate link** issues a new token; the old URL dies. Only for `sent` / `paid`.
- Drafts can be edited or deleted. Sent invoices are not edited in v1 (status actions only).
- Staff viewing an invoice in the CRM does **not** increment view count.
- List/get/update/send/void only succeed for invoices the current user created (`created_by_id`). No `team_id` on invoices.
- The billed client must belong to a team the user is a member of.

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/invoices` | staff | `client_id`, `status` filters |
| POST | `/api/invoices` | staff | Creates draft |
| GET | `/api/invoices/{id}` | staff | Includes `share_url` |
| PATCH | `/api/invoices/{id}` | staff | Draft only |
| DELETE | `/api/invoices/{id}` | staff | Draft only |
| POST | `/api/invoices/{id}/send` | staff | |
| POST | `/api/invoices/{id}/mark-paid` | staff | |
| POST | `/api/invoices/{id}/void` | staff | |
| POST | `/api/invoices/{id}/rotate-link` | staff | |
| GET | `/api/invoices/{id}/views` | staff | View history |

## UI

- `/invoices`, `/invoices/new`, `/invoices/:id`, `/invoices/:id/edit`
- Detail: copy share link, view count, view history, document preview

## Files

- `backend/app/api/invoices.py`
- `backend/app/models/invoice.py`
- `backend/app/services/invoices.py`
- `frontend/src/pages/InvoicesListPage.tsx`
- `frontend/src/pages/InvoiceFormPage.tsx`
- `frontend/src/pages/InvoiceDetailPage.tsx`
- `frontend/src/components/InvoiceDocument.tsx`

## Follow-ups / out of scope

No taxes, estimates, recurring invoices, or email send. Public link + view count: [public-invoice-links.md](public-invoice-links.md).
