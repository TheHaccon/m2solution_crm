#!/bin/bash
set -euo pipefail

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
PRIMARY_HOST="${PRIMARY_HOST:-db}"
REPL_USER="${REPLICATION_USER:-replicator}"
REPL_SLOT="${REPLICATION_SLOT:-crm_replica}"

if [[ -z "${REPLICATION_PASSWORD:-}" ]]; then
  echo "REPLICATION_PASSWORD is required" >&2
  exit 1
fi

run_as_pg() {
  if [[ "$(id -u)" = "0" ]]; then
    gosu postgres "$@"
  else
    "$@"
  fi
}

if [[ ! -s "$PGDATA/PG_VERSION" ]]; then
  echo "Replica data dir empty; waiting for primary ${PRIMARY_HOST}"
  until pg_isready -h "$PRIMARY_HOST" -q; do
    sleep 2
  done

  find "$PGDATA" -mindepth 1 -maxdepth 1 -exec rm -rf {} + || true
  if [[ "$(id -u)" = "0" ]]; then
    chown postgres:postgres "$PGDATA"
    chmod 700 "$PGDATA"
  fi

  export PGPASSWORD="$REPLICATION_PASSWORD"
  until run_as_pg pg_basebackup \
      -h "$PRIMARY_HOST" \
      -U "$REPL_USER" \
      -D "$PGDATA" \
      -Fp -Xs -P -R \
      -S "$REPL_SLOT"; do
    echo "pg_basebackup failed; retrying in 3s"
    find "$PGDATA" -mindepth 1 -maxdepth 1 -exec rm -rf {} + || true
    if [[ "$(id -u)" = "0" ]]; then
      chown postgres:postgres "$PGDATA"
      chmod 700 "$PGDATA"
    fi
    sleep 3
  done
  unset PGPASSWORD
fi

exec docker-entrypoint.sh postgres
