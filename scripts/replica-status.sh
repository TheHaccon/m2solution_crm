#!/usr/bin/env bash
set -euo pipefail

# Exit 0 if standby is streaming, or if it is not running (post-failover).
# Exit 1 if standby is running but not in recovery.

COMPOSE_DIR="${COMPOSE_DIR:-/srv/m2solution_crm}"
# shellcheck disable=SC1091
source "$COMPOSE_DIR/scripts/_compose.sh"
cd "$COMPOSE_DIR"

if ! compose_db ps --status running --services 2>/dev/null | grep -qx db; then
  echo "db (primary) is not running" >&2
  exit 1
fi

PGUSER="$(compose_db exec -T db printenv POSTGRES_USER | tr -d '\r\n')"
PGDATABASE="$(compose_db exec -T db printenv POSTGRES_DB | tr -d '\r\n')"
PGUSER="${PGUSER:-crm}"
PGDATABASE="${PGDATABASE:-crm}"

echo "=== primary slot ==="
compose_db exec -T db \
  psql -U "$PGUSER" -d "$PGDATABASE" -c \
  "SELECT slot_name, slot_type, active, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"

if ! compose_db ps --status running --services 2>/dev/null | grep -qx db-replica; then
  echo "db-replica is not running (ok after failover; rebuild standby on the repaired disk)"
  exit 0
fi

REPL_USER="$(compose_db exec -T db-replica printenv POSTGRES_USER | tr -d '\r\n')"
REPL_DB="$(compose_db exec -T db-replica printenv POSTGRES_DB | tr -d '\r\n')"
REPL_USER="${REPL_USER:-crm}"
REPL_DB="${REPL_DB:-crm}"

echo "=== replica ==="
compose_db exec -T db-replica \
  psql -U "$REPL_USER" -d "$REPL_DB" -c \
  "SELECT pg_is_in_recovery() AS in_recovery, now() - pg_last_xact_replay_timestamp() AS replay_lag;"

in_recovery="$(compose_db exec -T db-replica \
  psql -U "$REPL_USER" -d "$REPL_DB" -Atc "SELECT pg_is_in_recovery();" | tr -d '\r\n')"
if [[ "$in_recovery" != "t" ]]; then
  echo "db-replica is running but not in recovery" >&2
  exit 1
fi
