# Feature: Staff auth

Date: 2026-08-31

## What it does

Staff sign in with email and password and receive a JWT. There are no client accounts.

## Behavior

- First API start creates a seed staff user if that email is missing (`SEED_EMAIL` / `SEED_PASSWORD`), plus a default team `M2 Solution` and membership.
- Invalid credentials return 401.
- Frontend stores the token in `localStorage` and sends `Authorization: Bearer …`.
- Frontend stores the active team in `localStorage` (`m2_team_id`) and sends `X-Team-Id` on staff API calls (not auth or public invoices).
- Unauthenticated staff routes redirect to `/login`.
- Login email must be a real-looking address (`.local` is rejected by the validator).

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| POST | `/api/auth/login` | none | JSON `{ email, password }` → `{ access_token }` |
| GET | `/api/auth/me` | staff | Current user |

## UI

- `/login` — staff sign-in
- Sidebar: click your name for account settings (team, **Dark mode**, manage teams, **Sign out**)

## Files

- `backend/app/api/auth.py`
- `backend/app/core/security.py`, `deps.py`
- `backend/app/models/user.py`
- `frontend/src/auth/AuthContext.tsx`
- `frontend/src/pages/LoginPage.tsx`

## Follow-ups / out of scope

No password reset, invites, or roles beyond “staff”.
