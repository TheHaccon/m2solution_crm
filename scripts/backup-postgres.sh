#!/usr/bin/env bash
echo "Nightly pg_dump retention was replaced by a streaming replica on data_backup." >&2
echo "Status:  $0/../replica-status.sh  (or scripts/replica-status.sh)" >&2
echo "Failover: scripts/failover-to-backup.sh" >&2
echo "See docs/features/backups.md" >&2
exit 1
