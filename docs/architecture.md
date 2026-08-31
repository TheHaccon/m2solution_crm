# Architecture

## Stack

| Layer | Choice |
| ----- | ------ |
| Frontend | Vite, React, TypeScript (`.tsx`), Tailwind, React Router |
| Backend | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 (`DATABASE_URL`) |
| Auth | JWT for **staff only** (bcrypt passwords) |
| Run | Two Compose projects: prod (`crm`: `db` + `db-replica` + nginx + API) and dev (`crm-dev`: Vite + API reload). One Postgres instance, databases `crm` and `crm_dev`. Or local Vite + uvicorn |

## Repo layout

```
backend/          FastAPI app, Alembic, Dockerfile
frontend/         React SPA, nginx.conf, Dockerfile
docs/             Product and feature docs (required for every feature)
scripts/          SQLite→Postgres copy, replication enable, failover, replica status
deploy/postgres/  Replica container entrypoint, ensure-extra-db.sh
deploy/systemd/   Hourly replica health check units
docker-compose.yml
docker-compose.dev.yml
```

Frontend calls `/api/...`. In Vite (dev Compose or local) this is proxied to the API. In prod Docker, nginx on the `web` service proxies `/api/` to the `api` service. Public traffic hits `https://crm.m2solution.ca` on the VPS, which tunnels to this host’s port 8080.

## Data model

- `users` — staff accounts
- `clients` — companies/people you bill and meet
- `invoices` — number, status (`draft` / `sent` / `paid` / `void`), totals, `public_token`, `view_count`, `last_viewed_at`
- `invoice_line_items` — description, qty, rate, amount
- `invoice_views` — each counted public open (cookie/viewer id, time, user-agent)
- `meetings` — title, datetime, attendees, markdown body, linked to a client

Tables are created on API startup (`Base.metadata.create_all`). Alembic migration `001_initial` matches this schema.

## Auth and access

- Staff APIs require `Authorization: Bearer <jwt>`.
- `GET /api/public/invoices/{token}` is unauthenticated. Lookup is by unguessable `public_token`, never by sequential invoice number.
- Draft and void invoices are not visible on the public URL (`sent` and `paid` only).

## Environment (backend)

| Variable | Role |
| -------- | ---- |
| `DATABASE_URL` | SQLAlchemy URL (`postgresql+psycopg://crm:…@db:5432/crm` prod, `…/crm_dev` Compose dev; from the host `127.0.0.1:5432`) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Compose `db` bootstrap (repo-root `.env`). `POSTGRES_DB` is the prod database (`crm`) |
| `DEV_POSTGRES_DB` | Second database on the same instance for the dev stack (`crm_dev`) |
| `REPLICATION_PASSWORD` | Streaming replica user `replicator` |
| `PGDATA_PRIMARY` / `PGDATA_REPLICA` | Host paths for the Postgres cluster (all databases) |
| `SECRET_KEY` | JWT signing |
| `PUBLIC_APP_URL` | Prod origin for share links (`https://crm.m2solution.ca/i/{token}`) |
| `CORS_ORIGINS` | Prod browser origins |
| `DEV_PUBLIC_APP_URL` / `DEV_CORS_ORIGINS` | Dev stack only (`http://localhost:5173`) |
| `PROD_WEB_PUBLISH` | Optional prod `web` publish address (default `8080`) |
| `SEED_EMAIL` / `SEED_PASSWORD` | First staff user created if missing (per database) |
| `COMPANY_*` | Name, email, address, phone on the public invoice |

Defaults live in `backend/app/core/config.py`, `.env.example`, and `backend/.env.example`. Prod cluster files: `/mnt/data_main/m2solution_crm/pgdata` (primary) and `/mnt/data_backup/m2solution_crm/pgdata` (standby). Failover: [features/backups.md](features/backups.md). How to run both stacks: [run.md](run.md).
