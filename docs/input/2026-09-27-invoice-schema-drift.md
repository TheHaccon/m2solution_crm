# Repair drifted invoice and client columns on the live CRM database

## Status
ready-for-github

## Change type
bugfix

## Summary
`GET /api/dashboard` returns 500 because the API filters `invoices.created_by_id` and that column is not in the live `crm` database. Alembic is already stamped at `004_expenses`, so `alembic upgrade head` will not replay `002_teams`, which is the revision that adds the column. `clients.team_id` is missing the same way.

## Motivation
Staff can log in and load teams, then the dashboard fails. Invoice, client, and accounting queries that use these columns will fail the same way.

## Detailed intent
Observed on the running Compose stack (`crm-api-1`, database `crm`) after login:

- `GET /api/auth/login`, `GET /api/auth/me`, and `GET /api/teams` returned 200.
- `GET /api/dashboard` returned 500: `column invoices.created_by_id does not exist` in `backend/app/api/dashboard.py` (`unpaid_count` filter `Invoice.created_by_id == user.id`, user id 2, status `sent`).

Live schema check (read-only):

- `alembic_version` is `004_expenses`.
- `invoices` columns stop at `updated_at`. No `created_by_id`. Invoice row count is 0.
- `clients` has no `team_id`.
- Tables that later revisions and `Base.metadata.create_all` can create are present: `teams`, `team_members`, `file_nodes`, `expense_categories`, `expense_recurrences`, `expenses`.

Expected: dashboard counts and recent invoices load for the signed-in user. The live database matches the Invoice and Client models (`created_by_id`, `team_id`), including the foreign keys and indexes from `002_teams`.

The code in `002_teams` is already correct and idempotent. The defect is that this database never received those alters, while its version row says it did. A new revision should add the missing columns, backfill, and constraints only when they are absent, so `alembic upgrade head` repairs this database and any other stamp-ahead copy.

## Constraints
- Do not hand-edit prod as the delivery. Issue, branch, and pull request still apply.
- Invoice count is 0, so a backfill of `created_by_id` has no rows to assign. `clients.team_id` still needs a backfill to the existing `M2 Solution` team before it can be `NOT NULL`, matching `002_teams`.
- Startup uses `Base.metadata.create_all`. That creates missing tables and does not add columns to tables that already exist. It can hide a skipped migration until an old table is queried.

## Open questions
- Whether `crm_dev` has the same stamp-ahead gap. This capture only inspected `crm`.
- How `alembic_version` reached `004_expenses` without the `002_teams` alters. The symptom is enough to repair; the history is not in the database.

## Risks and criticism
- Re-running `002_teams` by stamping backward can fight tables that already exist (`teams`, `file_nodes`, `expenses`) and is the wrong repair.
- A one-off `ALTER TABLE` on prod would make the dashboard work and would leave the next drifted database broken, because head is already `004_expenses`.
- Leaving `create_all` in startup means a future missing column can ship as a 500 again while new tables look fine.
- `clients.team_id` is not in the traceback. The dashboard dies on the first invoice query. Meetings and client lists will fail as soon as that query is reached.

## Out of scope
- Rewriting invoice ownership or team scoping.
- Data backfill beyond what `002_teams` already does (first user for invoices, default team for clients).
- Changing Google sign-in, files, or expenses behavior.

## Technical plan (draft)
Add an Alembic revision after `004_expenses` that repeats the missing `002_teams` alters with the same existence checks: `clients.team_id` and `invoices.created_by_id`, foreign keys, and indexes. Apply it with `alembic upgrade head` on `crm`. Confirm `GET /api/dashboard` returns 200 for a signed-in staff user.

## Proposed issues (draft)
One bugfix issue: repair live schema drift for `invoices.created_by_id` and `clients.team_id`.

## Raw notes
Trace from `docker compose logs api` on 2026-09-27. SQL parameters: `created_by_id_1=2`, `status_1=sent`.
