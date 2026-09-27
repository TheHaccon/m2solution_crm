# Shared by CRM ops scripts. Always target prod (`docker-compose.yml` / project `crm`).
# Dev is a separate project (`crm-dev`) and must not receive replica/failover commands.
COMPOSE_DIR="${COMPOSE_DIR:-/srv/m2solution_crm}"
COMPOSE_FILE="${COMPOSE_FILE:-$COMPOSE_DIR/docker-compose.yml}"
