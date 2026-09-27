# Feature: Postgres replica and disk failover

Date: 2026-08-31

## What it does

Keep a live Postgres standby on the second disk. If `/mnt/data_main` fails, promote that standby and retarget the shared-db stack. Ops-only; staff UI is unchanged.

This is **not** a 30-day dump archive. The replica copies every write, including deletes and corruption. It does **not** cover NVMe/OS failure or the whole machine dying.

## Behavior

- Primary: `${PGDATA_PRIMARY}` in `postgres.env` (Compose `db`, LAN/WG/localhost on 5432)
- Standby: `${PGDATA_REPLICA}` (Compose `db-replica`, `127.0.0.1:5433`)
- Streaming replication with role `replicator` and slot `crm_replica`. Whole instance (`crm`, `crm_dev`, and any extra databases).
- CRM API never connects to the replica.
- **Do not rsync a live `pgdata` directory.**
- Ops scripts target **`docker-compose.db.yml`** via `scripts/_compose.sh` (`compose_db`).

### Enable (once, existing cluster)

```bash
/srv/m2solution_crm/scripts/enable-replication.sh
docker compose -f docker-compose.db.yml up -d db-replica
/srv/m2solution_crm/scripts/replica-status.sh
```

### Failover (main disk dead or you choose to switch)

```bash
/srv/m2solution_crm/scripts/failover-to-backup.sh
```

1. Confirms replica is in recovery
2. Stops primary `db`
3. `SELECT pg_promote()` on `db-replica`
4. Stops `db-replica`
5. Swaps `PGDATA_PRIMARY` / `PGDATA_REPLICA` in **`postgres.env`**
6. Starts `db` on backup disk; restarts CRM `api`

### Failback (after `data_main` is replaced)

Empty `/mnt/data_main/m2solution_crm/pgdata` (uid 999), start `db-replica` so it basebackup’s from the new primary. Not automated.

## API

None.

## UI

None.

## Files

- `docker-compose.db.yml`
- `deploy/postgres/replica-entrypoint.sh`
- `scripts/enable-replication.sh`, `scripts/failover-to-backup.sh`, `scripts/replica-status.sh`, `scripts/_compose.sh`
- `deploy/systemd/m2solution-crm-replica-status.service`, `deploy/systemd/m2solution-crm-replica-status.timer`
- `postgres.env.example`

## Follow-ups / out of scope

- Automatic failover (Patroni)
- RAID1
- WAL archive / point-in-time dumps
- Off-site copy
