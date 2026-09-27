#!/usr/bin/env bash
set -euo pipefail

# Configure an already-initialized primary for streaming replication. Idempotent.

COMPOSE_DIR="${COMPOSE_DIR:-/srv/m2solution_crm}"
# shellcheck disable=SC1091
source "$COMPOSE_DIR/scripts/_compose.sh"
cd "$COMPOSE_DIR"

if ! compose_db ps --status running --services 2>/dev/null | grep -qx db; then
  echo "db service is not running" >&2
  exit 1
fi

env_val() {
  grep -E "^${1}=" "$POSTGRES_ENV" | tail -n1 | cut -d= -f2-
}

REPLICATION_PASSWORD="${REPLICATION_PASSWORD:-$(env_val REPLICATION_PASSWORD)}"
if [[ -z "$REPLICATION_PASSWORD" ]]; then
  echo "REPLICATION_PASSWORD is not set in postgres.env" >&2
  exit 1
fi

PGUSER="$(compose_db exec -T db printenv POSTGRES_USER | tr -d '\r\n')"
PGDATABASE="$(compose_db exec -T db printenv POSTGRES_DB | tr -d '\r\n')"
PGUSER="${PGUSER:-crm}"
PGDATABASE="${PGDATABASE:-crm}"

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}
PW="$(sql_escape "$REPLICATION_PASSWORD")"

compose_db exec -T db \
  psql -v ON_ERROR_STOP=1 -U "$PGUSER" -d "$PGDATABASE" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'replicator') THEN
    CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD '${PW}';
  ELSE
    ALTER ROLE replicator WITH REPLICATION LOGIN PASSWORD '${PW}';
  END IF;
END
\$\$;
SELECT pg_create_physical_replication_slot('crm_replica', true)
WHERE NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'crm_replica');
SQL

compose_db exec -T db bash -c '
set -euo pipefail
PGDATA="${PGDATA:-/var/lib/postgresql/data}"
LINE="host replication replicator all scram-sha-256"
if ! grep -qxF "$LINE" "$PGDATA/pg_hba.conf"; then
  echo "$LINE" >> "$PGDATA/pg_hba.conf"
fi
'

compose_db exec -T db \
  psql -v ON_ERROR_STOP=1 -U "$PGUSER" -d "$PGDATABASE" -c "SELECT pg_reload_conf();"

echo "replication enabled on primary (role replicator, slot crm_replica, pg_hba reloaded)"
