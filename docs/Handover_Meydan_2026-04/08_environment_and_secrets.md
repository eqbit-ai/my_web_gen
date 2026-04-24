# 8. Environment and Secrets

Every environment variable the product reads, what it controls, an example value, and where it comes from.

## Environment variable table

| Name | Purpose | Example | Source |
|---|---|---|---|
| `DATABASE_URL` | Async Postgres connection string used by SQLAlchemy. | `postgresql+asyncpg://meydan:••••@rds-prod.xxx.rds.amazonaws.com:5432/meydan_db` | Secrets Manager → ECS env. |
| `DB_POOL_SIZE` | SQLAlchemy pool size per process. | `10` | ECS env (optional, default 10). |
| `DB_MAX_OVERFLOW` | SQLAlchemy extra connections beyond pool size. | `20` | ECS env (optional). |
| `REDIS_URL` | Redis connection string (rate limits, job queue, session cache). | `rediss://:••••@meydan-cache.xxx.amazonaws.com:6379/0` | Secrets Manager → ECS env. |
| `JWT_SECRET` | HMAC secret for JWT signing. 64-char hex. | `a3f1…` | Secrets Manager; **rotate every 180 days**. |
| `JWT_ALGORITHM` | JWT alg. | `HS256` | Code default, set only to override. |
| `JWT_EXPIRE_MINUTES` | Access-token lifetime. | `1440` | ECS env (optional). |
| `ANTHROPIC_API_KEY` | Claude Sonnet 4 HTML/JS generation. | `sk-ant-…` | Secrets Manager; **rotate on leak only** — affects billing attribution. |
| `OPENAI_API_KEY` | GPT-4.1 planning + landing chat. | `sk-proj-…` | Secrets Manager; same rotation rule. |
| `PEXELS_API_KEY` | Stock imagery. | `…` | Secrets Manager. |
| `UNSPLASH_ACCESS_KEY` | Stock imagery. | `…` | Secrets Manager. |
| `OPENPROVIDER_USERNAME` | Registrar login. | `meydan-ai` | Secrets Manager. |
| `OPENPROVIDER_PASSWORD` | Registrar password. | `••••` | Secrets Manager; **rotate every 90 days**. |
| `OPENPROVIDER_API_URL` | Override the default API URL (use sandbox in dev). | `https://api.openprovider.eu/v1beta` | ECS env. |
| `OPENPROVIDER_CONTACT_*` | Registrant contact block (first/last name, company, email, phone, street, zip, number). | see `.env.example` | Secrets Manager. |
| `CLOUDFLARE_API_TOKEN` | DNS CRUD on `meydanfzai.com` zone. Scoped to Zone:DNS:Edit. | `••••` | Secrets Manager; rotate every 180 days. |
| `CLOUDFLARE_ACCOUNT_ID` | Account scope. | `abc123…` | Secrets Manager. |
| `AWS_ACCESS_KEY_ID` | S3 + CloudFront + ACM API access. | `AKIA…` | IAM user via Secrets Manager; prefer **IAM role** on ECS task instead. |
| `AWS_SECRET_ACCESS_KEY` | Paired with above. | `••••` | Same as above. |
| `AWS_REGION` | Default region. | `me-central-1` | ECS env. |
| `AWS_ACCOUNT_ID` | Used by `s3_deploy.py` to generate ARNs. | `290172088819` | ECS env. |
| `EMAIL_PROVIDER` | `resend` (default) or `ses`. | `resend` | ECS env. |
| `EMAIL_SENDER` | From address. | `noreply@meydanfzai.com` | ECS env. |
| `RESEND_API_KEY` | Transactional email API key. | `re_…` | Secrets Manager; rotate every 180 days. |
| `RESEND_SENDER_EMAIL` | Verified Resend sender. | `noreply@meydanfzai.com` | ECS env. |
| `ADMIN_EMAIL` | Receives token-request + moderation alerts. | `ops@meydanfzai.com` | ECS env. |
| `FRONTEND_URL` | Used in email templates + CORS. | `https://meydanfzai.com` | ECS env. |
| `ALB_URL` | Internal base URL (worker → API callbacks). | `http://meydan-alb-internal.me-central-1.elb.amazonaws.com` | ECS env. |
| `API_BASE_URL` | Used by worker and scripts to call the API. | `https://meydanfzai.com/api` | ECS env. |
| `ALLOWED_ORIGINS` | Comma-separated CORS whitelist. | `https://meydanfzai.com,https://www.meydanfzai.com` | ECS env. |
| `TRUSTED_PROXY` | When `true`, trust `X-Forwarded-*`. | `true` in prod | ECS env. |
| `ENVIRONMENT` | `production`, `staging`, `dev`. Gates Swagger UI and some defaults. | `production` | ECS env. |
| `DEV_MODE` | Enables generous debug endpoints + verbose logs. **Must be `false` in prod.** | `false` | ECS env. |
| `LOG_LEVEL` | Python log level. | `INFO` | ECS env. |
| `WORKER_CONCURRENCY` | Number of generation jobs a worker processes in parallel. | `4` | Worker ECS env. |
| `MODERATION_LLM_ENABLED` | Enable LLM-based pre-generation moderation. | `true` | ECS env. |
| `METRICS_API_KEY` | Gate for `/api/metrics`. | `••••` | Secrets Manager. |
| `SENTRY_DSN` | Optional error reporting. Empty → Sentry disabled. | `https://…@sentry.io/…` | Secrets Manager. |
| `SKIP_MIGRATIONS` | Set on the worker container to skip `alembic upgrade` on boot (API runs it). | `1` | Worker ECS task def. |

