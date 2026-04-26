# 11. Singapore Production Migration Runbook

End-to-end migration: stand up `ap-southeast-1` (Singapore) prod from zero, move live data and traffic from `us-east-1` (account `371170753756`) to Singapore (account `290172088819`), and reset `us-east-1` to a clean dev environment.

> **Read this whole document before starting.** Do not skip Phase 0. The cut-over (Phase 4) is the only step that touches user-visible state — everything before it is non-destructive and can be run at any time.

## 0. Decisions on file (confirm before Phase 4)

| Decision | Default | Confirm? |
|---|---|---|
| Customer-deployed sites (S3 buckets that serve `meydanfzai.com/*` customer pages) | **Stay in `us-east-1`** — zero customer-facing change, no customer DNS edits required. The dev S3 buckets become "deployed-sites" buckets shared with prod. | ☐ |
| Application stack (API, Worker, Frontend, RDS, Redis, ALB) | **Move to `ap-southeast-1`** | ☐ |
| Maintenance window | TBD — recommend Saturday 02:00–04:00 GST (low traffic) | ☐ |
| Decommission us-east-1 prod data after migration? | **No** — keep snapshot for 30 days, then wipe and re-seed as dev | ☐ |
| User-facing comms | Email + status banner 48 h ahead | ☐ |

If any answer changes, the runbook needs revising before execution.

## 1. Pre-flight checklist

Run all of this **before** the maintenance window. Nothing here is destructive.

### 1.1 Access verification
- [ ] AWS CLI authenticated against **dev** account `371170753756` — `aws sts get-caller-identity` returns the dev account.
- [ ] AWS CLI profile `prod` configured for account `290172088819` — `aws sts get-caller-identity --profile prod` returns the prod account.
- [ ] Cloudflare API token in hand (zone-edit on `meydanfzai.com`).
- [ ] OpenProvider login in hand.
- [ ] All `_PROD` GitHub secrets exist on the repo (`AWS_ACCESS_KEY_ID_PROD`, `AWS_SECRET_ACCESS_KEY_PROD`).

### 1.2 Env-var inventory (Singapore secrets you'll need)
Source: `08_environment_and_secrets.md`. Copy every value out of the dev ECS task definition into a local `.env.singapore-prod` you delete after Phase 3.

```bash
aws ecs describe-task-definition \
  --task-definition meydan-dev-api \
  --region us-east-1 \
  --query 'taskDefinition.containerDefinitions[0].{env:environment,secrets:secrets}' \
  > dev-task-env.json
```

Anything in `secrets` is a Secrets Manager reference — fetch the actual value with `aws secretsmanager get-secret-value` from us-east-1 and write it into the new Singapore Secrets Manager in Phase 2.

**Critical**: `JWT_SECRET` MUST be copied byte-for-byte. If it differs between us-east-1 and ap-southeast-1, every existing user session is invalidated on cut-over.

### 1.3 Customer-domain inventory
- [ ] Pull list of customers using custom domains:
  ```sql
  SELECT user_id, custom_domain, cloudfront_distribution_id, s3_bucket
  FROM sites WHERE custom_domain IS NOT NULL;
  ```
- [ ] For each, confirm the S3 bucket is in `us-east-1` and the CloudFront distribution stays as-is (Decision 1).

### 1.4 Capacity check
- [ ] Singapore service quotas: VPC, EIP, ALB, ECS task count. File quota-increase tickets **48 h ahead** if any are at default and you need more than 5 of anything.

## 2. Phase 1 — Provision Singapore (no downtime)

Goal: full app stack running in Singapore, behind a temporary hostname (e.g. `singapore-staging.meydanfzai.com`), serving an empty database. Production traffic still on us-east-1.

### 2.1 ECR repos
```bash
export AWS_PROFILE=prod
export AWS_REGION=ap-southeast-1
aws ecr create-repository --repository-name meydan-api --image-scanning-configuration scanOnPush=true
aws ecr create-repository --repository-name meydan-frontend --image-scanning-configuration scanOnPush=true
```

