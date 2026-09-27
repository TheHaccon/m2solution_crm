# Feature: Staff auth

Date: 2026-08-31

## What it does

Staff sign in with email and password, or with Google when the Google OAuth client is configured. Both paths issue the same staff JWT. There are no client accounts.

## Behavior

- First API start creates a seed staff user if that email is missing (`SEED_EMAIL` / `SEED_PASSWORD`), plus a default team `M2 Solution` and membership.
- Invalid credentials return 401.
- Frontend stores the token in `localStorage` and sends `Authorization: Bearer …`.
- Frontend stores the active team in `localStorage` (`m2_team_id`) and sends `X-Team-Id` on staff API calls (not auth or public invoices).
- Unauthenticated staff routes redirect to `/login`.
- Login email must be a real-looking address (`.local` is rejected by the validator).
- Signed-in `admin@m2solution.com` can reset any staff password (including their own) from account settings. Privilege is that literal email, not `SEED_EMAIL`. Unknown target email returns 404. New password must differ from the current hash (400). Existing JWTs stay valid until expiry.
- **Google sign-in** uses the authorization-code flow (backend holds `GOOGLE_CLIENT_SECRET`). The API trusts only a Google email with `email_verified` true, looks up `users.email` (case-insensitive, same as password login), and issues a JWT for that existing row. Unknown or unverified emails fail generically; the API never creates a user or team membership. Password login stays available as a fallback.
- If `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, or `GOOGLE_REDIRECT_URI` is empty, `GET /api/auth/google/start` returns 503. The operator must create an OAuth client in Google Cloud; the app does not invent credentials.

## API

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| POST | `/api/auth/login` | none | JSON `{ email, password }` → `{ access_token }` |
| GET | `/api/auth/me` | staff | Current user |
| POST | `/api/auth/admin/password-reset` | staff (`admin@m2solution.com` only) | JSON `{ email, new_password }` — 204; others 403; unknown email 404 |
| GET | `/api/auth/google/start` | none | Redirects to Google authorize URL (CSRF `state`); 503 if Google env unset |
| GET | `/api/auth/google/callback` | none | Google redirect; validates `state`, exchanges `code`, matches staff email → redirect to `{PUBLIC_APP_URL}/login?google_token=…` or `?google_error=1` |

## UI

- `/login` — staff sign-in (email/password form plus **Sign in with Google**)
- After Google returns, LoginPage consumes `google_token` (or shows a generic error for `google_error`), stores the JWT, loads `/api/auth/me`, then goes to the dashboard
- Sidebar: click your name for account settings (team, **Dark mode**, manage teams, **Sign out**)
- Account menu shows **Reset staff password** only when the signed-in email is `admin@m2solution.com` (target email, new password, confirm)
- No “connect a different Google account” or email-change UI; public invoice links stay unauthenticated

## Files

- `backend/app/api/auth.py`
- `backend/app/schemas/auth.py`
- `backend/app/core/security.py`, `deps.py`, `config.py`
- `backend/app/models/user.py`
- `frontend/src/auth/AuthContext.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/layouts/StaffLayout.tsx`

## Follow-ups / out of scope

No email/forgot-password reset, invites, or roles beyond “staff”. No Microsoft/Apple, no user creation from Google, no account-linking table. This feature does not create `admin@m2solution.com` or change the seeder.
