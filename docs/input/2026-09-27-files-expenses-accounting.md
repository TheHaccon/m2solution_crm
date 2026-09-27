# Enroll local files, expenses, accounting, and shared Postgres

## Status
ready-for-github

## Change type
feature

## Summary
Enroll the uncommitted working tree so staff can keep files, personal expenses, and a year-end accounting view, and so Postgres runs as a shared host cluster instead of inside the CRM Compose project. Staff can also change their own password, and the API seeds two Gmail staff accounts instead of `admin@m2solution.com`.

The behavior is already implemented in this checkout. These issues exist so that work can be reviewed and merged. They are not a request for a second design.

## Motivation
The CRM today tracks clients, meetings, and invoices. Staff still need a place for configs and uploads, a record of deductible costs with receipts, and a calendar-year view of what was billed, collected, and spent. The database also needs to be a host service other apps can share, with prod and dev databases separated.

## Detailed intent
Staff-only. Public invoice links stay token URLs and do not gain access to files, expenses, or accounting.

**Files.** A Files page with a folder tree. Team space is shared with the active team. Personal space is private to the signed-in user and starts with Invoices and Expenses folders. Invoice PDFs are written into Personal → Invoices. Uploads are capped at 25 MB. Blobs are stored under `FILES_ROOT` by uuid, not by a user-supplied path. Prod and dev use different directories. The Postgres replica does not copy these files.

**Expenses.** Personal deductible costs (not shared via the team switcher). Categories, CAD amounts, a spent-on date, optional monthly recurrence, and one receipt per expense stored under Personal → Expenses → {category}.

**Accounting.** A calendar-year report of the signed-in user's invoices and expenses: billed, collected, outstanding, expenses, and net collected. Charts, registers, and a CSV export. No tax in v1.

**Shared Postgres.** CRM prod and dev no longer run their own Postgres. They join an external Docker network `shared-db` and use hostname `db`. The cluster is `docker-compose.db.yml` (primary, replica, pgweb, declarative extra databases). Prod database is `crm`; dev is `crm_dev`.

**Auth in the same tree.** `POST /api/auth/password` lets the signed-in user change their password after confirming the current one. Seed users default to `matcote111@gmail.com` and `mathieu.laureti@gmail.com`. The login form is not prefilled. Admin password reset stays limited to the literal email `admin@m2solution.com`.

Google sign-in is already shipped (issues #3, #4, #5, pull request #6). Do not create those issues again.

## Constraints
- Do not commit `.env` or `postgres.env`. Examples only (`.env.example`, `postgres.env.example`).
- The working tree is on `feature/admin-password-reset`, which is the wrong branch for this batch. A later implementation branch must carry this diff without dropping it and without pushing it straight to `main`.
- One feature batch, one pull request, after gate 2. This capture does not approve building.
- File and receipt bytes are on the primary data disk (`/mnt/data_main/m2solution_crm/files` in prod). They are not in the database replica.

## Open questions
- Admin password reset still keys off `admin@m2solution.com`, while seed users are the two Gmail addresses. Nothing in this tree creates or renames that admin account. Confirm later whether reset should follow a real staff email.
- Whether the shared-Postgres cutover has already been applied on the host. The Compose files in the tree assume it has. A rebuild against the old embedded Postgres layout would not match this diff.

## Risks and criticism
- This code was written before an issue existed. Review has to judge the current diff, not a fresh implementation that might diverge from it.
- Moving Postgres out of `docker-compose.yml` can take prod down if the shared cluster or `DATABASE_URL` is wrong. That cutover is ops-sensitive and must not be treated as a casual compose rebuild.
- Unknown file ids return 404, including for files the caller must not see. That hides existence and also hides bugs.
- Recurrence catch-up (up to 36 months) runs on read. A first visit can insert many rows.
- Accounting ignores the team header. A user who thinks the year view is team-wide will misread the numbers.
- `admin@m2solution.com` is no longer the seed default, but it remains the only account that can reset passwords. After this ships, password reset may be unreachable unless that user still exists in the database.

## Out of scope
- Google sign-in (already merged).
- Tax (TPS/TVQ) on invoices or expenses.
- Public or client access to files, expenses, or accounting.
- A report PDF. CSV only.
- Changing staff email addresses.
- Rewriting the features that are already in the working tree.

## Technical plan (draft)
Keep the existing modules: file API and storage, expense API and receipt files, accounting API, Alembic `003_files` and `004_expenses`, `docker-compose.db.yml`, and the staff pages `/files`, `/expenses`, `/accounting`. Ship them together because expenses and invoice PDFs write into the file tree, and accounting reads invoices and expenses.

## Raw notes
Gate 1 quote: "Create the GitHub issues" (2026-09-27). Source of truth for behavior is `docs/features/file-manager.md`, `docs/features/expenses.md`, `docs/features/accounting.md`, `docs/features/shared-postgres.md`, and the auth section of `docs/features/auth.md`.
