#!/usr/bin/env bash
set -euo pipefail

# Idempotent: allow password auth from Docker bridges, LAN, and WireGuard.
# Appends to pg_hba.conf on the mounted PGDATA volume, then reloads.

: "${PGHOST:=db}"
: "${PGUSER:=crm}"
: "${POSTGRES_DB:-crm}"
: "${PGDATA:-/var/lib/postgresql/data}"

HBA="${PGDATA}/pg_hba.conf"
if [[ ! -f "$HBA" ]]; then
  echo "pg_hba.conf not found at ${HBA}" >&2
  exit 1
fi

append_hba() {
  local line="$1"
  if ! grep -qxF "$line" "$HBA"; then
    echo "$line" >> "$HBA"
    echo "added pg_hba: ${line}"
  fi
}

append_hba "host all ${PGUSER} 172.16.0.0/12 scram-sha-256"
append_hba "host all ${PGUSER} 192.168.0.0/16 scram-sha-256"
append_hba "host all ${PGUSER} 10.50.0.0/24 scram-sha-256"

psql -v ON_ERROR_STOP=1 -d postgres -c "SELECT pg_reload_conf();"
echo "pg_hba reloaded"