### 2.2 CloudFormation stack
```bash
cd infrastructure/aws
aws cloudformation deploy \
  --stack-name meydan-prod \
  --template-file cloudformation.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-southeast-1 \
  --parameter-overrides \
      Environment=production \
      DomainName=meydanfzai.com \
      DBInstanceClass=db.r6g.xlarge \
      DBMasterUsername=meydan \
      DBMasterPassword="<generate-32-char>" \
      RedisNodeType=cache.r6g.large \
      ApiDesiredCount=2 \
      WorkerDesiredCount=2
```

This produces: VPC, subnets, NAT, ALB, security groups, RDS PostgreSQL 15 (Multi-AZ), ElastiCache Redis, ECS cluster + task defs + 3 services, S3 uploads bucket, ACM cert, CloudFront OAC, IAM roles. ~25 min.

### 2.3 ACM cert in us-east-1 (CloudFront requirement)
CloudFront certs **must** live in `us-east-1`. The CFN stack puts the regional cert in Singapore for the ALB; you also need:
```bash
aws acm request-certificate \
  --domain-name meydanfzai.com --subject-alternative-names "*.meydanfzai.com" \
  --validation-method DNS \
  --region us-east-1 \
  --profile prod
```
Add the validation CNAME(s) in Cloudflare dashboard. Wait for `ISSUED`.

### 2.4 Secrets Manager (Singapore)
Author every secret listed in `08_environment_and_secrets.md`:
```bash
for kv in \
  "meydan/prod/JWT_SECRET=<copied from us-east-1>" \
  "meydan/prod/ANTHROPIC_API_KEY=<value>" \
  "meydan/prod/OPENAI_API_KEY=<value>" \
  "meydan/prod/RESEND_API_KEY=<value>" \
  "meydan/prod/CLOUDFLARE_API_TOKEN=<value>" \
  "meydan/prod/OPENPROVIDER_PASSWORD=<value>" \
  "meydan/prod/DATABASE_URL=<rds-endpoint>" \
  "meydan/prod/REDIS_URL=<elasticache-endpoint>" \
  ; do
    name="${kv%%=*}"; value="${kv#*=}"
    aws secretsmanager create-secret --name "$name" --secret-string "$value" --region ap-southeast-1 --profile prod
done
```

Update the Singapore ECS task defs to reference these (the CFN template emits placeholders; edit the rendered task def JSON or run a follow-up `update-task-definition`).

### 2.5 Build & push images
First push to `main` will do this via `deploy-prod.yml`. To smoke-test ahead of that:
```bash
docker build --platform linux/amd64 -t 290172088819.dkr.ecr.ap-southeast-1.amazonaws.com/meydan-api:smoketest -f backend/Dockerfile backend/
aws ecr get-login-password --region ap-southeast-1 --profile prod | docker login --username AWS --password-stdin 290172088819.dkr.ecr.ap-southeast-1.amazonaws.com
docker push 290172088819.dkr.ecr.ap-southeast-1.amazonaws.com/meydan-api:smoketest
```

### 2.6 Apply Alembic migrations against the empty Singapore DB
```bash
DATABASE_URL="postgresql+asyncpg://meydan:<pw>@<rds-endpoint>:5432/meydan_db" \
  alembic -c backend/alembic.ini upgrade head
```

### 2.7 Bring services to steady state
```bash
aws ecs update-service --cluster meydan-prod-cluster --service meydan-prod-api --desired-count 1 --region ap-southeast-1 --profile prod
aws ecs update-service --cluster meydan-prod-cluster --service meydan-prod-worker --desired-count 1 --region ap-southeast-1 --profile prod
aws ecs update-service --cluster meydan-prod-cluster --service meydan-prod-frontend --desired-count 1 --region ap-southeast-1 --profile prod
aws ecs wait services-stable --cluster meydan-prod-cluster \
  --services meydan-prod-api meydan-prod-worker meydan-prod-frontend \
  --region ap-southeast-1 --profile prod
```

### 2.8 Temporary DNS for verification
In Cloudflare add a `CNAME singapore-staging` → ALB DNS name (DNS-only, grey cloud).
- [ ] `curl https://singapore-staging.meydanfzai.com/api/health` returns `{"status":"ok"}`
- [ ] Sign up a throwaway user, generate a website, deploy it. Confirm everything works against the empty Singapore DB.

End of Phase 1. **Production traffic is still on us-east-1. No downtime so far.**

