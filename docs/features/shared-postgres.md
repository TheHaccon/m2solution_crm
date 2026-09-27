# Feature: Shared Postgres

Date: 2026-09-04

## What it does

Host-wide PostgreSQL 16 cluster for the CRM and other services on the same machine. One primary, one streaming replica, declarative database creation, and LAN + WireGuard access for tools outside Docker.

## Behavior

- **Stack:** `docker compose -f docker-compose.db.yml up -d` (project `shared-db`). Cluster secrets (`REPLICATION_PASSWORD`, pgweb auth, extra DB list) load from `postgres.env` via `env_file`. `./scripts/db-compose.sh` also passes `postgres.env` for compose interpolation (custom `PGDATA_*` / publish addresses).
- **Config:** [`postgres.env`](../postgres.env.example) — passwords, disk paths, publish addresses, `POSTGRES_EXTRA_DATABASES`.
- **Network:** Docker network `shared-db` (external — not removed on `down` while CRM containers are attached). Created by `./scripts/db-compose.sh up` if missing. Full teardown including the network: `./scripts/db-compose.sh down --force` (stops CRM prod/dev first).
- **Primary publishes:** `${POSTGRES_PUBLISH_LAN}` (default `192.168.2.99:5432`), `${POSTGRES_PUBLISH_WG}` (default `10.50.0.2:5432`), and `127.0.0.1:5432`.
- **Replica:** `127.0.0.1:5433` only (ops inspection).
- **`db-init`:** runs `ensure-databases.sh` (creates `POSTGRES_EXTRA_DATABASES`) and `configure-pg-access.sh` (appends `pg_hba` for Docker/LAN/WG, reloads).
- **`POSTGRES_DB`** (`crm`) is created on first cluster init; extras (e.g. `crm_dev`) are created by `db-init`.
- **`pgweb`:** browser UI on **`http://192.168.2.99:8085`** (LAN only). HTTP basic auth (`PGWEB_AUTH_USER` / `PGWEB_AUTH_PASS`), then auto-connected to database **`crm`** on host `db`. One pgweb instance talks to **one Postgres server**; every database on that server is reachable from the same UI — click the database name in the sidebar to switch (`crm_dev`, `cooking_main`, `cooking_dev`, etc.). Do **not** set `PGWEB_LOCK_SESSION` or `PGWEB_SESSIONS` in compose (lock blocks switching; sessions disables auto-connect).
- CRM prod/dev stacks have **no** Postgres services; they use external network `shared-db`.

### Add a database for a new service

1. Add the name to `POSTGRES_EXTRA_DATABASES` in `postgres.env` (comma-separated), e.g. `crm_dev,cooking_main,cooking_dev`.
2. `docker compose -f docker-compose.db.yml up db-init` (or restart the stack).
3. Point the service at `db:5432/<name>` on `shared-db`, or from LAN `192.168.2.99:5432/<name>`.

### Connection examples

| Client | URL |
| ------ | --- |
| CRM container | `postgresql://crm:…@db:5432/crm` on network `shared-db` |
| LAN laptop | `postgresql://crm:…@192.168.2.99:5432/crm` |
| WireGuard | `postgresql://crm:…@10.50.0.2:5432/crm` |
| Another Compose stack | `networks: shared-db: external: true` + hostname `db` |

Replication and failover: [backups.md](backups.md). CRM-specific notes: [postgres.md](postgres.md).

## API

None (infrastructure only).

## UI

- **pgweb** — `http://192.168.2.99:8085` on the home LAN (basic auth). See behavior above.

## Files

- `docker-compose.db.yml`, `postgres.env.example`
- `deploy/postgres/ensure-databases.sh`, `deploy/postgres/configure-pg-access.sh`, `deploy/postgres/replica-entrypoint.sh`
- `scripts/db-compose.sh`, `scripts/_compose.sh` (`compose_db` helper)
- `docker-compose.yml`, `docker-compose.dev.yml` (external `shared-db`)

## Follow-ups / out of scope

- Per-service Postgres roles (shared `crm` user for now)
- PgBouncer / connection pooling
- Publishing the replica on LAN
- Moving the cluster to another host
