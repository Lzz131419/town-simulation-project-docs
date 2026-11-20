#!/bin/sh
set -eu
# Runs in its own backup container. pg_dump uses PGPASSWORD from the environment.
backup_dir=${BACKUP_DIR:-/backups}
interval=${BACKUP_INTERVAL_SECONDS:-86400}
keep_days=${BACKUP_KEEP_DAYS:-7}
case "$interval:$keep_days" in *[!0-9:]*|:*) echo 'Invalid backup configuration' >&2; exit 1;; esac
[ "$interval" -ge 60 ] && [ "$keep_days" -ge 1 ]
mkdir -p "$backup_dir"
trap 'rm -f "$backup_dir"/*.partial; exit 0' TERM INT
while :; do
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  partial="$backup_dir/town-$stamp.dump.partial"
  result=0
  if pg_dump --format=custom --no-owner --file="$partial" && pg_restore --list "$partial" >/dev/null; then
    mv "$partial" "$backup_dir/town-$stamp.dump"
    date +%s > "$backup_dir/last-success"
    find "$backup_dir" -type f -name 'town-*.dump' -mtime "+$keep_days" -delete
    echo "PostgreSQL backup completed: $stamp"
  else
    rm -f "$partial"
    echo 'PostgreSQL backup failed; previous backups retained' >&2
    result=1
  fi
  if [ "${BACKUP_ONCE:-0}" = 1 ]; then exit "$result"; fi
  sleep "$interval" & wait $!
done
