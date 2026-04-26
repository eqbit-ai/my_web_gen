# 7. Deployment Runbook

Two paths covered:
- **Day-to-day deploys** — `git push` triggers the right GitHub Actions workflow. You will use this 99 % of the time.
- **First-time provisioning** — taking a clean AWS account to a running environment. You do this once per environment.

## Branches and environments

| Branch | Triggers workflow | AWS account | Region | Public URL |
|---|---|---|---|---|
| `dev` | `.github/workflows/deploy-dev.yml` | `371170753756` (dev) | `us-east-1` | `https://meydanfzai.com` (apex) **and** `https://dev.meydanfzai.com` (Cloudflare-proxied CNAME to the dev ALB). Both currently serve the same dev environment. |
| `main` | `.github/workflows/deploy-prod.yml` | `290172088819` (prod) | `ap-southeast-1` (Singapore) | Not yet provisioned. The prod ECS cluster `meydan-prod-cluster` does not exist at time of handover — prod migration is paused pending client sign-off. |

> Legacy branches `production` and `staging` exist in the remote but are not wired to any workflow. They are stale initial commits. Safe to delete after handover.

**Every push** to `dev` or `main` also runs `ci.yml` (lint + test + security scan + frontend build + SonarCloud scan).

## Day-to-day deploy — what actually happens on `git push`

1. You push to `dev`.
2. `ci.yml` runs in parallel: Python lint + pytest, Frontend build (with `CI=true` so ESLint warnings fail the job), Security scan (Trivy or equivalent), SonarCloud analysis. Any red job surfaces in the PR/commit.
3. `deploy-dev.yml` runs in parallel to `ci.yml`:
   - Builds `meydan-api` + `meydan-frontend` images with `--platform linux/amd64` and pushes to ECR `371170753756.dkr.ecr.us-east-1.amazonaws.com`.
   - `aws ecs update-service --force-new-deployment` on each of `meydan-dev-api`, `meydan-dev-worker`, `meydan-dev-frontend`.
   - `aws ecs wait services-stable` waits up to ~10 minutes for the new task set to reach steady state.
4. `entrypoint.sh` runs `alembic upgrade head` before gunicorn boots, so migrations apply automatically on the API container.

Pushing to `main` follows the same pattern but against the prod account/region with the `_PROD` secrets (see `deploy-prod.yml`). At present this workflow cannot succeed because the prod cluster does not exist.

> **Known CI annoyance**: the `aws ecs wait services-stable` step can time out even when the deploy actually succeeds — ECS reports steady state a few minutes later and the container is healthy. If the Wait step is red but the `/api/health` endpoint responds 200, treat the deploy as successful. Tracked in `10_known_issues_and_support.md`.

## Prerequisites

### Accounts
- **AWS account** with administrator access. Production region at handover: **ap-southeast-1** (Singapore). Dev/staging region: **us-east-1**.
- **GitHub** access to the private `meydan-ai` repository.
- **Cloudflare** account — authoritative DNS for `meydanfzai.com` (apex NS delegated at OpenProvider).
- **OpenProvider** reseller account — domain registration.
- **Resend** account with `meydanfzai.com` domain verified.
- **OpenAI** and **Anthropic** API keys with production quotas.
- **Sentry** project (optional — set `SENTRY_DSN` to enable).

### Local tools
- Docker Desktop (for `--platform linux/amd64` builds — **critical**, see below).
- AWS CLI v2, configured (`aws configure`).
- GitHub CLI (`gh`), optional.
- Node 18+, Python 3.12+, `psql` client (for one-off SQL).

### Secrets to have on hand before deploying
All of the env vars listed in `08_environment_and_secrets.md`.

## First-time provisioning — numbered steps

Use this only when bringing up a new environment (e.g. the prod cluster in ap-southeast-1). For routine deploys see "Day-to-day deploy" above.

> Throughout, substitute your values. Everything assumes `export AWS_REGION=ap-southeast-1`.

### 1. Provision the core stack
```bash
cd infrastructure/aws
aws cloudformation deploy \
  --stack-name meydan-core \
  --template-file cloudformation.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      Environment=production \
      DomainName=meydanfzai.com
```
This creates: VPC, private/public subnets, ECS cluster, ALB, target groups, RDS (PostgreSQL 15), ElastiCache Redis, CloudWatch log groups, S3 asset buckets, IAM roles.

### 2. Store secrets in AWS Secrets Manager
```bash
aws secretsmanager create-secret --name meydan/prod/env --secret-string file://prod.env.json
```
`prod.env.json` is a JSON map of every env var from `08_environment_and_secrets.md`. The ECS task definitions resolve each entry at runtime.

### 3. Push Docker images to ECR
```bash
aws ecr create-repository --repository-name meydan-api  # once
aws ecr create-repository --repository-name meydan-frontend

docker buildx build --platform linux/amd64 -t meydan-api ./backend
docker buildx build --platform linux/amd64 -t meydan-frontend ./frontend
```
**CRITICAL**: always build with `--platform linux/amd64`. Building on Apple Silicon without this flag produces an arm64 image that ECS Fargate cannot run; the task will crash-loop with no clear error.

Tag and push:
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag meydan-api     $ECR/meydan-api:latest
docker tag meydan-frontend $ECR/meydan-frontend:latest
docker push $ECR/meydan-api:latest
docker push $ECR/meydan-frontend:latest
```

### 4. Register ECS task definitions
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-api.json
aws ecs register-task-definition --cli-input-json file://ecs-task-worker.json
```
`entrypoint.sh` runs `alembic upgrade head` automatically on API boot, so the database migrates itself on the first deploy. The worker container has `SKIP_MIGRATIONS=1`.

