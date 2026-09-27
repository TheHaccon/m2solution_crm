# Delivery: Files, expenses, accounting, auth seeds, shared Postgres

## Status
pr-open

## Links
- Issue(s): #7 — https://github.com/TheHaccon/m2solution_crm/issues/7 · #8 — https://github.com/TheHaccon/m2solution_crm/issues/8 · #9 — https://github.com/TheHaccon/m2solution_crm/issues/9 · #10 — https://github.com/TheHaccon/m2solution_crm/issues/10 · #11 — https://github.com/TheHaccon/m2solution_crm/issues/11 · #12 — https://github.com/TheHaccon/m2solution_crm/issues/12 · #13 — https://github.com/TheHaccon/m2solution_crm/issues/13
- Input doc: docs/input/2026-09-27-files-expenses-accounting.md
- Branch: `feature/files-expenses-accounting`
- PR: https://github.com/TheHaccon/m2solution_crm/pull/14

## Summary
Staff get a Files manager (team + personal spaces), invoice PDFs written into Personal → Invoices, personal expenses with categories/receipts/monthly recurrence, and a calendar-year Accounting report with CSV export. Staff can change their own password; seed defaults are two Gmail accounts with no login prefill. CRM Postgres runs as the shared host cluster (`docker-compose.db.yml` / `shared-db`), not embedded in the CRM compose stacks.

## Changes
### UI
- Sidebar **Files** → `/files` — team + personal folder trees, upload/create/rename/move/delete, preview (text/markdown/images/PDF), 25 MB upload limit (`FilesPage.tsx`).
- Sidebar **Expenses** → `/expenses` — categories, expense CRUD, receipt upload, recurring monthly table (`ExpensesPage.tsx`).
- Sidebar **Accounting** → `/accounting` — year picker, billed/collected/outstanding/expenses/net cards, charts, registers, Export CSV (`AccountingPage.tsx`).
- Account settings: **Change password** (current + new + confirm).
- `/login` — empty email/password fields (no prefill); Google token narrowing fix so frontend build passes.
- Nav wiring in `StaffLayout.tsx` / `App.tsx`.

### API / backend
- **Files** (`/api/files`): list, folders, text, upload, metadata, content GET/PUT, rename/move, delete — staff JWT; team space needs `X-Team-Id`; personal by `owner_id`.
- **Invoice PDFs**: create/edit/send/paid/void (and draft delete) write `{number}.pdf` into Personal → Invoices (`invoice_files` / `invoice_pdf` services).
- **Expenses**: `/api/expense-categories`, `/api/expenses`, `/api/expenses/{id}/receipt`, `/api/expense-recurrences` — personal scope; receipt blobs under Personal → Expenses → {category}.
- **Accounting**: `GET /api/accounting?year=`, `GET /api/accounting/export?year=` — calendar year, CAD, no tax; materializes recurrences first.
- **Auth**: `POST /api/auth/password` (change own); seed emails default to `matcote111@gmail.com` and `mathieu.laureti@gmail.com` (old `admin@m2solution.com` treated as unset). Admin reset still gated on literal `admin@m2solution.com`.

### Data / config / migrations
- Alembic: files + expenses schema (e.g. `003_files`, `004_expenses`).
- `FILES_ROOT` bind mounts; prod/dev use separate host dirs.
- Shared Postgres: `docker-compose.db.yml`, `postgres.env.example`, `scripts/db-compose.sh`; CRM compose attaches to external network `shared-db` (no embedded Postgres services).
- Frontend: `recharts` dependency; nginx routes for new SPA pages.

### Evergreen docs
- `docs/features/file-manager.md`, `expenses.md`, `accounting.md`, `shared-postgres.md` (new/updated).
- `docs/features/auth.md`, `invoices.md`, `docker.md`, `postgres.md`, `backups.md`, `docs/run.md`, `docs/overview.md`, `docs/README.md` feature table.

## Testing
### Automated
- Commands (first pass): crm-dev API curls for files / expenses / accounting / password / invoice PDF / 25 MB limit; google + admin reset scripts; compose / alembic / gitignore checks.
- First-pass result: **FAIL** on `npm run build` (TS2345 `LoginPage` `googleToken`).
- Rework: `docker run … node:20-alpine npm ci && npm run build` exit **0** at commit `d6cbd35`; OpenAPI spot-check auth/files/expenses/accounting; prior API curl pass tip-compatible.
- Result: **pass** after rework.

### Manual
- Browser MCP / Playwright E2E: **not run** (tooling unavailable).
- Source / spot checks for LoginPage empty prefill + auth merge: **pass**.

### What was NOT run
- Production `docker compose up --build` was **not** run (project `crm`).
- Full live Google OAuth (crm-dev returns 503 — `GOOGLE_*` unset).
- Destructive shared-Postgres cutover.
- Browser E2E.

### Tester sign-off
Approved for documenter: **yes**. Honest handoff copied above; do not invent additional runs.

## Screenshots / recordings
- **N/A** (browser MCP / Playwright unavailable)

## Risks / follow-ups
1. Admin password reset still only allows literal `admin@m2solution.com`, which is no longer the seed default — seeded Gmail staff cannot use that UI unless that row exists.
2. Shared Postgres cutover can take prod down if the cluster or `DATABASE_URL` is wrong.
3. Production compose was **not** rebuilt or exercised in this delivery; after ship use `docs/run.md` commands (see after-ship relaunch below).
4. Live Google OAuth still depends on operator-set `GOOGLE_*` (unchanged from prior batch).

### After-ship relaunch (exact)
```bash
# assumes shared-db already up (else: ./scripts/db-compose.sh up -d)
docker compose up --build -d
# optional: docker compose exec api alembic upgrade head
# optional refresh: docker compose -f docker-compose.dev.yml up --build -d
```

## GitHub — commit (for Orchestrator or explicit user request)
### Subject
Document delivery for files, expenses, accounting batch (#7–#13).

### Body
Add delivery report and update active-slice manifest for the feature batch PR.

## GitHub — pull request
### Title
Add files, expenses, accounting, auth seeds, and shared Postgres (#7–#13)

### Body
(see opened PR — Summary, Test plan, Closes #7–#13, raised risks, after-ship relaunch)

## Ship checklist (awaiting user approval)
- [x] Push branch `feature/files-expenses-accounting` to origin
- [x] Open PR #14 ready for review (not draft)
- [ ] Review PR diff and Tester notes
- [ ] Acknowledge risks: admin reset email gate (`admin@m2solution.com` only); shared-Postgres cutover can take prod down
- [ ] After merge: rebuild prod per `docs/run.md` — production compose was **not** rebuilt in this delivery
- [ ] Explicit merge approval — merge PR #14 into `main` (`Closes #7`–`#13`)
- [ ] Archive `docs/work/active-slice.yaml` after merge

Do **not** merge until the user approves this checklist.
