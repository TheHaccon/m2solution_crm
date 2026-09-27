# Feature: Clients

Date: 2026-08-31

## What it does

Staff CRUD for companies/people you bill and meet with. Records belong to the **active team** and are shared with every member.

## Behavior

- List with optional search on name/email (`?q=`). Scoped to `X-Team-Id`.
- Detail page shows contact info, **your** invoices, and team meetings. Internal notes render as markdown ([markdown.md](markdown.md)).
- Delete removes the client and cascaded meetings plus **your** invoices. Blocked (409) if a teammate still has invoices for this client.
- Invoice and meeting create can be started from the client (`?clientId=`).

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/clients` | staff | Optional `q`; requires `X-Team-Id` |
| POST | `/api/clients` | staff | Assigns `team_id` from header |
| GET | `/api/clients/{id}` | staff | 404 if other team |
| PATCH | `/api/clients/{id}` | staff | |
| DELETE | `/api/clients/{id}` | staff | 204; 409 if teammate invoices |

## UI

- `/clients`, `/clients/new`, `/clients/:id`, `/clients/:id/edit`

## Files

- `backend/app/api/clients.py`
- `backend/app/models/client.py`
- `frontend/src/pages/ClientsListPage.tsx`
- `frontend/src/pages/ClientDetailPage.tsx`
- `frontend/src/pages/ClientFormPage.tsx`

## Follow-ups / out of scope

No contacts-per-company table; one client record is the company/person.
