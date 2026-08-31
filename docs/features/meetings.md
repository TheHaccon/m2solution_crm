# Feature: Meeting notes

Date: 2026-08-31

## What it does

Staff record internal notes about meetings with a client (date, attendees, markdown body). Clients never see these.

## Behavior

- Always linked to a `client_id`.
- List is newest `scheduled_at` first; can filter `?client_id=`.
- Detail renders simple markdown (`#` / `##` / `###`, `- ` lists).
- Shown on the client detail page next to invoices.

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/meetings` | staff | Optional `client_id` |
| POST | `/api/meetings` | staff | |
| GET | `/api/meetings/{id}` | staff | |
| PATCH | `/api/meetings/{id}` | staff | |
| DELETE | `/api/meetings/{id}` | staff | 204 |

## UI

- `/meetings`, `/meetings/new`, `/meetings/:id`, `/meetings/:id/edit`

## Files

- `backend/app/api/meetings.py`
- `backend/app/models/meeting.py`
- `frontend/src/pages/MeetingsListPage.tsx`
- `frontend/src/pages/MeetingFormPage.tsx`
- `frontend/src/pages/MeetingDetailPage.tsx`

## Follow-ups / out of scope

No rich-text editor, attachments, or calendar sync.