### 5. Create ECS services
```bash
aws ecs create-service --cli-input-json file://ecs-service-api.json
aws ecs create-service --cli-input-json file://ecs-service-worker.json
```
Three Fargate services run: **API**, **Worker**, **Frontend**. Desired count at handover: API × 2, Worker × 2, Frontend × 2.

### 6. Bootstrap the first admin user
Once the API is up and migrations have run:
```bash
# Sign up as the admin via the UI, verify the email, then:
psql "$DATABASE_URL" -c "UPDATE public.users SET is_admin=true, approved=true, tokens_remaining=10000000 WHERE email='admin@meydanfzai.com';"
```

### 7. Apply observability config
```bash
./deploy-observability.sh       # applies dashboards + alarms + WAF
```

### 8. Point DNS
At **Cloudflare** (authoritative for `meydanfzai.com`):
- `A meydanfzai.com → ALB IP` (or CNAME to CloudFront if using the CDN path)
- `CNAME www.meydanfzai.com → meydanfzai.com`
- `CNAME *.meydanfzai.com → CloudFront distribution` (for tenant subdomains)
- Resend-verification records (DKIM, SPF, DMARC) — values come from the Resend dashboard.

> **Do not** edit these records in Route 53 — the authoritative zone is Cloudflare. Route 53 records in the AWS account are cosmetic and not resolved by the internet.

### 9. Smoke-test
See the post-deployment checks section below.

## Post-deployment checks

Open each URL and confirm the expected response before announcing the deploy:

| Check | URL | Expected |
|---|---|---|
| Public health | `https://meydanfzai.com/api/health` | `{"status":"ok"}` |
| Deep health | `https://meydanfzai.com/api/health/deep` | `{"db":"ok","redis":"ok"}` |
| Frontend shell | `https://meydanfzai.com/` | Landing page renders, no console errors. |
| OpenAPI | `https://meydanfzai.com/api/openapi.json` | JSON, 200. |
| Login | UI login with the admin account | JWT received; dashboard loads. |
| Sample generation | Dashboard → New site, a two-sentence brief | SSE events stream, a site is produced in under 120 s. |
| Sample deploy | Deploy the generated site to a `*.meydanfzai.com` subdomain | URL returns 200 within 60 s of invalidation. |

**Logs to inspect**: CloudWatch Logs groups `/ecs/meydan-api` and `/ecs/meydan-worker`. Filter by the correlation ID returned by the smoke-test deploy.

**Metrics to verify**: CloudWatch dashboard `meydan-production` panels: request rate > 0, p95 < 1 s on non-generation routes, 5xx rate < 1 %.

## Rollback procedure

### If a new image is bad (API or worker)
```bash
# Identify the last-known-good task definition revision:
aws ecs describe-services --cluster meydan --services meydan-api | jq '.services[0].taskDefinition'
# Roll back:
aws ecs update-service --cluster meydan --service meydan-api \
  --task-definition meydan-api:<N-1>  --force-new-deployment
```
Do the same for `meydan-worker` or `meydan-frontend` as needed.

### If a migration is bad
1. Revert the Alembic revision locally: `alembic downgrade -1`.
2. Generate a forward-compatible revision that *un-applies* the change.
3. Commit, rebuild, redeploy. **Never** edit a merged migration in place — write a new one.

### If CloudFront misbehaves
- Primary site (`meydanfzai.com`): distribution `E368CULECTE3G5`. Create an invalidation for `/*` from the AWS console.
- Tenant sites: the admin panel has a one-click redeploy-and-invalidate (`POST /api/deploy/{site_id}/redeploy`).

### Full DR restore
See the disaster-recovery snapshot rotation plan documented in `infrastructure/aws/OPERATIONS-GUIDE.md`. RDS automated backups are retained 14 days; cross-region snapshots land in `us-west-2`. Deletion protection is on.

## Local setup — a new developer to running product in under 30 minutes

```bash
# 1. Clone and configure
git clone git@github.com:meydan-ai/meydan-ai.git
cd meydan-ai
cp backend/.env.example backend/.env      # fill in the keys (at minimum: DATABASE_URL, JWT_SECRET, OPENAI_API_KEY, ANTHROPIC_API_KEY)

# 2. Bring up the stack
docker compose up -d --build
# Services come up on:
#   Frontend: http://localhost:3000
#   API:      http://localhost:8000  (Swagger: http://localhost:8000/api/docs)
#   Postgres: localhost:5432
#   Redis:    localhost:6379

# 3. Wait for migrations
docker compose logs -f api    # look for "Application startup complete"

# 4. Create a local admin
docker compose exec postgres psql -U meydan -d meydan_db -c \
  "INSERT INTO public.users (email, hashed_password, full_name, company_name, license_number, is_admin, approved, email_verified_at, tokens_remaining)
   VALUES ('admin@localhost', '<bcrypt-of-password>', 'Local Admin', 'Dev', 'DEV-0001', true, true, now(), 1000000);"

# 5. Log in at http://localhost:3000 with admin@localhost / your password.
```

A shorter path — skip Docker and run Postgres/Redis locally, then:
```bash
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# in another tab:
cd frontend && npm ci && npm start
```
