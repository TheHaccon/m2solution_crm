#!/usr/bin/env bash
set -euo pipefail

# Idempotent: create POSTGRES_EXTRA_DATABASES on the shared Postgres instance.
# POSTGRES_DB is created by the postgres image on first init only.

ident_ok() {
  [[ "$1" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]
}

: "${PGHOST:=db}"
: "${PGUSER:=crm}"
: "${POSTGRES_DB:=crm}"
: "${POSTGRES_EXTRA_DATABASES:=}"

if ! ident_ok "$PGUSER" || ! ident_ok "$POSTGRES_DB"; then
  echo "PGUSER and POSTGRES_DB must be simple SQL identifiers" >&2
  exit 1
fi

exists="$(psql -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_DB}'")"
if [[ "$exists" != "1" ]]; then
  psql -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE ${POSTGRES_DB} OWNER ${PGUSER};"
  echo "created database ${POSTGRES_DB}"
else
  echo "database ${POSTGRES_DB} already exists"
fi

IFS=',' read -r -a extra_dbs <<< "${POSTGRES_EXTRA_DATABASES}"
for db in "${extra_dbs[@]}"; do
  db="${db#"${db%%[![:space:]]*}"}"
  db="${db%"${db##*[![:space:]]}"}"
  [[ -z "$db" ]] && continue
  if [[ "$db" == "$POSTGRES_DB" ]]; then
    continue
  fi
  if ! ident_ok "$db"; then
    echo "invalid database name: ${db}" >&2
    exit 1
  fi
  exists="$(psql -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '${db}'")"
  if [[ "$exists" != "1" ]]; then
    psql -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE ${db} OWNER ${PGUSER};"
    echo "created database ${db}"
  else
    echo "database ${db} already exists"
  fi
done
