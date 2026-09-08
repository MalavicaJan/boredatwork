#!/usr/bin/env bash
# Nightly database dump, kept for 14 days.
set -euo pipefail

cd "$(dirname "$0")"
source .env

BACKUP_DIR="${HOME}/backups"
mkdir -p "$BACKUP_DIR"

STAMP=$(date +%Y-%m-%d-%H%M)
FILE="$BACKUP_DIR/boredatwork-$STAMP.sql.gz"

docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$FILE"

echo "Wrote $FILE"

find "$BACKUP_DIR" -name 'boredatwork-*.sql.gz' -mtime +14 -delete
