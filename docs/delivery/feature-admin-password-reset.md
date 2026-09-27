# Delivery: Admin-only staff password reset

## Status
ship-prep

## Links
- Issue(s): #1 — https://github.com/TheHaccon/m2solution_crm/issues/1
- Input doc: docs/input/2026-09-27-admin-password-reset.md
- Branch: `feature/admin-password-reset`
- PR: **pending**

## Summary
Signed-in `admin@m2solution.com` can set a new password for any staff account (including their own) from account settings. Authorization is enforced on the API by that literal email; no email is sent and the seeder is unchanged. Existing JWTs remain valid until expiry.

## Changes
### UI
- `frontend/src/layouts/StaffLayout.tsx` — account menu shows **Reset staff password** only when the signed-in email is `admin@m2solution.com` (target email, new password, confirm).

### API / backend
- `POST /api/auth/admin/password-reset` — staff JWT required; only `admin@m2solution.com` allowed.
- Request JSON: `{ email, new_password }` (password length 8–72 via schema).
- Responses: `204` success; `403` non-admin; `404` unknown email; `400` new password same as current hash; `401` unauthenticated; `422` validation.
- Password hashed with existing bcrypt helper in `security.py` (`hash_password` / `verify_password`).
- Files: `backend/app/api/auth.py`, `backend/app/schemas/auth.py`.

### Data / config / migrations
- **None** — no schema migration; `config.py` / seeder / `SEED_*` not changed.

### Evergreen docs
- `docs/features/auth.md` — admin reset behavior, API row, UI note.

## Testing
### Automated
- Commands: `python scripts_test_admin_password_reset.py` against commit `235e4e2` (git archive + TestClient / `crm_dev`).
- Result: **pass**
- Extra checks in the same run: unauthenticated → `401`; validation → `422`; JWT issued before reset still → `200` after reset.

### Manual
- Steps: browser MCP verification of admin-only Reset gating in the account menu.
- Result: **not run** — browser MCP failed. Admin-only Reset gating confirmed via code review of `StaffLayout.tsx` at `235e4e2`.

### Acceptance criteria (Tester)

| Criterion | Result |
| --------- | ------ |
| Admin reset → `204` + login with new password | PASS |
| Non-admin → `403` | PASS |
| Unknown email → `404` | PASS |
| Password length 8–72 | PASS |
| Same password → `400` | PASS |
| Admin self-reset allowed | PASS |
| `config.py` not in feature commit | PASS |
| Old JWT still valid after reset | PASS |

### Tester sign-off
Overall **APPROVE** (Tester handoff on commit `235e4e2`). Automated suite passed; UI gating not browser-verified (code review only).

## Screenshots / recordings
- **N/A** (no browser capture; MCP failed)

## Risks / follow-ups
- After automated tests, `crm_dev` admin password was left as `admin-jwt-1`.
- Test user `apr-other@m2solution.com` was left in the DB.
- Privilege is entirely the literal `admin@m2solution.com` account; lockout of that account is out of scope (break-glass later).
- Existing sessions are not revoked on password reset (by design).

## GitHub — commit (for Orchestrator or explicit user request)
### Subject
Document delivery for admin staff password reset.

### Body
Add delivery report and update active-slice manifest for issue #1.

Closes #1 (via PR).

## GitHub — pull request
### Title
Add admin-only staff password reset

### Body
## Summary
- Staff API `POST /api/auth/admin/password-reset` lets signed-in `admin@m2solution.com` set any staff password (bcrypt via existing `security.py`); `204` / `403` / `404` / `400`.
- Account menu shows **Reset staff password** only for that admin email (`StaffLayout.tsx`).
- Evergreen auth docs updated; automated regression script `backend/scripts_test_admin_password_reset.py` included.
- No seeder / `SEED_*` / `config.py` changes; existing JWTs stay valid until expiry.

## Test plan
- [x] `python scripts_test_admin_password_reset.py` against `235e4e2` (TestClient / `crm_dev`) — pass
- [x] AC: admin reset + login, non-admin 403, unknown 404, length 8–72, same-password 400, admin self-reset, config untouched, old JWT valid
- [ ] Manual browser: admin-only Reset control visible for `admin@m2solution.com`, hidden for other staff (not run — MCP failed; code-reviewed)
- [ ] Spot-check login after a real admin reset in a shared env if desired

## Linked issues
Closes #1

## Ship checklist (awaiting user approval)
- [x] Push branch `feature/admin-password-reset` to origin
- [ ] Mark PR ready for review (opened ready unless noted otherwise)
- [ ] Merge PR into `main` (`Closes #1`)
- [ ] Archive `docs/work/active-slice.yaml` after merge
- [ ] Restore or rotate `crm_dev` admin password if still `admin-jwt-1`; remove leftover `apr-other@m2solution.com` if undesired

Do **not** merge until the user approves this checklist.
