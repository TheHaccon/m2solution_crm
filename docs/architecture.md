# Architecture

## Stack

| Layer | Choice |
| ----- | ------ |
| Frontend | Vite, React, TypeScript (`.tsx`), Tailwind, React Router |
| Backend | FastAPI, SQLAlchemy 2, Alembic, SQLite (Postgres-ready via `DATABASE_URL`) |
| Auth | JWT for **staff only** (bcrypt passwords) |
| Run | Docker Compose (nginx + API) or local Vite + uvicorn |

## Repo layout

```
backend/          FastAPI app, Alembic, Dockerfile
frontend/         React SPA, nginx.conf, Dockerfile
docs/             Product and feature docs (required for every feature)
docker-compose.yml
docker-compose.dev.yml
```

Frontend calls `/api/...`. In local Vite this is proxied to `http://127.0.0.1:8000`. In Docker, nginx on the `web` service proxies `/api/` to the `api` service.

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
| `DATABASE_URL` | SQLAlchemy URL (`sqlite:///./crm.db` local, `sqlite:////data/crm.db` in Docker) |
| `SECRET_KEY` | JWT signing |
| `PUBLIC_APP_URL` | Origin used when building share links (`…/i/{token}`) |
| `CORS_ORIGINS` | Comma-separated browser origins |
| `SEED_EMAIL` / `SEED_PASSWORD` | First staff user created if missing |
| `COMPANY_*` | Name, email, address, phone on the public invoice |

Defaults live in `backend/app/core/config.py` and `backend/.env.example`.
