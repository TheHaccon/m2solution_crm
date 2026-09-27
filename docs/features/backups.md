# Feature: Postgres replica and disk failover

Date: 2026-08-31

## What it does

Keep a live Postgres standby on the second disk. If `/mnt/data_main` fails, promote that standby and retarget Compose so the API still talks to hostname `db`. Ops-only; staff UI is unchanged.

This is **not** a 30-day dump archive. The replica copies every write, including deletes and corruption. It does **not** cover NVMe/OS failure or the whole machine dying.

## Behavior

- Primary: `${PGDATA_PRIMARY}` default `/mnt/data_main/m2solution_crm/pgdata` (Compose service `db`, `127.0.0.1:5432`)
- Standby: `${PGDATA_REPLICA}` default `/mnt/data_backup/m2solution_crm/pgdata` (Compose service `db-replica`, `127.0.0.1:5433` for inspection)
- Streaming replication with role `replicator` and physical slot `crm_replica`. Lag is typically seconds. The replica is the whole instance (`crm` and `crm_dev`).
- API never connects to the replica (prod uses `crm`, dev uses `crm_dev` on the primary).
- **Do not rsync a live `pgdata` directory.**
- Replica/failover scripts always target **prod** (`docker-compose.yml`). There is no second Postgres for dev.

### Enable (once, existing cluster)

```bash
/srv/m2solution_crm/scripts/enable-replication.sh
docker compose up -d db-replica
/srv/m2solution_crm/scripts/replica-status.sh
```

`enable-replication.sh` creates/updates `replicator`, creates slot `crm_replica` if missing, appends `pg_hba` `host replication replicator all scram-sha-256`, reloads. Replica entrypoint runs `pg_basebackup -R` when the backup `pgdata` is empty.

Hourly systemd timer `m2solution-crm-replica-status.timer` runs `replica-status.sh`. It exits non-zero if `db-replica` is running but **not** in recovery. If the replica container is stopped (after failover), the check succeeds.

Replace the old dump timer (once, needs root):

```bash
sudo systemctl disable --now m2solution-crm-backup.timer || true
sudo cp /srv/m2solution_crm/deploy/systemd/m2solution-crm-replica-status.service \
        /srv/m2solution_crm/deploy/systemd/m2solution-crm-replica-status.timer \
        /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now m2solution-crm-replica-status.timer
```

### Failover (main disk dead or you choose to switch)

```bash
/srv/m2solution_crm/scripts/failover-to-backup.sh
```

1. Confirms replica is in recovery
2. Stops `db`
3. `SELECT pg_promote()` on `db-replica`
4. Stops `db-replica` (one postmaster per directory)
5. Sets `PGDATA_PRIMARY` to the backup disk path in `.env` (`PGDATA_REPLICA` to the old main path)
6. Starts `db` on the backup disk; restarts `api`

Writes during that window are lost. Lag from before the outage is typically seconds.

### Failback (after `data_main` is replaced)

Empty `/mnt/data_main/m2solution_crm/pgdata` (uid 999), keep `PGDATA_REPLICA` pointing there, start `db-replica` so it basebackup’s from the new primary. Not automated.

### Leftover dumps

Old `crm-*.dump` files under `/mnt/data_backup/m2solution_crm/` are not the failover path. `scripts/backup-postgres.sh` now only points here.

## API

None.

## UI

None.

## Files

- `docker-compose.yml` (`db-replica`, `PGDATA_PRIMARY` / `PGDATA_REPLICA`). Dev Compose has no Postgres service.
- `deploy/postgres/replica-entrypoint.sh`
- `scripts/enable-replication.sh`, `scripts/failover-to-backup.sh`, `scripts/replica-status.sh`, `scripts/_compose.sh`
- `deploy/systemd/m2solution-crm-replica-status.service`, `deploy/systemd/m2solution-crm-replica-status.timer`
- `.env.example` (`REPLICATION_PASSWORD`, `PGDATA_*`)

## Follow-ups / out of scope

- Automatic failover (Patroni)
- RAID1
- WAL archive / point-in-time dumps
- Off-site copy
