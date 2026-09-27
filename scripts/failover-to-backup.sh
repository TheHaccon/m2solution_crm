#!/usr/bin/env bash
set -euo pipefail

# Promote the standby on data_backup and retarget Compose `db` at that disk.

COMPOSE_DIR="${COMPOSE_DIR:-/srv/m2solution_crm}"
# shellcheck disable=SC1091
source "$COMPOSE_DIR/scripts/_compose.sh"
cd "$COMPOSE_DIR"

MAIN_PGDATA="/mnt/data_main/m2solution_crm/pgdata"
BACKUP_PGDATA="/mnt/data_backup/m2solution_crm/pgdata"

if ! docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx db-replica; then
  echo "db-replica is not running; cannot promote" >&2
  exit 1
fi

PGUSER="$(docker compose -f "$COMPOSE_FILE" exec -T db-replica printenv POSTGRES_USER | tr -d '\r\n')"
PGDATABASE="$(docker compose -f "$COMPOSE_FILE" exec -T db-replica printenv POSTGRES_DB | tr -d '\r\n')"
PGUSER="${PGUSER:-crm}"
PGDATABASE="${PGDATABASE:-crm}"

in_recovery="$(docker compose -f "$COMPOSE_FILE" exec -T db-replica \
  psql -U "$PGUSER" -d "$PGDATABASE" -Atc "SELECT pg_is_in_recovery();" | tr -d '\r\n')"
if [[ "$in_recovery" != "t" ]]; then
  echo "db-replica is not in recovery (pg_is_in_recovery=$in_recovery); refusing to promote" >&2
  exit 1
fi

echo "stopping primary db"
docker compose -f "$COMPOSE_FILE" stop db

echo "promoting db-replica"
docker compose -f "$COMPOSE_FILE" exec -T db-replica \
  psql -v ON_ERROR_STOP=1 -U "$PGUSER" -d "$PGDATABASE" -c "SELECT pg_promote();"

for _ in $(seq 1 30); do
  in_recovery="$(docker compose -f "$COMPOSE_FILE" exec -T db-replica \
    psql -U "$PGUSER" -d "$PGDATABASE" -Atc "SELECT pg_is_in_recovery();" | tr -d '\r\n' || true)"
  if [[ "$in_recovery" == "f" ]]; then
    break
  fi
  sleep 1
done
if [[ "$in_recovery" != "f" ]]; then
  echo "promote did not complete (still in recovery)" >&2
  exit 1
fi

echo "stopping db-replica so only one postmaster owns the backup pgdata"
docker compose -f "$COMPOSE_FILE" stop db-replica

python3 - "$COMPOSE_DIR/.env" "$BACKUP_PGDATA" "$MAIN_PGDATA" <<'PY'
from pathlib import Path
import sys
env_path = Path(sys.argv[1])
primary, replica = sys.argv[2], sys.argv[3]
text = env_path.read_text()

def set_key(text: str, key: str, value: str) -> str:
    prefix = f"{key}="
    lines = text.splitlines(True)
    out = []
    found = False
    for line in lines:
        if line.startswith(prefix):
            found = True
            out.append(f"{key}={value}\n")
        else:
            out.append(line)
    if not found:
        if text and not text.endswith("\n"):
            out.append("\n")
        out.append(f"{key}={value}\n")
    return "".join(out)

text = set_key(text, "PGDATA_PRIMARY", primary)
text = set_key(text, "PGDATA_REPLICA", replica)
env_path.write_text(text)
PY

echo "starting db on backup disk"
docker compose -f "$COMPOSE_FILE" up -d db
docker compose -f "$COMPOSE_FILE" restart api || true

echo "failover complete: PGDATA_PRIMARY=$BACKUP_PGDATA"
echo "when data_main is replaced, empty $MAIN_PGDATA and start db-replica to rebuild the standby"
