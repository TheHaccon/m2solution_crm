#!/usr/bin/env bash
set -euo pipefail

# Idempotent: create DEV_POSTGRES_DB on the shared Postgres instance (prod `db`).
# Initdb.d cannot do this — it only runs when the data directory is empty.

ident_ok() {
  [[ "$1" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]
}

: "${PGHOST:=db}"
: "${PGUSER:=crm}"
: "${DEV_POSTGRES_DB:=crm_dev}"

if ! ident_ok "$PGUSER" || ! ident_ok "$DEV_POSTGRES_DB"; then
  echo "PGUSER and DEV_POSTGRES_DB must be simple SQL identifiers" >&2
  exit 1
fi

exists="$(psql -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '${DEV_POSTGRES_DB}'")"
if [[ "$exists" != "1" ]]; then
  psql -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE ${DEV_POSTGRES_DB} OWNER ${PGUSER};"
  echo "created database ${DEV_POSTGRES_DB}"
else
  echo "database ${DEV_POSTGRES_DB} already exists"
fi