## 3. Phase 2 — Pre-cutover verification (no downtime)

### 3.1 Pre-warm the data path
- [ ] Author the migration scripts and store them at `infrastructure/migration/`. See "Helper scripts" at the bottom of this doc.
- [ ] Test `pg_dump` end-to-end against a **read replica** of the dev RDS, restored into a *separate test* Singapore DB. Verify row counts and that `tenant_*` schemas restore cleanly.
- [ ] Test S3 sync (`aws s3 sync`) from us-east-1 uploads bucket to Singapore uploads bucket, in dry-run mode (`--dryrun`).

### 3.2 Comms
- [ ] T-48 h: send maintenance email to all users (template in Phase 6 below).
- [ ] T-24 h: drop Cloudflare TTL on `meydanfzai.com` and `www.meydanfzai.com` to **60 s**.
- [ ] T-2 h: status banner on the dashboard ("Scheduled maintenance — service unavailable from HH:MM to HH:MM GST").

## 4. Phase 3 — Cut-over (maintenance window)

This is the only step with downtime. Budget **45 minutes**, not 30.

### 4.1 T-0: Freeze writes on us-east-1
```bash
# Scale API + Worker to zero so no new writes land
aws ecs update-service --cluster meydan-dev-cluster --service meydan-dev-api --desired-count 0 --region us-east-1
aws ecs update-service --cluster meydan-dev-cluster --service meydan-dev-worker --desired-count 0 --region us-east-1
aws ecs wait services-stable --cluster meydan-dev-cluster \
  --services meydan-dev-api meydan-dev-worker --region us-east-1
```
The frontend stays up so users see the maintenance banner. ALB returns 503 for `/api/*` because no targets are healthy.

### 4.2 T+2 min: Final pg_dump
```bash
bash infrastructure/migration/pg_dump_us_east.sh > /tmp/meydan_us_east_$(date -u +%Y%m%d_%H%M%S).sql
```
Expected size at handover: ~150–400 MB. Time: 1–3 min.

### 4.3 T+5 min: Restore into Singapore
```bash
bash infrastructure/migration/pg_restore_singapore.sh /tmp/meydan_us_east_*.sql
```
Time: 2–5 min. The Singapore DB is currently empty (or has the throwaway user from Phase 2.8 — drop and recreate the database first).

### 4.4 T+10 min: S3 sync (uploads only — deployed sites stay)
```bash
bash infrastructure/migration/s3_sync_uploads.sh
```
Time: depends on volume. At handover: ~5–20 GB → 5–15 min.

### 4.5 T+25 min: Verification queries against Singapore DB
- [ ] `SELECT COUNT(*) FROM public.users;` matches us-east-1
- [ ] `SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%';` matches us-east-1
- [ ] Pick three random users — their `sites` and `edit_logs` rows present
- [ ] One generated site loads end-to-end via `singapore-staging.meydanfzai.com`

### 4.6 T+30 min: DNS cut-over (Cloudflare)
Edit in the Cloudflare dashboard (or via API):

| Record | From | To |
|---|---|---|
| `meydanfzai.com` (A) | us-east-1 ALB IPs | CNAME-flatten → Singapore ALB DNS name |
| `www.meydanfzai.com` (CNAME) | us-east-1 ALB | Singapore ALB |
| `dev.meydanfzai.com` (CNAME) | us-east-1 ALB | **unchanged** — stays as dev |

Set proxy mode to **orange-cloud (proxied)** for the apex and `www` to also fix open issue C1 from `10_known_issues_and_support.md` in the same operation.

### 4.7 T+35 min: Smoke tests against `meydanfzai.com`
- [ ] `curl https://meydanfzai.com/api/health` → `200 OK`
- [ ] Login with an existing user account works (validates JWT_SECRET copy)
- [ ] One existing user's deployed site still loads (validates customer-site DNS untouched)
- [ ] Generate a new site end-to-end (validates LLM clients, Resend, S3 deploy, Cloudflare)

### 4.8 T+45 min: Open the gates
- [ ] Remove maintenance banner.
- [ ] Email the all-clear to the same list.
- [ ] Bring TTLs back up to default (3600 s) once you've watched traffic for 1 h.

