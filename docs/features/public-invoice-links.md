# Feature: Public invoice links and view counts

Date: 2026-08-31

## What it does

Staff copy a secret URL and send it themselves. The recipient opens the invoice **without signing in**. Each open is counted so staff can see that the client looked at it.

## Behavior

- URL shape: `{PUBLIC_APP_URL}/i/{public_token}`. Token is a long random string, not `INV-2026-0001`.
- Public GET succeeds only if status is `sent` or `paid`. Missing/draft/void → 404.
- View is recorded on `GET /api/public/invoices/{token}` (not on staff CRM preview).
- Viewer identity: `X-Viewer-Id` header (frontend `localStorage`) or `invoice_viewer` cookie. A new id is set if both are missing.
- Dedup: same viewer + same invoice within **30 seconds** does not add another view (stops refresh spam and React Strict Mode double-fetch).
- Stored: `invoices.view_count`, `invoices.last_viewed_at`, and a row in `invoice_views` (time, hashed IP, user-agent).

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/public/invoices/{token}` | none | Returns invoice + company fields; may `Set-Cookie` |

## UI

- `/i/:token` — standalone document + Print (no CRM chrome)
- Staff invoice page: copy link, rotate link, view history

## Files

- `backend/app/api/public.py`
- `frontend/src/pages/PublicInvoicePage.tsx`
- `frontend/src/components/InvoiceDocument.tsx`

## Follow-ups / out of scope

No email delivery from the app. Link security is “unguessable URL”, not login.
