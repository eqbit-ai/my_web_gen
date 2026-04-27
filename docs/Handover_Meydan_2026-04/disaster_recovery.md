# Disaster Recovery Runbook — Singapore Production

Supplementary to the 10-document handover. Covers what is protected, what is not, and how to restore.

## What is protected today

| Component | Protection | Where it lives |
|---|---|---|
| **RDS PostgreSQL** | Multi-AZ (auto-failover within region) + 14-day automated backups + KMS encryption + deletion protection | `ap-southeast-1`, account `290172088819` |
| **ElastiCache Redis** | 7-day automated snapshot retention | `ap-southeast-1` |
| **Customer-deployed sites (S3)** | Versioning **enabled** (any object overwrite/delete is recoverable for 90 days), 99.999999999% intra-region durability | `s3://meydan-prod-sites-sg` |
| **ECR images** | Lifecycle keeps last 20 images per repo; untagged auto-expire at 7 days | `290172088819.dkr.ecr.ap-southeast-1.amazonaws.com/{meydan-api,meydan-frontend}` |
| **Secrets** | Secrets Manager — encrypted at rest, multi-AZ replicated | `meydan/prod/*` |
| **Code + IaC** | Git on GitHub `Meydanfz23/meydan-website-generator` | branches `dev`, `main` |
| **Configuration** | ECS task definitions are revision-controlled; `aws ecs describe-task-definition --task-definition meydan-prod-{api,worker,frontend}:N` returns any historical revision | ECS |

## What is NOT protected (accepted risk at handover)

- **Region-wide outage of `ap-southeast-1`** — no cross-region snapshot copies. The blast radius is the entire prod stack. Mitigations declined for cost (~$10–25/mo). If risk profile changes, set up an AWS Backup plan with copy to `ap-southeast-2` (Sydney) — instructions below under "Adding cross-region copies later".
- **Drone-strike-class infrastructure damage** — same as above. The reason `ap-southeast-1` was chosen over `me-central-1` is geopolitical stability, not engineering invulnerability.
- **Account-wide compromise** — if the prod IAM user is hijacked, an attacker with admin can delete data and snapshots in one region. Defence: enable MFA on the root + IAM user, and add CloudTrail-driven alarms for `Delete*` API calls.

## Backup inventory commands

Run these to verify daily that backups are flowing:

```bash
# Latest RDS automated snapshot
aws rds describe-db-snapshots --db-instance-identifier meydan-prod-db \
  --snapshot-type automated --region ap-southeast-1 --profile prod \
  --query 'DBSnapshots | sort_by(@, &SnapshotCreateTime) | [-1].{id:DBSnapshotIdentifier,created:SnapshotCreateTime}'

# RDS PITR window (the earliest restorable point)
aws rds describe-db-instances --db-instance-identifier meydan-prod-db \
  --region ap-southeast-1 --profile prod \
  --query 'DBInstances[0].{earliest:EarliestRestorableTime,latest:LatestRestorableTime}'

# Latest ElastiCache snapshot
aws elasticache describe-snapshots --cache-cluster-id meydan-prod-redis \
  --region ap-southeast-1 --profile prod \
  --query 'Snapshots | sort_by(@, &NodeSnapshots[0].SnapshotCreateTime) | [-1].{name:SnapshotName,created:NodeSnapshots[0].SnapshotCreateTime}'

# S3 object versions (sample)
aws s3api list-object-versions --bucket meydan-prod-sites-sg --max-items 5 --profile prod \
  --query 'Versions[].{key:Key,id:VersionId,modified:LastModified,latest:IsLatest}'
```

## Recovery procedures

### Scenario 1 — "A user reports their deployed site has been overwritten with a bad version"

```bash
# 1. List versions for that customer's index.html
aws s3api list-object-versions --bucket meydan-prod-sites-sg --prefix <slug>/index.html --profile prod

# 2. Restore by copying the previous version on top of the current key
aws s3api copy-object --bucket meydan-prod-sites-sg \
  --copy-source "meydan-prod-sites-sg/<slug>/index.html?versionId=<previous-version-id>" \
  --key "<slug>/index.html" --profile prod

# 3. Invalidate the user's CloudFront distribution if they're on a custom domain
aws cloudfront create-invalidation --distribution-id <id> --paths "/index.html" --profile prod
```

Recovery time: **under 5 minutes per site**. Recovery point: **last 90 days of versions**.

### Scenario 2 — "We need to roll back the database to before a bad migration ran"

Two paths.

**Path A — Point-in-time recovery (fast, preferred)**: restores the DB to any second within the 14-day backup window.

