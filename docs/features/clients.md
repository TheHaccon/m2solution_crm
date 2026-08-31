# Feature: Clients

Date: 2026-08-31

## What it does

Staff CRUD for companies/people you bill and meet with.

## Behavior

- List with optional search on name/email (`?q=`).
- Detail page shows contact info, invoices, and meetings.
- Delete removes the client and cascaded invoices/meetings.
- Invoice and meeting create can be started from the client (`?clientId=`).

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/clients` | staff | Optional `q` |
| POST | `/api/clients` | staff | |
| GET | `/api/clients/{id}` | staff | |
| PATCH | `/api/clients/{id}` | staff | |
| DELETE | `/api/clients/{id}` | staff | 204 |

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
