# Shared by CRM ops scripts. Targets the shared Postgres stack (docker-compose.db.yml).
COMPOSE_DIR="${COMPOSE_DIR:-/srv/m2solution_crm}"
POSTGRES_ENV="${POSTGRES_ENV:-$COMPOSE_DIR/postgres.env}"
COMPOSE_FILE="${COMPOSE_FILE:-$COMPOSE_DIR/docker-compose.db.yml}"
SHARED_DB_NETWORK="${SHARED_DB_NETWORK:-shared-db}"

ensure_shared_db_network() {
  docker network inspect "$SHARED_DB_NETWORK" >/dev/null 2>&1 \
    || docker network create "$SHARED_DB_NETWORK"
}

compose_db() {
  docker compose --env-file "$COMPOSE_DIR/.env" --env-file "$POSTGRES_ENV" -f "$COMPOSE_FILE" "$@"
}

compose_db_down_force() {
  echo "Stopping CRM prod and dev (they use network $SHARED_DB_NETWORK)..." >&2
  docker compose -f "$COMPOSE_DIR/docker-compose.yml" down
  docker compose -f "$COMPOSE_DIR/docker-compose.dev.yml" down
  compose_db down
  if docker network inspect "$SHARED_DB_NETWORK" >/dev/null 2>&1; then
    docker network rm "$SHARED_DB_NETWORK"
    echo "Removed network $SHARED_DB_NETWORK" >&2
  fi
}
