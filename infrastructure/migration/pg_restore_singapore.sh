#!/usr/bin/env bash
# Restore a us-east-1 dump into the ap-southeast-1 prod RDS.
# Usage: ./pg_restore_singapore.sh <dump.sql>
# Required env: SINGAPORE_DB_URL

set -euo pipefail

if [[ -z "${SINGAPORE_DB_URL:-}" ]]; then
  echo "ERROR: SINGAPORE_DB_URL not set. Source ~/.meydan-migration.env first." >&2
  exit 1
fi

DUMP="${1:?usage: $0 <dump.sql>}"
[[ -f "${DUMP}" ]] || { echo "ERROR: ${DUMP} not found" >&2; exit 1; }

TS="$(date -u +%Y%m%d_%H%M%S)"
LOG="/tmp/meydan-migration-pgrestore-${TS}.log"

echo "Restoring ${DUMP} → ap-southeast-1" | tee -a "${LOG}"
echo "Started: $(date -u)" | tee -a "${LOG}"

# Sanity: confirm the target DB is empty (no users, no tenants).
EXISTING_USERS=$(psql "${SINGAPORE_DB_URL}" -At -c \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='users';")
if [[ "${EXISTING_USERS}" == "1" ]]; then
  ROW_COUNT=$(psql "${SINGAPORE_DB_URL}" -At -c "SELECT COUNT(*) FROM public.users;")
  if [[ "${ROW_COUNT}" -gt 0 ]]; then
    echo "ERROR: Singapore DB already has ${ROW_COUNT} users. Refusing to restore on top." >&2
    echo "Drop and recreate the database first if this is intentional." >&2
    exit 1
  fi
fi

# Drop any leftover tenant schemas from Phase 2.8 smoke testing.
echo "Dropping any pre-existing tenant_* schemas..." | tee -a "${LOG}"
psql "${SINGAPORE_DB_URL}" -At -c \
  "SELECT 'DROP SCHEMA \"' || schema_name || '\" CASCADE;' FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%';" \
  | psql "${SINGAPORE_DB_URL}" 2>>"${LOG}" || true

# Drop public table contents (keep alembic version table to be re-applied by dump).
echo "Truncating public.* tables..." | tee -a "${LOG}"
psql "${SINGAPORE_DB_URL}" -At -c \
  "SELECT 'TRUNCATE \"' || table_name || '\" CASCADE;' FROM information_schema.tables WHERE table_schema='public';" \
  | psql "${SINGAPORE_DB_URL}" 2>>"${LOG}" || true

echo "Applying dump..." | tee -a "${LOG}"
psql --single-transaction --set ON_ERROR_STOP=on "${SINGAPORE_DB_URL}" < "${DUMP}" 2>>"${LOG}"

USER_COUNT=$(psql "${SINGAPORE_DB_URL}" -At -c "SELECT COUNT(*) FROM public.users;")
TENANT_COUNT=$(psql "${SINGAPORE_DB_URL}" -At -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%';")
echo "Done. Users: ${USER_COUNT}, tenant schemas: ${TENANT_COUNT}. Log: ${LOG}" | tee -a "${LOG}"
