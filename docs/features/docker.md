# Feature: Docker

Date: 2026-08-31

## What it does

Run the CRM as two Compose projects (**prod** and **dev**) plus a separate **shared Postgres** stack. Prod is public at `https://crm.m2solution.ca`; dev is localhost + SSH forward.

## Behavior

### Shared Postgres — `docker compose -f docker-compose.db.yml up -d`

- Project `shared-db`: `db`, `db-replica`, `db-init`.
- Network `shared-db` (hostname `db`). See [shared-postgres.md](shared-postgres.md).
- Start **before** CRM stacks.

### Prod — `docker compose up --build -d` (project `crm`)

- `web` on `10.50.0.2:8081`. `api` on `shared-db` only (not published).
- No Postgres services in this file.
- File blobs: `${FILES_ROOT}` → `/data/files` on `api`.

### Dev — `docker compose -f docker-compose.dev.yml up --build -d` (project `crm-dev`)

- Vite `127.0.0.1:5173`, API `127.0.0.1:8000`.
- Uses `crm_dev` on shared `db` via external network `shared-db`.
- File blobs: `${DEV_FILES_ROOT}`.

CRM `.env` holds app settings; `postgres.env` holds cluster settings. Both need matching `POSTGRES_USER` / `POSTGRES_PASSWORD` for compose interpolation.

## API

No new business API. Health: `GET /api/health`.

## UI

Same app. Prod = built SPA + nginx. Dev = Vite.

## Files

- `docker-compose.db.yml`, `postgres.env.example`
- `docker-compose.yml`, `docker-compose.dev.yml`, `.env.example`
- `deploy/postgres/` scripts
- `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`

## Follow-ups / out of scope

Replica/failover: [backups.md](backups.md). File blobs are not on the replica disk.