See `backend/.env.example` for the canonical local-dev starter.

## Rotation schedule

| Secret | Cadence | Procedure |
|---|---|---|
| `JWT_SECRET` | 180 days | (1) Add a new secret value in Secrets Manager. (2) Support both old and new keys for one deploy cycle using `JWT_SECRET` primary + `JWT_SECRET_PREVIOUS` fallback (code change needed if not present). (3) Roll primary, keep previous for 24 h, then remove. |
| `DATABASE_URL` password | 90 days | (1) Create a new role or set a new password via `ALTER USER meydan WITH PASSWORD …`. (2) Update Secrets Manager. (3) Force new ECS deploy (`--force-new-deployment`). |
| `RESEND_API_KEY` | 180 days | Generate new key in Resend dashboard → update Secrets Manager → force-deploy. Delete the old key after confirming the new one works. |
| `CLOUDFLARE_API_TOKEN` | 180 days | Same pattern. Scope strictly to Zone:DNS:Edit on `meydanfzai.com`. |
| `OPENPROVIDER_PASSWORD` | 90 days | Change in OpenProvider portal → update Secrets Manager → force-deploy. |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | On leak or quarterly | Rotate in provider dashboard → update Secrets Manager → force-deploy. Cost attribution resets; note the rotation in the cost sheet. |
| AWS keys | **Do not rotate — use IAM roles instead.** | Replace static keys on ECS tasks with an IAM task role referencing the least-privilege policy in `infrastructure/aws/cloudformation.yml`. |
| `METRICS_API_KEY` | 180 days | Update Secrets Manager; update Grafana / Prometheus scraper config. |

## Secrets-in-repo scan

Confirmation that no secret is committed to the repository:

```bash
# Run from the repo root. Should print no findings.
git log --all --full-history -p -- backend/.env | grep -E '(sk-ant-|sk-proj-|AKIA|re_|eyJ[A-Za-z0-9_-]{20,})' || echo "clean"
```

Additional scans to run before hand-off:
```bash
pip install detect-secrets
detect-secrets scan --all-files > .secrets.baseline.scan

# or using trufflehog:
docker run --rm -v "$PWD:/repo" trufflesecurity/trufflehog:latest git file:///repo --only-verified
```

At time of handover, both scans pass with zero verified findings. `backend/.env` is `.gitignore`'d; only `backend/.env.example` (placeholder values) is tracked.

> **Hard rule**: `backend/.env` must never be `git add`ed. The `.gitignore` enforces this, but verify with `git check-ignore -v backend/.env` before any push.
