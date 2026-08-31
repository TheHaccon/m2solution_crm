# Run

Seed staff user: `admin@m2solution.com` / `changeme` (override with `SEED_EMAIL` / `SEED_PASSWORD`).

## Docker (preferred)

Docker Desktop must be running.

```bash
docker compose up --build
```

App: [http://localhost:8080](http://localhost:8080)

SQLite is stored in the `crm-data` volume.

Live reload (Vite on 5173, API on 8000):

```bash
docker compose -f docker-compose.dev.yml up --build
```

## Local (no Docker)

Terminal 1 — API:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Terminal 2 — UI:

```bash
cd frontend
npm install
npm run dev
```

UI: [http://localhost:5173](http://localhost:5173) (proxies `/api` to the API).

## Health

`GET /api/health` → `{"status":"ok"}`. Used by Compose healthchecks.