## 5. Phase 4 — Post-cutover (next 24 h)

- [ ] CloudWatch dashboard `meydan-production` shows green panels.
- [ ] Error-rate alarm not triggered.
- [ ] No support tickets above baseline.
- [ ] Customer-domain sites still resolve (spot-check 3 customers).
- [ ] Take a Singapore RDS snapshot manually as a safety belt.
- [ ] Cross-region snapshot copy schedule confirmed (target: us-west-2 per current DR posture — need to revisit; consider `ap-southeast-2` Sydney as the new DR target since it's geographically closer to the new prod).

## 6. Phase 5 — Reset us-east-1 to a clean dev env (T+30 days)

Wait 30 days before doing this — it's the only un-rollbackable step.

- [ ] Final RDS snapshot of the legacy us-east-1 DB → keep for 90 days.
- [ ] `DROP DATABASE meydan_db; CREATE DATABASE meydan_db;` then `alembic upgrade head` against an empty schema.
- [ ] Empty the uploads bucket: `aws s3 rm s3://meydan-dev-uploads --recursive`.
- [ ] Leave deployed-sites bucket alone (it's serving customers).
- [ ] Re-seed dev with a couple of test accounts.
- [ ] Update `08_environment_and_secrets.md` to remove "us-east-1 = de-facto prod" caveat.

## 7. Rollback playbook (if Phase 3 goes wrong)

Trigger criteria: any smoke test in 4.7 fails, or 4.6 takes longer than 10 min and traffic is half-broken.

```bash
# 1. Revert DNS — point apex back at us-east-1 ALB (proxied OFF, exactly as before)
# (use Cloudflare dashboard; record IDs in reference-dns-cloudflare.md)

# 2. Bring us-east-1 services back up
aws ecs update-service --cluster meydan-dev-cluster --service meydan-dev-api --desired-count 2 --region us-east-1
aws ecs update-service --cluster meydan-dev-cluster --service meydan-dev-worker --desired-count 2 --region us-east-1
```

Rollback window: **safe for 60 minutes after T-0**. Beyond that, any writes accepted by Singapore are not in us-east-1, and rollback means data loss for those users. If you're past 60 min and Singapore is broken, recover forward, do not roll back.

## 8. Comms templates

### Pre-maintenance email (T-48 h)
> **Subject**: Scheduled maintenance — Meydan Free Zone, [Sat DD MMM] 02:00–04:00 GST
>
> Hi [name],
>
> We're moving our infrastructure to a new region for better performance. Your dashboard and the website generator will be unavailable for up to 60 minutes during the window above. Your published websites will stay online throughout — only the editor and login go offline.
>
> No action is required from you. We'll email you as soon as we're back.
>
> Thanks,
> The Meydan AI team

### All-clear email (post Phase 3)
> **Subject**: Meydan Free Zone — back online
>
> The migration completed at HH:MM GST. Everything is green. If you see anything off, reply to this email.

## 9. Helper scripts to author at `infrastructure/migration/`

These don't exist yet — author them as part of Phase 2 and check them into `dev` before the maintenance window:

- `pg_dump_us_east.sh` — `pg_dump --no-owner --no-privileges --schema=public --schema='tenant_*'` of dev RDS to stdout
- `pg_restore_singapore.sh` — drop existing public + tenant schemas, `psql < dump.sql` against Singapore RDS
- `s3_sync_uploads.sh` — `aws s3 sync s3://meydan-dev-uploads s3://meydan-prod-uploads --source-region us-east-1 --region ap-southeast-1`
- `verify_migration.sh` — run the verification SQL from 4.5 against both DBs and diff

Each script should fail loud (`set -euo pipefail`) and log to `/tmp/meydan-migration-<step>-<ts>.log`.

## 10. Sign-off

The migration is complete when:
- [ ] Phase 4 (24 h post-cutover) shows zero abnormal alarms
- [ ] No customer reports a regression
- [ ] `00_README.md` and `07_deployment_runbook.md` updated to reflect new reality (us-east-1 = dev only)
- [ ] This runbook annotated with actual times taken vs. estimates, for the next migration

---

**Authors**: Migration runbook drafted 2026-04-26. Update this footer after the actual run with the executor name and date.
