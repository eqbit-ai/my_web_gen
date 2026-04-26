# Singapore migration scripts

Helpers for the runbook in `docs/Handover_Meydan_2026-04/11_singapore_migration_runbook.md`.

| Script | Purpose | Phase |
|---|---|---|
| `pg_dump_us_east.sh` | Dump `meydan_db` (public + tenant_*) from the us-east-1 RDS to a local SQL file. | 4.2 |
| `pg_restore_singapore.sh` | Drop and restore the dump into the ap-southeast-1 RDS. | 4.3 |
| `s3_sync_uploads.sh` | Cross-region sync of the user-uploads bucket. | 4.4 |
| `verify_migration.sh` | Compare row/schema counts between us-east-1 and ap-southeast-1 DBs. | 4.5 |

## Required env vars

```
US_EAST_DB_URL=postgresql://meydan:<pw>@<dev-rds-endpoint>:5432/meydan_db
SINGAPORE_DB_URL=postgresql://meydan:<pw>@<prod-rds-endpoint>:5432/meydan_db
US_EAST_UPLOADS_BUCKET=meydan-dev-uploads
SINGAPORE_UPLOADS_BUCKET=meydan-prod-uploads
```

Put them in `~/.meydan-migration.env` (chmod 600), source it, then run the scripts. Do **not** check this file in.

## Running

Test against a Singapore *test* database first (Phase 2). Only run for real during the maintenance window with the cluster scaled to zero.

```bash
source ~/.meydan-migration.env
./pg_dump_us_east.sh /tmp/dump.sql
./pg_restore_singapore.sh /tmp/dump.sql
./s3_sync_uploads.sh
./verify_migration.sh
```

Each script logs to `/tmp/meydan-migration-<step>-<ts>.log` and aborts on the first error.
