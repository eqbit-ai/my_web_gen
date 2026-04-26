#!/usr/bin/env bash
# Cross-region sync of the user-uploads bucket from us-east-1 → ap-southeast-1.
# The deployed-sites bucket is intentionally NOT synced — customer sites stay in us-east-1
# (Decision 1 in the runbook). Re-read 11_singapore_migration_runbook.md if unsure.
#
# Usage: ./s3_sync_uploads.sh [--dry-run]
# Required env: US_EAST_UPLOADS_BUCKET, SINGAPORE_UPLOADS_BUCKET

set -euo pipefail

if [[ -z "${US_EAST_UPLOADS_BUCKET:-}" || -z "${SINGAPORE_UPLOADS_BUCKET:-}" ]]; then
  echo "ERROR: US_EAST_UPLOADS_BUCKET / SINGAPORE_UPLOADS_BUCKET not set." >&2
  exit 1
fi

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN="--dryrun"
fi

TS="$(date -u +%Y%m%d_%H%M%S)"
LOG="/tmp/meydan-migration-s3sync-${TS}.log"

echo "Sync s3://${US_EAST_UPLOADS_BUCKET} → s3://${SINGAPORE_UPLOADS_BUCKET} ${DRY_RUN}" | tee -a "${LOG}"
echo "Started: $(date -u)" | tee -a "${LOG}"

aws s3 sync \
  "s3://${US_EAST_UPLOADS_BUCKET}" \
  "s3://${SINGAPORE_UPLOADS_BUCKET}" \
  --source-region us-east-1 \
  --region ap-southeast-1 \
  --no-progress \
  ${DRY_RUN} 2>&1 | tee -a "${LOG}"

SRC_COUNT=$(aws s3 ls "s3://${US_EAST_UPLOADS_BUCKET}" --recursive --region us-east-1 | wc -l | tr -d ' ')
DST_COUNT=$(aws s3 ls "s3://${SINGAPORE_UPLOADS_BUCKET}" --recursive --region ap-southeast-1 | wc -l | tr -d ' ')
echo "Source objects: ${SRC_COUNT}, destination objects: ${DST_COUNT}." | tee -a "${LOG}"

if [[ -z "${DRY_RUN}" && "${SRC_COUNT}" != "${DST_COUNT}" ]]; then
  echo "WARNING: object counts differ. Re-run sync or investigate." | tee -a "${LOG}"
  exit 2
fi

echo "Done. Log: ${LOG}" | tee -a "${LOG}"
