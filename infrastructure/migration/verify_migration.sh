#!/usr/bin/env bash
# Compare row/schema counts between us-east-1 and ap-southeast-1 DBs.
# Usage: ./verify_migration.sh
# Required env: US_EAST_DB_URL, SINGAPORE_DB_URL

set -euo pipefail

if [[ -z "${US_EAST_DB_URL:-}" || -z "${SINGAPORE_DB_URL:-}" ]]; then
  echo "ERROR: US_EAST_DB_URL / SINGAPORE_DB_URL not set." >&2
  exit 1
fi

TS="$(date -u +%Y%m%d_%H%M%S)"
LOG="/tmp/meydan-migration-verify-${TS}.log"

count() {
  psql "$1" -At -c "$2" 2>/dev/null
}

declare -a CHECKS=(
  "users|SELECT COUNT(*) FROM public.users;"
  "sites|SELECT COUNT(*) FROM public.sites;"
  "tenant_schemas|SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%';"
  "edit_logs|SELECT COUNT(*) FROM public.edit_logs;"
  "token_transactions|SELECT COUNT(*) FROM public.token_transactions;"
)

FAIL=0
echo "Check                | us-east-1 | ap-southeast-1 | result" | tee -a "${LOG}"
echo "---------------------+-----------+----------------+-------" | tee -a "${LOG}"
for entry in "${CHECKS[@]}"; do
  name="${entry%%|*}"
  query="${entry#*|}"
  src=$(count "${US_EAST_DB_URL}" "${query}" || echo "ERR")
  dst=$(count "${SINGAPORE_DB_URL}" "${query}" || echo "ERR")
  if [[ "${src}" == "${dst}" ]]; then
    res="OK"
  else
    res="MISMATCH"
    FAIL=1
  fi
  printf "%-20s | %9s | %14s | %s\n" "${name}" "${src}" "${dst}" "${res}" | tee -a "${LOG}"
done

echo "" | tee -a "${LOG}"
if [[ "${FAIL}" -eq 0 ]]; then
  echo "All checks passed. Log: ${LOG}" | tee -a "${LOG}"
else
  echo "FAIL — at least one row count mismatch. Inspect before proceeding to DNS cut-over." | tee -a "${LOG}"
  exit 1
fi
