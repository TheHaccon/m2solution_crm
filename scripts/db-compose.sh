#!/usr/bin/env bash
# Wrapper for the shared Postgres stack. Loads postgres.env for compose interpolation.
set -euo pipefail

COMPOSE_DIR="${COMPOSE_DIR:-/srv/m2solution_crm}"
# shellcheck disable=SC1091
source "$COMPOSE_DIR/scripts/_compose.sh"
cd "$COMPOSE_DIR"

case "${1:-}" in
  up|start|restart|run|create)
    ensure_shared_db_network
    ;;
  down)
    if [[ "${2:-}" == "--force" ]]; then
      compose_db_down_force
      exit 0
    fi
    ;;
esac

compose_db "$@"
