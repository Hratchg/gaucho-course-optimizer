#!/bin/bash
# Import the GCO database dump into a running Postgres container.
# Usage: bash scripts/import_db.sh
# Prereq: docker compose up db -d

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DUMP_FILE="$PROJECT_DIR/data/gco_dump.sql"

if [ ! -f "$DUMP_FILE" ]; then
  echo "Error: $DUMP_FILE not found. Run scripts/export_db.sh first."
  exit 1
fi

echo "Importing database from data/gco_dump.sql..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
  psql -U gco -d gco < "$DUMP_FILE"

echo "Done! Database restored."
echo ""
echo "Verify with:"
echo "  docker compose exec db psql -U gco -c \"SELECT 'professors' as tbl, count(*) FROM professors UNION ALL SELECT 'courses', count(*) FROM courses UNION ALL SELECT 'gaucho_scores', count(*) FROM gaucho_scores;\""
