# Feature: Dev seeding

Date: 2026-10-17

## What it does

Developers can reset the **crm_dev** database and dev file blobs to a fixed demo dataset so every sidebar area has sample data. Production database `crm` is blocked by a guard.

## Behavior

- Command truncates all application tables except `alembic_version`, clears `FILES_ROOT` for the dev stack (unless `--no-files`), then runs the seed registry in order.
- Seed staff passwords are **reset** to `SEED_PASSWORD` (unlike API startup, which only creates missing users).
- Two teams: `M2 Solution` (main demo data) and `Demo Client Co` (team switcher).
- Stable public sent invoice token: `dev-demo-invoice-public-token` → `{DEV_PUBLIC_APP_URL}/i/dev-demo-invoice-public-token`
- API startup still runs idempotent `seed_staff()` only; full demo data is **not** loaded on every boot.

## API

No HTTP API. CLI:

| Command | Where | Notes |
| ------- | ----- | ----- |
| `python -m app.seeds` | Dev API container / local `backend/` with `DATABASE_URL` → `crm_dev` | Full reseed |
| `./scripts/dev-reseed.sh` | Repo root | Compose wrapper |
| `python -m app.seeds --dry-run` | Same | Guard check only |
| `python -m app.seeds --no-files` | Same | Skip blob wipe |

## UI

After reseed, log in with the first `SEED_EMAIL` address and `SEED_PASSWORD` (defaults in [run.md](../run.md)). Explore:

- **Clients** — Acme Workshop, Northwind Labs, Contoso Retail
- **Meetings** — markdown and plain notes
- **Invoices** — draft, sent (public link above), paid, void
- **Expenses** — categories, two rows, one recurrence
- **Files** — team `configs/README.md`, personal `dev-notes.txt`
- **Projects** — Website refresh (manual + finished timer), Internal tooling (running timer)
- **Accounting** — amounts dated in the current calendar year

## Files

- `backend/app/seeds/` — registry, wipe, demo modules, `cli.py`
- `backend/scripts_dev_reseed.py` — local entrypoint
- `backend/scripts_test_dev_reseed.py` — automated check (runs only on `crm_dev`)
- `scripts/dev-reseed.sh`
- `.cursor/rules/seed-development-data.mdc`

## Follow-ups / out of scope

- Reseeding production `crm`
- Revoking JWTs on reseed (sign out manually)
