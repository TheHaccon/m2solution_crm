# Feature: Docker

Date: 2026-08-31

## What it does

Run the CRM as two Compose projects on the same host: **prod** (public invoices and staff work at `https://crm.m2solution.ca`) and **dev** (hot reload, localhost only, SSH port forward). They share the prod Postgres instance and use different databases.

## Behavior

### Prod — `docker compose up --build -d` (project `crm`)

- `web` on **8080**, `api` not published; nginx proxies `/api/` to `api:8000`.
- `db` Postgres 16 on `127.0.0.1:5432`. `db-replica` on `127.0.0.1:5433`.
- `db-init` creates database `${DEV_POSTGRES_DB}` (default `crm_dev`) if missing. Prod API uses `${POSTGRES_DB}` (default `crm`).
- Cluster files: `${PGDATA_PRIMARY}` (default `/mnt/data_main/m2solution_crm/pgdata`) and `${PGDATA_REPLICA}` (default `/mnt/data_backup/m2solution_crm/pgdata`).
- `PUBLIC_APP_URL` / `CORS_ORIGINS` default to `https://crm.m2solution.ca`.
- `PROD_WEB_PUBLISH` (optional) can restrict 8080, e.g. `10.50.0.2:8080` for WireGuard-only.
- VPS nginx terminates TLS for `crm.m2solution.ca` and proxies to `10.50.0.2:8080`.
- Named network `crm-db` so the dev API can reach hostname `db`.

### Dev — `docker compose -f docker-compose.dev.yml up --build -d` (project `crm-dev`)

- Vite on **`127.0.0.1:5173`**, API reload on **`127.0.0.1:8000`**, `VITE_API_PROXY=http://api:8000`.
- No Postgres service. API uses `crm_dev` on the prod instance (`@db:5432/crm_dev` via external network `crm-db`). Start prod `db` + `db-init` first.
- `DEV_PUBLIC_APP_URL` / `DEV_CORS_ORIGINS` default to `http://localhost:5173` so prod `.env` URLs are not reused.
- Reach it with `ssh -L 5173:127.0.0.1:5173`.

Prod `api` waits until `db` is healthy (`pg_isready`). Prod `web` waits until `api` is healthy (`GET /api/health`). Prod `db-replica` waits until `db` is healthy, then `pg_basebackup` if its data dir is empty.

Both stacks may run together. Credentials still come from repo-root `.env`.

## API

No new business API. Health: `GET /api/health`.

## UI

Same app. Prod is the built SPA behind nginx (same origin as `/api`). Dev is Vite. Share links in each stack use that stack’s `PUBLIC_APP_URL`.

## Files

- `docker-compose.yml` (`name: crm`), `docker-compose.dev.yml` (`name: crm-dev`), `.env.example`
- `deploy/postgres/replica-entrypoint.sh`, `deploy/postgres/ensure-extra-db.sh`
- `backend/Dockerfile`, `backend/.dockerignore`
- `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore`
- `backend/app/main.py` (`/api/health`)
- `frontend/vite.config.ts` (`VITE_API_PROXY`, `host: true`)

## Follow-ups / out of scope

SQLite volume `crm-data` is no longer used. Replica/failover is [backups.md](backups.md) (whole instance, both databases).
