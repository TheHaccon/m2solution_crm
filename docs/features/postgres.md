# Feature: Postgres

Date: 2026-08-31

## What it does

Staff CRM data lives in PostgreSQL 16. The cluster is a **shared host service** ([shared-postgres.md](shared-postgres.md)), not part of the CRM Compose file. CRM prod uses database `crm`; CRM dev uses `crm_dev` on the same instance.

## Behavior

- **Cluster:** `docker-compose.db.yml` (project `shared-db`). Config in `postgres.env`.
- Primary on `127.0.0.1`, `192.168.2.99`, and `10.50.0.2` port 5432. Standby on `127.0.0.1:5433`.
- **CRM prod** (`crm`): `DATABASE_URL` → `@db:5432/crm` via external network `shared-db`.
- **CRM dev** (`crm-dev`): `@db:5432/crm_dev`.
- `db-init` creates `POSTGRES_EXTRA_DATABASES` (includes `crm_dev` by default).
- Tables created on API startup (`Base.metadata.create_all`) plus seed users/team per database. Existing DBs need Alembic migrations.
- Staff file **contents** are on disk (`FILES_ROOT`); only `file_nodes` metadata is in Postgres.

### One-shot SQLite copy

```bash
docker compose -f docker-compose.db.yml up -d db
docker compose run --rm --no-deps \
  -v m2solution_crm_crm-data:/sqlite:ro \
  -v /srv/m2solution_crm/scripts:/scripts:ro \
  -e SOURCE_DATABASE_URL=sqlite:////sqlite/crm.db \
  api python /scripts/migrate_sqlite_to_postgres.py
```

## API

No new business API. Health: `GET /api/health` (CRM API). DB: Compose `pg_isready`.

## UI

Unchanged.

## Files

- `docker-compose.db.yml`, `postgres.env.example`
- `docker-compose.yml`, `docker-compose.dev.yml`
- `deploy/postgres/ensure-databases.sh`, `deploy/postgres/configure-pg-access.sh`
- `.env.example`, `backend/.env.example`
- `backend/app/core/config.py`, `backend/app/core/database.py`

## Follow-ups / out of scope

- Removing old SQLite volume `m2solution_crm_crm-data` after migration
