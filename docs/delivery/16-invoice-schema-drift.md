# Delivery: Repair invoice/client schema drift

## Status
pr-open

## Links
- Issue(s): #16 — https://github.com/TheHaccon/m2solution_crm/issues/16
- Input doc: docs/input/2026-09-27-invoice-schema-drift.md
- Branch: `fix/invoice-schema-drift`
- PR: **pending** (filled after open)
- Tip commit: `b994afd6271249262c082695b5a17be20e6e684c`

## Summary
Live `crm` was Alembic-stamped at `004_expenses` without the `002_teams` column alters, so `GET /api/dashboard` (and other queries) failed with missing `invoices.created_by_id` / `clients.team_id`. This change adds repair revision `005_repair_inv_client_cols` (after `004_expenses`) that adds those columns, FKs, and indexes only when absent, with the same backfill as `002_teams`. It does not stamp backward. Revision id was shortened to 26 characters so it fits Alembic’s `VARCHAR(32)` version column.

## Changes
### UI
- **None** (dashboard and other staff UI already expected these columns; no frontend change).

### API / backend
- **None** to route contracts. Existing staff endpoints that filter or join on `Invoice.created_by_id` / `Client.team_id` (notably `GET /api/dashboard` with `X-Team-Id`) succeed once the schema is repaired.
- File: `backend/alembic/versions/005_repair_inv_client_cols.py` (renamed from `005_repair_invoice_client_columns.py`; revision string shortened for `alembic_version`).

### Data / config / migrations
- New Alembic revision after `004_expenses`:
  - Adds `clients.team_id` (NOT NULL after backfill to default **M2 Solution** team) + FK/index when missing.
  - Adds `invoices.created_by_id` + FK/index when missing (backfill to first user when invoice rows exist; live had 0 invoices).
  - Existence checks so already-correct DBs are a no-op.
  - Does **not** recreate `teams` / `team_members` or stamp backward past `004_expenses`.
- Ops: apply with `alembic upgrade head` on a rebuilt API image (**no bind-mount**); do **not** recreate the Postgres volume.

### Evergreen docs
- `docs/architecture.md` — migration list + stamp-ahead repair note (`005_repair_inv_client_cols`).
- `docs/run.md` — how to apply the repair without recreating the volume.
- `docs/features/teams.md` — points at the repair revision file.
- Input enrolled: `docs/input/2026-09-27-invoice-schema-drift.md`.

## Testing
### Automated
- Commands: none beyond live Alembic + HTTP checks below.
- Result: **not run** as a dedicated unit/integration suite (schema repair verified on live Compose `crm`).

### Manual
- Steps (Tester):
  1. API-only rebuild required (no bind-mount) so the container has the new revision file.
  2. `alembic upgrade head` on live `crm`: `004_expenses` → `005_repair_inv_client_cols`.
  3. Confirm columns + FKs/indexes present.
  4. `GET /api/dashboard` with `X-Team-Id` → **200** (staff `mathieu.laureti@gmail.com`).
  5. Second `alembic upgrade head` → idempotent no-op.
  6. Postgres volume **not** recreated.
- Result: **pass**

### Acceptance criteria (Tester)

| Criterion | Result |
| --------- | ------ |
| After upgrade, `GET /api/dashboard` returns 200 for signed-in staff | PASS |
| Missing columns/FKs/indexes added only when absent; backfill matches `002_teams` | PASS |
| Second upgrade is idempotent no-op | PASS |
| Delivery does not stamp backward / re-run `002_teams` | PASS |
| Postgres volume not recreated | PASS |

### Tester sign-off
Overall **PASS** on tip `b994afd`. Live `crm` was repaired during testing (`alembic_version` = `005_repair_inv_client_cols`). Ops note for ship: production DB is already at head for this revision; merge mainly ships the short revision id + docs so images match what was applied.

## Screenshots / recordings
- **N/A** (API/schema repair; no UI change)

## Risks / follow-ups
- **Live already repaired** during Tester run — merging does not need a second upgrade on that same `crm` volume unless someone rebuilds from an image that still only has the long revision id.
- Commit `660b487` (long revision id `005_repair_invoice_client_columns`, 33 chars) entered `main` ancestry via merge of PR #17 (`fix/google-userinfo`). This PR finishes the rename to `005_repair_inv_client_cols` (26 chars) so images match the version stamped on live and fit `VARCHAR(32)`.
- If another environment was upgraded with the **long** revision id string, operators must align `alembic_version` / image carefully before upgrading again (live Tester path used the short id).
- `crm_dev` was out of scope; check separately if it has the same stamp-ahead gap.
- Startup `create_all` still creates missing tables only — future missing columns can still surface as 500s until a migration exists.

## GitHub — commit (for Orchestrator or explicit user request)
### Subject
Document delivery for invoice schema drift repair (#16).

### Body
Add delivery report and update active-slice manifest for issue #16.

## GitHub — pull request
### Title
Repair missing invoice and client columns on stamp-ahead CRM DBs

### Body
## Summary
- Add Alembic repair revision `005_repair_inv_client_cols` after `004_expenses` for stamp-ahead databases missing `clients.team_id` and `invoices.created_by_id` (existence-checked; same backfill as `002_teams`).
- Does not stamp backward or re-run `002_teams`.
- Shorten revision id to fit Alembic `VARCHAR(32)` (follow-up rename from the too-long first id).
- Evergreen docs: `architecture.md`, `run.md`, `features/teams.md`.

## Test plan
- [x] API-only rebuild (no bind-mount); `alembic upgrade head` on live `crm`: `004_expenses` → `005_repair_inv_client_cols`
- [x] Columns + FKs/indexes present
- [x] `GET /api/dashboard` with `X-Team-Id` → 200 (staff mathieu.laureti@gmail.com)
- [x] Second upgrade idempotent no-op; Postgres volume not recreated
- [ ] Reviewers: confirm other envs (`crm_dev` if used) either already have the columns or run the same upgrade
- [ ] After merge: rebuild API image so revision id on disk matches live stamp (`005_repair_inv_client_cols`)

## Linked issues
Fixes #16

## Ship checklist (awaiting user approval)
- [x] Push branch `fix/invoice-schema-drift` to origin
- [ ] Mark PR ready for review (opened ready)
- [ ] Review PR diff and Tester notes
- [ ] Ops: live `crm` already at `005_repair_inv_client_cols` — no second upgrade needed on that volume; rebuild API from merged main so the short revision file is what images ship
- [ ] Explicit merge approval — merge PR into `main` (`Fixes #16`)
- [ ] Archive `docs/work/active-slice.yaml` after merge

Do **not** merge until the user approves this checklist.

Return to [documentation hub](../README.md) · [Main README](../../README.md)