```bash
# 1. Restore to a NEW instance (cannot overwrite running prod)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier meydan-prod-db \
  --target-db-instance-identifier meydan-prod-db-restore \
  --restore-time 2026-04-27T18:30:00Z \
  --multi-az --db-subnet-group-name meydan-prod-db-subnet \
  --vpc-security-group-ids <DB_SG> \
  --no-publicly-accessible \
  --region ap-southeast-1 --profile prod

# 2. Wait for status=available (~10 min), then verify the data
aws rds wait db-instance-available --db-instance-identifier meydan-prod-db-restore \
  --region ap-southeast-1 --profile prod

# 3. Cut over: scale ECS API + Worker to 0, repoint Secrets Manager `meydan/prod/database-url`
#    at the new endpoint, force-redeploy. Keep the old instance for 7 days as belt-and-braces.
```

Recovery time: **~15 minutes** (10 min restore + 5 min cut-over). Recovery point: **any second in the last 14 days**.

**Path B — Restore from a specific automated snapshot**: same flow, replace `restore-db-instance-to-point-in-time` with `restore-db-instance-from-db-snapshot --db-snapshot-identifier <id>`.

### Scenario 3 — "An attacker / intern dropped the production database"

Deletion protection is on, so `aws rds delete-db-instance` will refuse without `--skip-final-snapshot --no-deletion-protection` — both intentional friction. If it still happens:

1. Check the **automated snapshots** — they survive instance deletion for the retention period.
2. Restore the latest automated snapshot to a new instance per Scenario 2 Path B.
3. Repoint Secrets Manager and redeploy.

Recovery time: **~15 minutes**. Recovery point: **last automated snapshot (≤24 h old)**.

### Scenario 4 — "The Singapore region is down"

This is the gap we accepted. Without cross-region snapshots, Singapore-down means the app is down until AWS recovers. Customer-deployed sites continue serving (they are S3 + intra-region replicated; an S3 region outage is rare but possible).

The plan if `ap-southeast-1` becomes a multi-day issue:

1. Stand up replacement infrastructure in `ap-southeast-2` (Sydney) using `infrastructure/aws/` templates — VPC, ECR, ALB, etc. ~1 hour.
2. Wait for `ap-southeast-1` access to return enough to take a manual `pg_dump` and `s3 sync`. If Singapore is genuinely lost, accept data loss back to last cross-region replication (which is none — we declined that protection).
3. Repoint Route 53 / CloudFront origin to the Sydney ALB.

This scenario is the reason cross-region copies are recommended even for small accounts. We've accepted the risk; if Singapore becomes problematic we revisit.

## Adding cross-region copies later (when ready)

```bash
# Create AWS Backup vault in destination region first
aws backup create-backup-vault --backup-vault-name meydan-prod-dr-sydney \
  --region ap-southeast-2 --profile prod

# Then in source region, define a plan that copies daily
aws backup create-backup-plan --region ap-southeast-1 --profile prod \
  --backup-plan '{
    "BackupPlanName": "meydan-prod-daily-with-cross-region-copy",
    "Rules": [{
      "RuleName": "DailyBackup",
      "TargetBackupVaultName": "Default",
      "ScheduleExpression": "cron(0 19 ? * * *)",
      "StartWindowMinutes": 60,
      "CompletionWindowMinutes": 180,
      "Lifecycle": { "DeleteAfterDays": 30 },
      "CopyActions": [{
        "DestinationBackupVaultArn": "arn:aws:backup:ap-southeast-2:290172088819:backup-vault:meydan-prod-dr-sydney",
        "Lifecycle": { "DeleteAfterDays": 30 }
      }]
    }]
  }'

# Then assign resources (RDS + ElastiCache) to the plan via aws backup put-backup-selection.
```

Cost at our scale: ~$10–25 / month.

## Restore drill (recommended quarterly)

Once a quarter, run Scenario 2 Path A end-to-end into a non-prod restore instance. Drop it after verifying. This proves the backups are real and tests the procedure when the team has time, not at 3 AM mid-incident.

## Sign-off

| Item | Status | Verified by | Date |
|---|---|---|---|
| RDS Multi-AZ + 14-day backups + deletion protection | ✓ | Migration session | 2026-04-26 |
| ElastiCache 7-day snapshots | ✓ | Migration session | 2026-04-26 |
| S3 versioning + 90-day non-current expiry | ✓ | DR hardening | 2026-04-27 |
| ECR lifecycle (20 images, 7-day untagged expiry) | ✓ | DR hardening | 2026-04-27 |
| Cross-region snapshot copies | ✗ (accepted, $10–25/mo declined) | — | 2026-04-27 |
| Restore drill | ✗ (recommended quarterly) | — | — |
