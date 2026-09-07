#!/usr/bin/env bash
# Pull, rebuild and restart. Run from deploy/ on the server.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Pulling latest code"
git pull --ff-only

echo "==> Building images"
docker compose build

echo "==> Starting"
# --remove-orphans cleans up containers for services deleted from the file.
docker compose up -d --remove-orphans

echo "==> Waiting for the API"
for _ in $(seq 1 30); do
  if docker compose exec -T app python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" 2>/dev/null; then
    echo "    healthy"
    break
  fi
  sleep 2
done

echo
echo "Done. Reminder: create_tables only adds MISSING TABLES."
echo "Column changes need the SQL in backend/migrations/, applied by hand:"
echo "  docker compose exec -T db psql -U \$POSTGRES_USER -d \$POSTGRES_DB < ../backend/migrations/006_game_results_won.sql"
