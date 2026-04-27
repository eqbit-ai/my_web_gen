# 8. Environment and Secrets

Every environment variable the product reads. Plain values are set in the ECS task definition `environment` array; sensitive values are pulled at task-start from AWS Secrets Manager via `valueFrom` ARNs.

## Source of truth

- **Live source**: the running ECS task definition. Inspect with:
  ```bash
  aws ecs describe-task-definition --task-definition meydan-prod-api \
    --region ap-southeast-1 --profile prod \
    --query 'taskDefinition.containerDefinitions[0].{env:environment,secrets:secrets[].name}'
  ```
- **Documented baseline**: `backend/.env.example` (every var with example value and one-line comment).

## Environment variable table

| Name | Purpose | Example value | Source |
|---|---|---|---|
| `ENVIRONMENT` | `production` / `staging` / `dev`. Gates Swagger UI and some defaults. | `production` | ECS env (plain) |
| `AWS_REGION` | Default region for boto3 clients. | `ap-southeast-1` | ECS env (plain) |
| `AWS_S3_DEPLOY_BUCKET` | Bucket for customer-deployed sites. | `meydan-prod-sites-sg` | ECS env (plain) |
| `API_BASE_URL` | Used in email links and worker → API callbacks. | `https://meydanfzai.com` | ECS env (plain) |
| `FRONTEND_URL` | Used in email templates and CORS. | `https://meydanfzai.com` | ECS env (plain) |
| `ALLOWED_ORIGINS` | CORS whitelist (comma-separated). | `https://meydanfzai.com,https://www.meydanfzai.com` | ECS env (plain) |
| `JWT_ALGORITHM` | JWT signing alg. | `HS256` | ECS env (plain) |
| `JWT_EXPIRE_MINUTES` | Token lifetime. | `1440` (24 h) | ECS env (plain) |
| `JWT_SECRET` | HMAC key for signing. **Must match across all tasks/regions for session continuity.** | `(64 hex chars)` | Secrets Manager `meydan/prod/jwt-secret` |
| `DB_POOL_SIZE` | SQLAlchemy connection pool per worker process. | `15` | ECS env (plain) |
| `DB_MAX_OVERFLOW` | Burst capacity above pool size. | `25` | ECS env (plain) |
| `DATABASE_URL` | Async PG DSN. | `postgresql+asyncpg://meydan:…@meydan-prod-db.…rds.amazonaws.com:5432/meydan_db` | Secrets Manager `meydan/prod/database-url` |
| `REDIS_URL` | Redis connection. | `redis://meydan-prod-redis.…cache.amazonaws.com:6379/0` | Secrets Manager `meydan/prod/redis-url` |
| `DEV_MODE` | Enables generous debug endpoints + verbose logs. **Must be `false` in prod.** | `false` | ECS env (plain) |
| `LOG_LEVEL` | Python logger level. | `INFO` | ECS env (plain) |
| `TRUSTED_PROXY` | Trust `X-Forwarded-*` headers (set true behind ALB). | `true` | ECS env (plain) |
| `MODERATION_LLM_ENABLED` | Enable LLM-based pre-generation moderation. Flip to `false` in an OpenAI outage to fall back to keyword-only. | `true` | ECS env (plain) |
| `EMAIL_PROVIDER` | `resend` (default) or `ses`. | `resend` | ECS env (plain) |
| `EMAIL_SENDER` | From-address. | `noreply@meydanfzai.com` | ECS env (plain) |
| `RESEND_SENDER_EMAIL` | Verified Resend sender. | `noreply@meydanfzai.com` | ECS env (plain) |
| `RESEND_API_KEY` | Resend API key. | `re_…` | Secrets Manager `meydan/prod/resend-api-key` |
| `OPENPROVIDER_API_URL` | Domain registrar base URL. | `https://api.openprovider.eu/v1beta` | ECS env (plain) |
| `OPENPROVIDER_USERNAME` | OpenProvider login. | (email) | Secrets Manager `meydan/prod/openprovider-username` |
| `OPENPROVIDER_PASSWORD` | OpenProvider password. | `…` | Secrets Manager `meydan/prod/openprovider-password` |
| `OPENPROVIDER_RESELLER_ID` | OpenProvider reseller account ID. | `…` | Secrets Manager `meydan/prod/openprovider-reseller-id` |
| `ANTHROPIC_API_KEY` | Anthropic API key (Stage 2 + 3). | `sk-ant-…` | Secrets Manager `meydan/prod/anthropic-api-key` |
| `OPENAI_API_KEY` | OpenAI API key (Stage 0 + 1, moderation). | `sk-proj-…` | Secrets Manager `meydan/prod/openai-api-key` |
| `GEMINI_API_KEY` | Optional fallback model (currently unused). | `AIza…` | Secrets Manager `meydan/prod/gemini-api-key` |
| `PEXELS_API_KEY` | Pexels stock-photo API. | `…` | Secrets Manager `meydan/prod/pexels-api-key` |
| `UNSPLASH_ACCESS_KEY` | Unsplash stock-photo API. | `…` | Secrets Manager `meydan/prod/unsplash-access-key` |
| `WORKER_CONCURRENCY` | Concurrent generation jobs per worker task. | `5` | Worker ECS env (plain) |
| `PORT` | API listen port. | `8000` | API ECS env (plain) |
| `WORKERS` | Number of gunicorn workers per task. | `8` | API ECS env (plain) |
| `SENTRY_DSN` | Optional — error tracking. | `https://…@sentry.io/…` | Secrets Manager `meydan/prod/sentry-dsn` (optional) |
| `AWS_ACCOUNT_ID` | Used for ARN generation. | `290172088819` | ECS env (plain) |

