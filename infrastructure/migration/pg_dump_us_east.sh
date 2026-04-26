#!/usr/bin/env bash
# Dump public + tenant_* schemas from the us-east-1 dev RDS.
# Usage: ./pg_dump_us_east.sh <output.sql>
# Required env: US_EAST_DB_URL

set -euo pipefail

if [[ -z "${US_EAST_DB_URL:-}" ]]; then
  echo "ERROR: US_EAST_DB_URL not set. Source ~/.meydan-migration.env first." >&2
  exit 1
fi

OUT="${1:?usage: $0 <output.sql>}"
TS="$(date -u +%Y%m%d_%H%M%S)"
LOG="/tmp/meydan-migration-pgdump-${TS}.log"

echo "Dumping us-east-1 → ${OUT}" | tee -a "${LOG}"
echo "Started: $(date -u)" | tee -a "${LOG}"

# Discover tenant schemas first (pg_dump --schema does not glob server-side
# in older clients; we fetch the list and pass each explicitly).
TENANT_SCHEMAS=$(psql "${US_EAST_DB_URL}" -At -c \
  "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%' ORDER BY schema_name;")

if [[ -z "${TENANT_SCHEMAS}" ]]; then
  echo "WARNING: no tenant_* schemas found. Continuing with public only." | tee -a "${LOG}"
fi

SCHEMA_FLAGS=(--schema=public)
while IFS= read -r s; do
  [[ -z "${s}" ]] && continue
  SCHEMA_FLAGS+=(--schema="${s}")
done <<< "${TENANT_SCHEMAS}"

echo "Dumping schemas: public $(echo "${TENANT_SCHEMAS}" | wc -l | tr -d ' ') tenant schema(s)" | tee -a "${LOG}"

pg_dump \
  --no-owner --no-privileges --no-publications --no-subscriptions \
  --format=plain \
  --file="${OUT}" \
  "${SCHEMA_FLAGS[@]}" \
  "${US_EAST_DB_URL}" 2>>"${LOG}"

SIZE=$(du -h "${OUT}" | cut -f1)
echo "Done. Output ${OUT} (${SIZE}). Log: ${LOG}" | tee -a "${LOG}"
