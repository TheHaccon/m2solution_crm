# Feature: Docker

Date: 2026-08-31

## What it does

Run the CRM as containers. Production-style Compose serves the built SPA behind nginx and proxies `/api` to FastAPI so cookies and share links stay same-origin.

## Behavior

- `docker compose up --build` — `web` on **8080**, `api` not published; nginx proxies `/api/` to `api:8000`.
- SQLite at `/data/crm.db` on volume `crm-data`.
- API health: `GET /api/health`. `web` waits until `api` is healthy.
- `docker-compose.dev.yml` — Vite with hot reload on 5173, API reload on 8000, `VITE_API_PROXY=http://api:8000`.
- Share links use `PUBLIC_APP_URL` (default `http://localhost:8080` in the main Compose file).

## API

No new business API. Health: `GET /api/health`.

## UI

Same app, different origin/port depending on compose file.

## Files

- `docker-compose.yml`, `docker-compose.dev.yml`
- `backend/Dockerfile`, `backend/.dockerignore`
- `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore`
- `backend/app/main.py` (`/api/health`)
- `frontend/vite.config.ts` (`VITE_API_PROXY`, `host: true`)

## Follow-ups / out of scope

Images were not built on the authoring machine while Docker Desktop was stopped. Postgres in Compose is not wired yet; SQLite volume is v1.
