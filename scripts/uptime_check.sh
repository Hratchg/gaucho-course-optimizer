#!/usr/bin/env bash
# Ping a readiness URL and track outages in a single labelled GitHub issue.
#
# Down: open one issue labelled $LABEL, or silently refresh the body of the
#       one already open (body edits send no notifications).
# Up:   comment "Recovered at ..." on the open issue and close it.
#
# Exits 0 in both cases; the issue is the alert, not a red job.
#
# Env: URL (required), GH_TOKEN, GH_REPO (set by the workflow),
#      RUN_URL (optional link to this run), LABEL (default "uptime"),
#      ATTEMPTS (default 3), RETRY_DELAY seconds (default 20).
set -euo pipefail

: "${URL:?URL is required}"
LABEL="${LABEL:-uptime}"
ATTEMPTS="${ATTEMPTS:-3}"
RETRY_DELAY="${RETRY_DELAY:-20}"
RUN_URL="${RUN_URL:-}"
TITLE="Production /ready is down"
RESPONSE_FILE="$(mktemp)"

now_utc() { date -u +"%Y-%m-%d %H:%M:%S UTC"; }

# Retry a few times so one slow cold start or network blip doesn't open an issue.
code="000"
for attempt in $(seq 1 "$ATTEMPTS"); do
  code=$(curl -sS -o "$RESPONSE_FILE" -w '%{http_code}' --max-time 30 "$URL" || true)
  echo "attempt ${attempt}/${ATTEMPTS}: status=${code}"
  if [ "$code" = "200" ]; then break; fi
  if [ "$attempt" -lt "$ATTEMPTS" ]; then sleep "$RETRY_DELAY"; fi
done
head -c 2000 "$RESPONSE_FILE"; echo

# "<number> <createdAt as epoch seconds>" of the open uptime issue (there is at most one), or "".
open_issue=$(gh issue list --label "$LABEL" --state open --limit 1 \
  --json number,createdAt --jq '.[0] | select(.) | "\(.number) \(.createdAt | fromdateiso8601)"')

if [ "$code" = "200" ]; then
  if [ -z "$open_issue" ]; then
    echo "Up, and no open ${LABEL} issue. Nothing to do."
    exit 0
  fi
  read -r number opened_at <<<"$open_issue"
  mins=$(( ($(date -u +%s) - opened_at) / 60 ))
  gh issue comment "$number" --body \
    "Recovered at $(now_utc): \`${URL}\` returned 200. Down for about $((mins / 60))h $((mins % 60))m since this issue was opened.${RUN_URL:+ ([run](${RUN_URL}))}"
  gh issue close "$number"
  echo "Up. Closed #${number}."
  exit 0
fi

body_file="$(mktemp)"
{
  echo "The uptime check has failed ${ATTEMPTS} attempts in a row. This issue closes itself when the check passes again."
  echo
  echo "- **URL:** ${URL}"
  echo "- **Last status:** ${code} (000 means no HTTP response: timeout or connection error)"
  echo "- **Last checked:** $(now_utc)"
  if [ -n "$RUN_URL" ]; then echo "- **Last run:** ${RUN_URL}"; fi
  echo
  echo "Latest response body (first 2000 bytes):"
  echo
  echo '````'
  head -c 2000 "$RESPONSE_FILE"; echo
  echo '````'
} >"$body_file"

if [ -z "$open_issue" ]; then
  gh label create "$LABEL" --color B60205 \
    --description "Production uptime alerts from the readiness ping" --force
  gh issue create --title "$TITLE" --label "$LABEL" --body-file "$body_file"
else
  read -r number _ <<<"$open_issue"
  gh issue edit "$number" --body-file "$body_file"
  echo "Still down. Refreshed #${number}."
fi
