# Run

Two Compose projects can run at the same time. They share **one Postgres instance** (prod `db` + replica) and use **different databases**: `crm` (prod) and `crm_dev` (dev). Published app ports do not overlap.

| Stack | Compose file | Project | Who uses it |
| ----- | ------------ | ------- | ----------- |
| **Prod** | `docker-compose.yml` | `crm` | Public site `https://crm.m2solution.ca` (VPS nginx → WireGuard `10.50.0.2:8081`) |
| **Dev** | `docker-compose.dev.yml` | `crm-dev` | Staff only, via SSH local forward to Vite |

Seed staff user: `admin@m2solution.com` / `changeme` (override with `SEED_EMAIL` / `SEED_PASSWORD`). Each stack seeds its **own** database (`crm` vs `crm_dev`) and a default team `M2 Solution`.

On an existing database, apply Alembic `002_teams` (adds `teams`, `team_members`, `clients.team_id`, `invoices.created_by_id`). `create_all` will not add those columns.

Copy [`.env.example`](../.env.example) to `.env` and set `SECRET_KEY`, `POSTGRES_PASSWORD`, and `REPLICATION_PASSWORD`. Compose interpolates that file automatically. Prod share links use `PUBLIC_APP_URL`; dev uses `DEV_PUBLIC_APP_URL` so the public hostname is not baked into the hot-reload stack.

### Google staff sign-in (optional)

Create an OAuth 2.0 **Web application** client in [Google Cloud Console](https://console.cloud.google.com/apis/credentials). Set authorized redirect URIs to match `GOOGLE_REDIRECT_URI`:

| Environment | Example redirect URI |
| ----------- | -------------------- |
| Prod | `https://crm.m2solution.ca/api/auth/google/callback` |
| Dev (Vite proxies `/api`) | `http://localhost:5173/api/auth/google/callback` |

Put `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in root `.env` (Compose) and/or `backend/.env` (local uvicorn). Leave them empty to keep password-only login; `/api/auth/google/start` then returns 503. Details: [features/auth.md](features/auth.md).

Start **prod `db`** (and `db-init`) before the dev stack. Dev has no Postgres of its own; it joins Docker network `crm-db` and talks to hostname `db`.

## Prod

```bash
docker compose up --build -d
```

- UI / API (same origin): **`10.50.0.2:8081`** (WireGuard). Host **8080** is Pterodactyl Wings, not the CRM.
- Postgres primary: `127.0.0.1:5432` — `psql -h 127.0.0.1 -U crm -d crm`
- Dev database on the same instance: `psql -h 127.0.0.1 -U crm -d crm_dev` (created by `db-init`)
- Standby: `127.0.0.1:5433` when `db-replica` is running (copies the whole instance, including `crm_dev`)

Cluster files: `/mnt/data_main/m2solution_crm/pgdata`. Streaming replica and failover: [features/backups.md](features/backups.md).

If an older Compose project named `m2solution_crm` is still running, it holds 5432/5433:

```bash
docker compose -p m2solution_crm down
docker compose up --build -d
```

Override the public bind with `PROD_WEB_PUBLISH` in `.env` (default `10.50.0.2:8081`). VPS nginx must `proxy_pass` that address.

## Dev (SSH port forward)

```bash
docker compose up -d db db-init
docker compose -f docker-compose.dev.yml up --build -d
```

- Vite: **`127.0.0.1:5173`** (not on LAN or WireGuard)
- API (direct): `127.0.0.1:8000` — the UI still proxies `/api` through Vite, so you normally only forward 5173
- Database: `crm_dev` on the prod instance (`127.0.0.1:5432`). Network `crm-db` must already exist (prod Compose creates it).

From your laptop:

```bash
ssh -N -L 5173:127.0.0.1:5173 user@this-server
```

Then open [http://localhost:5173](http://localhost:5173). Forward `8000` as well only if you want to hit the API without Vite.

## Local (no Docker)

Postgres must already be reachable at `127.0.0.1:5432`. Copy `backend/.env.example` to `backend/.env` and match `POSTGRES_PASSWORD`. Use database `crm` or `crm_dev` in `DATABASE_URL` depending on which data you want.

Terminal 1 — API:

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Terminal 2 — UI:

```bash
cd frontend
npm install
npm run dev
```

UI: [http://localhost:5173](http://localhost:5173) (proxies `/api` to the API).

## Health

`GET /api/health` → `{"status":"ok"}`. Used by Compose healthchecks. Prod through the tunnel: `https://crm.m2solution.ca/api/health`.
