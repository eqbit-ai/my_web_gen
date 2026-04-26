# 4. Admin Workflow

Admins operate the product from the **Admin panel**, a protected React route at `/admin` backed by `/api/admin/*` endpoints. Screenshots live in `assets/screenshots/admin/`.

The admin surface is open to any user with `is_admin=true` on the `users` table. Flag is set manually via SQL at bootstrap (see `07_deployment_runbook.md`, post-deploy step 6).

## Step 1 — Log in as admin
- **Admin**: Visits `https://meydanfzai.com/login`, signs in with the admin account.
- **System**: Returns a JWT. Because `is_admin=true`, the UI exposes the **Admin** link in the top-right menu.
- Screenshot: `01_admin_login.png`

## Step 2 — Dashboard / stats overview
- **Admin**: Clicks **Admin** → lands on the stats page.
- **System**: Calls `GET /api/admin/stats` — totals (users, sites, generations today, failed generations, tokens consumed, token pool remaining).
- Screenshot: `02_admin_stats.png`

## Step 3 — Find a user
- **Admin**: Navigates to **Users**. Searches by email, company, or licence.
- **System**: `GET /api/admin/users?search=…`. Results show approval status, plan, tokens granted / consumed, last login.
- Screenshot: `03_admin_users.png`

## Step 4 — Approve, disable, or adjust a user
From the user detail page an admin can:
- **Approve** a pending user — grants 1M tokens and activates sign-in. `POST /api/admin/users/{user_id}/approve`.
- **Disable** / re-enable — `POST /api/admin/users/{user_id}/disable` / `…/enable`.
- **Grant additional tokens** — `POST /api/admin/users/{user_id}/grant-tokens` with `{amount, reason}`.
- **Adjust usage caps** (max sites, max generations / month) — `POST /api/admin/users/{user_id}/set_limits`.
- **Reset password** (forces password change on next login) — `POST /api/admin/users/{user_id}/reset-password`.

All mutations write to the `audit_logs` table with the acting admin's `user_id`, target `user_id`, action, and a JSON diff.
Screenshots: `04a_user_detail.png`, `04b_grant_tokens.png`.

## Step 5 — Read current usage and cost
Two places to look:

- **Admin panel → Analytics**:
  - Growth: `GET /api/admin/analytics/growth`
  - Generation success rate: `GET /api/admin/analytics/generation-success`
  - Token consumption: `GET /api/admin/analytics/token-consumption`

- **CloudWatch Dashboard** (AWS console — `us-east-1` for dev, `ap-southeast-1` for prod): panels for request rate, p95 latency, 5xx rate, LLM spend by provider, and ALB target health. The JSON for the dashboard lives at `infrastructure/aws/dashboard.json` — apply with `aws cloudwatch put-dashboard`.

For AWS spend specifically, the authoritative source is **AWS Cost Explorer** filtered by tag `Project=meydan-ai`. The admin panel surfaces *LLM* cost only (computed from token counters in `token_transactions`).

Screenshot: `05_analytics.png`

## Step 6 — Change a prompt or swap an AI model
Prompts live in two places:
1. **Version-controlled** — `backend/app/utils/prompt_pipeline.py` (enhance / plan / html / js). Edit, PR, deploy.
2. **Admin runtime store** — `prompt_versions` table, accessed via the Admin panel:
   - `GET /api/admin/prompts` — list prompt keys and versions.
   - `POST /api/admin/prompts/{key}` — create a new version.
   - `POST /api/admin/prompts/{key}/{version}/publish` — make it live.
   **Note**: the runtime store exists and is wired to the admin UI; at the time of handover the generation pipeline still reads `prompt_pipeline.py` directly. Wiring the live DB prompts into the pipeline is flagged in `10_known_issues_and_support.md` as "Prompt Manager live integration".

Swapping a model is a one-line config change in `backend/app/utils/llm_clients.py` (constants `CLAUDE_MODEL` and `OPENAI_PLAN_MODEL`). Deploy as a normal release. To **roll back**, revert the commit and redeploy — the model IDs are plain strings.

Screenshot: `06_prompts.png`

## Step 7 — Read application logs and the audit trail
- **Application logs**: CloudWatch Logs group `/ecs/meydan-api` (and `/ecs/meydan-worker`). Every log line includes `correlation_id`. Common saved queries are in `infrastructure/aws/log-queries.md`.
- **Audit trail**: Admin actions are in the `audit_logs` table. Browse from the admin panel: **Operations → Audit logs** (`GET /api/admin/audit-logs`). Fields: `actor_user_id`, `action`, `target_type`, `target_id`, `metadata`, `created_at`, `ip_address`.
- **Edit analytics**: The `edit_logs` table records every in-editor edit (category, token cost, latency). Browse at **Operations → Edit logs** (`GET /api/admin/edit-logs`).
- **Failed generations**: `GET /api/admin/generations/failed` and `…/redis-failed` — retry from the UI with one click.

Screenshot: `07_audit.png`

## Other admin-only surfaces (pointers)
- **Announcements** — banner broadcast to all users (`GET/POST/PATCH/DELETE /api/admin/announcements`).
- **Templates** — toggle the 10 premium templates on/off (`GET/PATCH /api/admin/templates`).
- **Token pool** — global cap for token grants (`GET /api/admin/tokens/pool`).
- **Circuit breaker reset** — `POST /api/admin/circuit/{openai|anthropic}/reset` if a breaker is stuck open.
- **Moderation queue** — review flagged content (`GET /api/admin/moderation`, `POST /api/admin/moderation/{approve|reject}`).

All routes are mounted under `/api/admin` and gated by the `require_admin` dependency in `backend/app/routes/admin/deps.py`.
