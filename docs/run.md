# Run

Three Compose projects: **shared Postgres**, **CRM prod**, and **CRM dev**. Postgres is started first; CRM apps join network `shared-db` and use hostname `db`.

| Stack | Compose file | Project | Who uses it |
| ----- | ------------ | ------- | ----------- |
| **Postgres** | `docker-compose.db.yml` | `shared-db` | All services on this host |
| **Prod** | `docker-compose.yml` | `crm` | Public site `https://crm.m2solution.ca` (VPS → `10.50.0.2:8081`) |
| **Dev** | `docker-compose.dev.yml` | `crm-dev` | Staff only, SSH forward to Vite |

Copy [`.env.example`](../.env.example) → `.env` (CRM app secrets) and [`postgres.env.example`](../postgres.env.example) → `postgres.env` (cluster secrets). Keep `POSTGRES_USER` / `POSTGRES_PASSWORD` in sync between both files. `docker compose -f docker-compose.db.yml` loads cluster secrets from `postgres.env` via `env_file`; use `./scripts/db-compose.sh` if you override disk paths or publish addresses in `postgres.env`.

Seed staff: `matcote111@gmail.com` and `mathieu.laureti@gmail.com` / `changeme` (comma-separated `SEED_EMAIL` / `SEED_PASSWORD`). Each CRM database (`crm` vs `crm_dev`) seeds independently.

## Shared Postgres (start first)

```bash
./scripts/db-compose.sh up -d
# same as: docker compose -f docker-compose.db.yml up -d
```

- Primary: `127.0.0.1:5432`, `192.168.2.99:5432`, `10.50.0.2:5432`
- Standby: `127.0.0.1:5433`
- Databases: `crm` (bootstrap), `crm_dev` (+ any name in `POSTGRES_EXTRA_DATABASES`)
- **pgweb:** `http://192.168.2.99:8085` (LAN + basic auth) — opens on `crm`; switch DB from the sidebar
- Cluster files: `/mnt/data_main/m2solution_crm/pgdata` — see [features/shared-postgres.md](features/shared-postgres.md)
- `docker compose -f docker-compose.db.yml down` leaves network `shared-db` in place (CRM still attached). Remove everything: `./scripts/db-compose.sh down --force`

## Prod

```bash
docker compose up --build -d
```

- UI / API: **`10.50.0.2:8081`** (WireGuard). Host **8080** is Pterodactyl Wings.
- File blobs: `/mnt/data_main/m2solution_crm/files` (not replicated)

### Schema migrations (Alembic)

After pulling a revision that adds columns (or a repair revision such as `005_repair_inv_client_cols`), apply without recreating the Postgres volume:

```bash
docker compose exec api alembic upgrade head
```

`create_all` on API startup does not add missing columns to existing tables. Do not stamp backward to re-run older revisions when later tables already exist.

## Dev (SSH port forward)

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

- Vite: `127.0.0.1:5173` — forward with `ssh -N -L 5173:127.0.0.1:5173 user@this-server`
- Database: `crm_dev` on the shared instance
- File blobs: `/mnt/data_main/m2solution_crm/files_dev`

## Cutover from embedded Postgres (one-time)

If Postgres still runs inside the old `crm` compose project:

```bash
docker compose down
docker compose -f docker-compose.dev.yml down
docker network rm crm-db 2>/dev/null || true
./scripts/db-compose.sh up -d
docker compose up --build -d
docker compose -f docker-compose.dev.yml up -d
```

Existing `pgdata` on disk is reused — no dump/restore.

## Local (no Docker)

Postgres must be reachable at `127.0.0.1:5432` (or LAN/WG address). Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL` to `crm` or `crm_dev`.

## Health

`GET /api/health` on CRM. Replica: `scripts/replica-status.sh`. Prod through tunnel: `https://crm.m2solution.ca/api/health`.
