# Feature: Postgres

Date: 2026-08-31

## What it does

Staff CRM data lives in PostgreSQL 16 instead of SQLite. The `db` Compose service is the system of record so later workers and extra services can connect over the Docker network. Cluster files sit on `/mnt/data_main` by default; a streaming replica lives on `/mnt/data_backup` (see [backups.md](backups.md)).

## Behavior

- Compose starts `postgres:16` as `db` (one instance). `api` waits until `pg_isready` succeeds.
- **Prod** (`name: crm`) data directory: `${PGDATA_PRIMARY}` (default `/mnt/data_main/m2solution_crm/pgdata`) bind-mounted to `/var/lib/postgresql/data`. Published `127.0.0.1:5432`. Standby `db-replica` on `${PGDATA_REPLICA}` at `127.0.0.1:5433` (see [backups.md](backups.md)).
- Databases on that instance: `${POSTGRES_DB}` (default `crm`) for prod, `${DEV_POSTGRES_DB}` (default `crm_dev`) for the hot-reload stack. `db-init` runs `deploy/postgres/ensure-extra-db.sh` so `crm_dev` exists even on an already-initialized cluster.
- **Dev** (`name: crm-dev`) has no Postgres container. Its API joins network `crm-db` and uses `postgresql+psycopg://crm:…@db:5432/crm_dev`.
- Prod API `DATABASE_URL` is `postgresql+psycopg://crm:…@db:5432/crm` (password from repo-root `.env`).
- Tables are still created on API startup (`Base.metadata.create_all`) plus the seed staff user and default team (per database). Existing databases need Alembic `002_teams`.
- SQLite `check_same_thread` / `PRAGMA foreign_keys` remain only when `DATABASE_URL` starts with `sqlite`.

### One-shot SQLite copy

If the old Docker volume `m2solution_crm_crm-data` still has `crm.db`:

```bash
docker compose up -d db
docker compose run --rm --no-deps \
  -v m2solution_crm_crm-data:/sqlite:ro \
  -v /srv/m2solution_crm/scripts:/scripts:ro \
  -e SOURCE_DATABASE_URL=sqlite:////sqlite/crm.db \
  api python /scripts/migrate_sqlite_to_postgres.py
```

The script copies `users` → `teams` / members → `clients` → `invoices` → line items / views / `meetings`, then resets serial sequences. Old SQLite dumps without teams get a default team and invoice owners. It **skips** if Postgres already has users (seed already ran).

## API

No new business API. Health: `GET /api/health` (API). DB health is Compose `pg_isready`.

## UI

Unchanged. Staff and public invoice links behave the same.

## Files

- `docker-compose.yml`, `docker-compose.dev.yml`
- `deploy/postgres/ensure-extra-db.sh`
- `.env.example`, `backend/.env.example`
- `backend/app/core/config.py`, `backend/app/core/database.py`
- `backend/requirements.txt` (`psycopg[binary]`), `backend/Dockerfile`
- `backend/alembic.ini`, `backend/alembic/env.py`
- `scripts/migrate_sqlite_to_postgres.py`

## Follow-ups / out of scope

- Removing volume `m2solution_crm_crm-data` after you no longer need the old SQLite file.