## Critical: trim trailing whitespace before storing in Secrets Manager

When creating a Secrets Manager entry from a CLI redirect (e.g. `aws … --output text > file && aws secretsmanager create-secret --secret-string file://file`), the `--output text` step appends a `\n`. ECS injects whatever bytes Secrets Manager has — newlines and all — into the env var. The `httpx` library (inside the OpenAI / Anthropic Python SDKs) then rejects header values containing newlines as `LocalProtocolError: Illegal header value`.

**Always trim before storing**:
```bash
printf '%s' "$VALUE" > /tmp/sec.txt        # printf, not echo
aws secretsmanager put-secret-value --secret-id meydan/prod/openai-api-key \
  --secret-string "file:///tmp/sec.txt"
```

This bit us during the Singapore migration — after fixing all 12 secrets, generation calls started working.

## Rotation schedule

| Secret | Rotate every | Procedure |
|---|---|---|
| `JWT_SECRET` | 12 months OR after suspected leak | Rolling rotation requires keeping both old + new keys briefly so existing sessions don't all invalidate. Implementation pending — currently a hard rotation forces re-login. |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | 6 months | Generate new in provider console → update Secrets Manager → force-redeploy ECS → revoke old key in provider console. |
| `RESEND_API_KEY` | 6 months | Same flow on resend.com. |
| `OPENPROVIDER_PASSWORD` | 12 months | OpenProvider dashboard. |
| `DB master password` | 12 months OR upon staff change | Rotate via `aws rds modify-db-instance --master-user-password` → update `meydan/prod/database-url` Secret with new value → force-redeploy. |
| `AWS IAM access keys` | 6 months OR upon staff change | IAM console → create new key → update GitHub Actions secrets `AWS_ACCESS_KEY_ID_PROD` / `AWS_SECRET_ACCESS_KEY_PROD` → deactivate old. |

## Secret-leak audit

Run this to confirm no secret values are committed to the repository:

```bash
# Scan full git history for AWS-style keys, Anthropic / OpenAI style, JWT secrets
git log --all -p | grep -E "AKIA[A-Z0-9]{16}|sk-ant-api[0-9]{2}|sk-proj-|JWT_SECRET\s*=\s*['\"][a-f0-9]{32,}" | head
git log --all -p -S "ANTHROPIC_API_KEY=" | head
git log --all -p -S "OPENAI_API_KEY=" | head
```

Result at handover: **no production-key values appear in committed source**. The only key-shaped strings are placeholder values in `backend/.env.example` (`sk-ant-…`, `sk-proj-…`, `re_…`).

> A previous session (2026-04-23) noted dev IAM access keys had been pasted in chat. Those keys have been rotated as part of the Singapore migration; the value pasted in chat is no longer valid against any AWS account.
