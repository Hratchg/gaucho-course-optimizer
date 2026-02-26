#!/bin/bash
# Export the full GCO database to a SQL dump for portability.
# Usage: bash scripts/export_db.sh
# Output: data/gco_dump.sql

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

mkdir -p "$PROJECT_DIR/data"

echo "Exporting database..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
  pg_dump -U gco --clean --if-exists --no-owner --no-acl gco \
  > "$PROJECT_DIR/data/gco_dump.sql"

SIZE=$(du -h "$PROJECT_DIR/data/gco_dump.sql" | cut -f1)
LINES=$(wc -l < "$PROJECT_DIR/data/gco_dump.sql")
echo "Done! Exported to data/gco_dump.sql ($SIZE, $LINES lines)"
echo ""
echo "To restore on another machine:"
echo "  docker compose up db -d"
echo "  bash scripts/import_db.sh"
