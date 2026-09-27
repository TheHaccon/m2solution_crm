# Delivery: Staff Google sign-in

## Status
merged

## Links
- Issue(s): #3 — https://github.com/TheHaccon/m2solution_crm/issues/3 · #4 — https://github.com/TheHaccon/m2solution_crm/issues/4 · #5 — https://github.com/TheHaccon/m2solution_crm/issues/5
- Input doc: docs/input/2026-09-27-google-sign-in.md
- Branch: `feature/google-sign-in`
- PR: https://github.com/TheHaccon/m2solution_crm/pull/6

## Summary
Staff can sign in with email/password or with Google. Google uses the authorization-code flow on the backend (client secret stays server-side). A verified Google email that already matches an existing `users` row gets the same staff JWT as password login; unknown or unverified emails fail without creating accounts. Password login remains the fallback. Operators must set `GOOGLE_*` env vars from a Google Cloud OAuth client before the button works.

## Changes
### UI
- `/login` keeps the email/password form and adds **Sign in with Google** (`frontend/src/pages/LoginPage.tsx`).
- Button navigates to `GET /api/auth/google/start`.
- After callback, LoginPage reads `google_token` (stores JWT, loads `/api/auth/me`, goes to dashboard) or shows a generic error for `google_error`.
- `AuthContext` / layout unchanged for session shape; public invoice routes stay unauthenticated.

### API / backend
- `GET /api/auth/google/start` — redirects to Google authorize URL with CSRF `state`; **503** if `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` unset.
- `GET /api/auth/google/callback` — validates `state`, exchanges `code` for tokens, requires `email_verified`, case-insensitive email match on `users`, redirects to `{PUBLIC_APP_URL}/login?google_token=…` or `?google_error=1`. Never creates a user.
- Password `POST /api/auth/login` unchanged.
- Helpers: `create_google_oauth_state` / `verify_google_oauth_state` in `security.py`; settings in `config.py`.
- Files: `backend/app/api/auth.py`, `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/schemas/auth.py`.

### Data / config / migrations
- Env: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` (plus existing `PUBLIC_APP_URL`).
- Placeholders in root `.env.example`, `backend/.env.example`; compose files pass through the vars.
- **No** schema migration; no user-creation or account-linking table.

### Evergreen docs
- `docs/features/auth.md` — Google flow, API rows, UI notes.
- `docs/run.md` — operator Google Cloud / env setup.
- `docs/architecture.md` — auth/env notes.

## Testing
### Automated
- Commands: `python scripts_test_google_sign_in.py` against commit `fd4758a`.
- Result: **pass**
- Covered: match → JWT; unknown email → error, no user create; unverified email / bad state fail; password login still works; missing Google config → 503.

### Manual
- Steps: live Google OAuth end-to-end with real `GOOGLE_*` credentials; browser screenshot of login UI.
- Result: live OAuth **not proven** (no `GOOGLE_*` credentials in the test env). Password form + **Sign in with Google** verified via source / Vite-served module. Browser MCP / Playwright unavailable (no screenshot).

### Acceptance criteria (Tester)

| Criterion | Result |
| --------- | ------ |
| Existing staff email match → same JWT shape as password login | PASS |
| Unknown Google email → error, no user create | PASS |
| Unverified email / bad OAuth state fail | PASS |
| Password login still works | PASS |
| Missing Google config → 503 on start | PASS |
| Public invoices remain unauthenticated | PASS |
| Docs / env placeholders present | PASS |
| Live Google OAuth E2E | **not run** (no credentials) |
| Browser UI screenshot | **not run** (MCP/Playwright unavailable) |

### Tester sign-off
Overall **PASS** on `fd4758a`. Automated suite passed. Live Google OAuth not proven. UI confirmed via source/Vite module, not browser capture. Dirty `/srv/m2solution_crm` workspace left untouched.

## Screenshots / recordings
- **N/A** (browser MCP / Playwright unavailable)

## Risks / follow-ups
- Feature cannot succeed in production until an operator creates a Google Cloud OAuth client and sets `GOOGLE_*` + redirect URIs (prod `https://crm.m2solution.ca` and dev origin).
- Mis-set redirect URI or secret makes the button fail even when the email would match.
- If Google changes the account email, Google sign-in fails until `users.email` is updated (no in-app email change).
- Existing JWTs are not revoked by this change (by design).

## GitHub — commit (for Orchestrator or explicit user request)
### Subject
Document delivery for Google staff sign-in batch.

### Body
Add delivery report and update active-slice manifest for issues #3 #4 #5.

## GitHub — pull request
### Title
Add Google OAuth staff sign-in matching existing emails

### Body
## Summary
- Authorization-code Google OAuth on the backend (client secret server-side): `GET /api/auth/google/start` + `/callback`.
- Verified Google email must already match a staff `users` row (case-insensitive); issues the same JWT as password login. Unknown emails fail with no user create.
- `/login` adds **Sign in with Google** beside the existing password form.
- Env placeholders and operator docs for Google Cloud OAuth setup (`GOOGLE_*`, redirect URIs). Password login kept as fallback.

## Test plan
- [x] `python scripts_test_google_sign_in.py` on `fd4758a` — match→JWT, unknown→error no create, unverified/bad state fail, password login, missing config 503
- [x] Public invoices remain unauthenticated; docs/env placeholders OK
- [ ] Live Google OAuth end-to-end after operator sets `GOOGLE_*` (not run in Tester env — no credentials)
- [ ] Manual browser: confirm **Sign in with Google** + password form on `/login` (source-verified; no MCP screenshot)
- [ ] Confirm password login still works in a shared env after merge

## Linked issues
Closes #3
Closes #4
Closes #5

## Ship checklist (awaiting user approval)
- [x] Push branch `feature/google-sign-in` to origin
- [x] Open PR ready for review
- [ ] Review PR diff and Tester notes
- [ ] Operator: create Google Cloud OAuth client and set `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` (and `PUBLIC_APP_URL`) before enabling Google sign-in in any env
- [ ] Confirm password login still works after deploy
- [ ] Explicit merge approval — merge PR into `main` (`Closes #3` `#4` `#5`)
- [ ] Archive `docs/work/active-slice.yaml` after merge

Do **not** merge until the user approves this checklist.
