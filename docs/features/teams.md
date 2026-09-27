# Feature: Teams

Date: 2026-09-01

## What it does

Staff belong to one or more **teams**. Click your name at the bottom of the sidebar to open account settings and pick the active team (`X-Team-Id`). Clients, client notes, and meetings are shared with everyone in that team. **Invoices are personal**: only the staff member who created an invoice can see or change it in the CRM.

## Behavior

- Seed creates a default team named `M2 Solution` and adds the seed staff user.
- Existing clients are assigned to that team; existing invoices are owned by the first staff user.
- Switching team remounts staff pages so clients/meetings/dashboard meetings refetch. The invoices list still shows only the signed-in user's invoices.
- Adding a member requires an **existing** staff email. Creating staff accounts is still seed/DB.
- You cannot remove the last member of a team.
- Deleting a client is blocked (409) if a teammate still has invoices for that client.
- Public invoice links are unchanged: anyone with the token can view, without a team header.

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/api/teams` | staff | Teams the user belongs to. No `X-Team-Id` required |
| POST | `/api/teams` | staff | Creates a team and adds the caller |
| GET | `/api/teams/{id}` | staff | Members; must belong |
| PATCH | `/api/teams/{id}` | staff | Rename |
| POST | `/api/teams/{id}/members` | staff | JSON `{ email }` of an existing user |
| DELETE | `/api/teams/{id}/members/{user_id}` | staff | Leave or remove; not the last member |

Staff client, meeting, and dashboard routes require header **`X-Team-Id`**. Invoice staff routes ignore it and filter by `created_by_id`.

## UI

- Sidebar: click your name → account menu (choose team, dark mode, manage teams, sign out). The active team name is shown under the email.
- `/teams` — create a team, list members, add by email (also linked from that menu)

## Files

- `backend/app/models/team.py`
- `backend/app/api/teams.py`
- `backend/app/core/deps.py`
- `backend/alembic/versions/002_teams.py`
- `frontend/src/team/TeamContext.tsx`
- `frontend/src/pages/TeamsPage.tsx`
- `frontend/src/layouts/StaffLayout.tsx`

## Follow-ups / out of scope

Not multi-company / multi-tenant. No roles inside a team. No creating staff users from the Teams page.
