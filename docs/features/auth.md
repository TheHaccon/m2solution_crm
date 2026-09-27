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
- Signed-in `admin@m2solution.com` can reset any staff password (including their own) from account settings. Privilege is that literal email, not `SEED_EMAIL`. Unknown target email returns 404. New password must differ from the current hash (400). Existing JWTs stay valid until expiry.

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| POST | `/api/auth/login` | none | JSON `{ email, password }` → `{ access_token }` |
| GET | `/api/auth/me` | staff | Current user |
| POST | `/api/auth/admin/password-reset` | staff (`admin@m2solution.com` only) | JSON `{ email, new_password }` — 204; others 403; unknown email 404 |

## UI

- `/login` — staff sign-in
- Sidebar: click your name for account settings (team, **Dark mode**, manage teams, **Sign out**)
- Account menu shows **Reset staff password** only when the signed-in email is `admin@m2solution.com` (target email, new password, confirm)

## Files

- `backend/app/api/auth.py`
- `backend/app/schemas/auth.py`
- `backend/app/core/security.py`, `deps.py`
- `backend/app/models/user.py`
- `frontend/src/auth/AuthContext.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/layouts/StaffLayout.tsx`

## Follow-ups / out of scope

No email/forgot-password reset, invites, or roles beyond “staff”. This feature does not create `admin@m2solution.com` or change the seeder.
