# Architecture

## Stack

| Layer | Choice |
| ----- | ------ |
| Frontend | Vite, React, TypeScript (`.tsx`), Tailwind, React Router |
| Backend | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 (`DATABASE_URL`) |
| Auth | JWT for **staff only** (bcrypt passwords) |
| Run | Three Compose projects: `shared-db` (Postgres), `crm` (prod), `crm-dev` (Vite). Or local Vite + uvicorn against shared Postgres |

## Repo layout

```
backend/          FastAPI app, Alembic, Dockerfile
frontend/         React SPA, nginx.conf, Dockerfile
docs/             Product and feature docs (required for every feature)
scripts/          SQLite→Postgres copy, replication enable, failover, replica status
deploy/postgres/  ensure-databases, configure-pg-access, replica entrypoint
deploy/systemd/   Hourly replica health check units
docker-compose.db.yml
docker-compose.yml
docker-compose.dev.yml
postgres.env.example
```

Frontend calls `/api/...`. In Vite (dev Compose or local) this is proxied to the API. In prod Docker, nginx on the `web` service proxies `/api/` to the `api` service. Public traffic hits `https://crm.m2solution.ca` on the VPS, which tunnels to this host’s `10.50.0.2:8081` (8080 is Wings).

## Data model

- `users` — staff accounts
- `teams` / `team_members` — staff groups; sidebar sets active team via `X-Team-Id`
- `clients` — companies/people you bill and meet; `team_id`
- `invoices` — number, status (`draft` / `sent` / `paid` / `void`), totals, `public_token`, `view_count`, `last_viewed_at`, `created_by_id` (owner; not team-scoped)
- `expense_categories` / `expense_recurrences` / `expenses` — personal deductible costs, optional monthly recurrence, optional receipt `file_nodes` id
- `invoice_line_items` — description, qty, rate, amount
- `invoice_views` — each counted public open (cookie/viewer id, time, user-agent)
- `meetings` — title, datetime, attendees, markdown body, linked to a client (team via that client)
- `file_nodes` — folder/file tree metadata (`space` team or personal); blobs on disk at `FILES_ROOT/<uuid>`, not in Postgres

Tables are created on API startup (`Base.metadata.create_all`). Alembic migrations `001_initial`, `002_teams`, `003_files`, `004_expenses`, and `005_repair_invoice_client_columns` match this schema. On an existing database, run those migrations — `create_all` creates **new tables** but does not add columns. If a database was stamped ahead to `004_expenses` without the `002_teams` column alters (`clients.team_id`, `invoices.created_by_id`), apply `005_repair_invoice_client_columns` via `alembic upgrade head` rather than stamping backward.

## Auth and access

- Staff APIs require `Authorization: Bearer <jwt>`.
- Client, meeting, dashboard, and **team file** routes also require **`X-Team-Id`** and membership.
- Invoice, expense, and accounting staff routes ignore the team header and return only rows where `created_by_id` is the current user.
- Personal files (`/api/files?space=personal`) ignore the team header and return only rows where `owner_id` is the current user.
- `GET /api/public/invoices/{token}` is unauthenticated. Lookup is by unguessable `public_token`, never by sequential invoice number.
- Draft and void invoices are not visible on the public URL (`sent` and `paid` only).

## Environment (backend)

| Variable | Role |
| -------- | ---- |
| `DATABASE_URL` | SQLAlchemy URL (`@db:5432/crm` prod, `…/crm_dev` dev on network `shared-db`; from host `127.0.0.1` / `192.168.2.99` / `10.50.0.2`) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | In `.env` for CRM compose interpolation; cluster paths/passwords also in `postgres.env` |
| `DEV_POSTGRES_DB` | Dev CRM database name (`crm_dev`) |
| `SECRET_KEY` | JWT signing |
| `PUBLIC_APP_URL` | Prod origin for share links (`https://crm.m2solution.ca/i/{token}`) |
| `CORS_ORIGINS` | Prod browser origins |
| `DEV_PUBLIC_APP_URL` / `DEV_CORS_ORIGINS` | Dev stack only (`http://localhost:5173`) |
| `PROD_WEB_PUBLISH` | Prod `web` publish address (default `10.50.0.2:8081`; 8080 is Wings) |
| `SEED_EMAIL` / `SEED_PASSWORD` | Staff users created if missing (per database). `SEED_EMAIL` is comma-separated; default `matcote111@gmail.com,mathieu.laureti@gmail.com`. The old `admin@m2solution.com` value is ignored and the two Gmail accounts are seeded instead |
| `COMPANY_*` | Name, email, address, phone on the public invoice |
| `FILES_ROOT` | Host path for prod file blobs (container `/data/files`). Default `/mnt/data_main/m2solution_crm/files` |
| `DEV_FILES_ROOT` | Host path for dev file blobs. Default `/mnt/data_main/m2solution_crm/files_dev` |
| `FILES_MAX_BYTES` | Upload cap (default 25000000) |

Defaults live in `backend/app/core/config.py`, `.env.example`, `postgres.env.example`, and `backend/.env.example`. Cluster: [features/shared-postgres.md](features/shared-postgres.md). Failover: [features/backups.md](features/backups.md). Run order: [run.md](run.md).
