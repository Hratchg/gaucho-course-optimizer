#!/usr/bin/env bash
# Check production for migration drift and track it in a single labelled GitHub issue.
#
# Drift:    open one issue labelled $LABEL, or silently refresh the body of the
#           one already open (body edits send no notifications).
# In sync:  comment "In sync again at ..." on the open issue and close it.
# Either way the job stays green: the issue is the alert, not a red job.
# If the check itself can't run (bad secret, database unreachable), exit 1 so
# the run goes red, and leave the issue alone.
#
# Env: DATABASE_URL (required), GH_TOKEN, GH_REPO (set by the workflow),
#      RUN_URL (optional link to this run), LABEL (default "migration-drift"),
#      PYTHON (default "python").
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
LABEL="${LABEL:-migration-drift}"
PYTHON="${PYTHON:-python}"
RUN_URL="${RUN_URL:-}"
TITLE="Production schema has drifted from the migrations"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="$(mktemp)"

now_utc() { date -u +"%Y-%m-%d %H:%M:%S UTC"; }

status=0
"$PYTHON" "$SCRIPT_DIR/check_migration_drift.py" --report "$REPORT_FILE" --run-url "$RUN_URL" \
  || status=$?

# 1 with a report is drift; anything else non-zero (including a Python crash,
# which also exits 1 but writes no report) means the check didn't run.
if [ "$status" -ne 0 ] && { [ "$status" -ne 1 ] || [ ! -s "$REPORT_FILE" ]; }; then
  echo "The drift check could not run (exit ${status}); leaving the ${LABEL} issue alone."
  exit 1
fi

# Number of the open drift issue (there is at most one), or "".
open_issue=$(gh issue list --label "$LABEL" --state open --limit 1 --json number --jq '.[0].number // empty')

if [ "$status" -eq 0 ]; then
  if [ -z "$open_issue" ]; then
    echo "In sync, and no open ${LABEL} issue. Nothing to do."
    exit 0
  fi
  gh issue comment "$open_issue" --body \
    "In sync again at $(now_utc): production is at the repo head and the models match the schema.${RUN_URL:+ ([run](${RUN_URL}))}"
  gh issue close "$open_issue"
  echo "In sync. Closed #${open_issue}."
  exit 0
fi

if [ -z "$open_issue" ]; then
  gh label create "$LABEL" --color FBCA04 \
    --description "Production schema differs from the migrations on master" --force
  gh issue create --title "$TITLE" --label "$LABEL" --body-file "$REPORT_FILE"
else
  gh issue edit "$open_issue" --body-file "$REPORT_FILE"
  echo "Still drifted. Refreshed #${open_issue}."
fi
