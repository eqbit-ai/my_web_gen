# 10. Known Issues and Support

Everything not finished, and everyone who still needs to be called when things break.

## Open bugs

| # | Title | Severity | Status | Steps to reproduce | Notes |
|---|---|---|---|---|---|
| 1 | Carousels/sliders do not function in generated sites | Medium | **OPEN** | Generate a site whose plan includes a carousel section. On the deployed site, click prev / next or wait for autoplay. Nothing happens. | Users can delete the carousel section and use a static multi-image grid. Root cause in `backend/app/utils/prompt_pipeline.py` stage 3 (JS) — selectors don't consistently match the HTML produced in stage 2. Candidate fix: replace the free-form JS with an injected standard carousel helper. Requires generation + visual verification, not fixed at handover. |
| 2 | Password-reset tokens exposed in HTTP response when `DEV_MODE=true` | High (config) | **FIXED (2026-04-24)** | Call `POST /api/auth/forgot-password` with `DEV_MODE=true`. Token appears in response body. | In-code default for `DEV_MODE` is `"false"`; prod/staging ECS task defs must continue to set `DEV_MODE=false`. `backend/app/routes/auth.py` gates the extra fields behind the env var. |
| 3 | IDOR across deploy and section endpoints | High (security) | **FIXED (2026-04-24)** | Get a JWT for user A. Call `POST /api/deploy` with user B's `session_id`. | All `/api/sections/*` endpoints already called `_verify_session_ownership()`. The main `POST /api/deploy` now performs the same check; other deploy endpoints filter by `Site.user_id`. |
| 4 | SQL-injection surface via tenant schema name | High (security) | **FIXED** | A trade licence containing a double-quote bypasses sanitisation and can break out of `SET search_path TO "{schema_name}"`. | `backend/app/database.py::_validate_schema_name` rejects any schema name that is not `[a-zA-Z0-9_]+`. All three call sites (`create_tenant_schema`, `init_tenant_tables`, `get_tenant_db`) validate before interpolation. |
| 5 | Content moderation fails open on LLM error | Medium | **FIXED (2026-04-24)** | Provoke a timeout on `moderation_llm` (e.g. block egress to OpenAI). Submit a prompt that would normally be rejected. | `check_prompt_safety_llm` now fails **closed** — LLM errors return `safe=False` with a user-facing "try again shortly" message. Operators can keyword-only-mode with `MODERATION_LLM_ENABLED=false`. |
| 6 | Exception details leaked to client in deploy + admin routes | Medium | **FIXED (2026-04-24)** | Trigger a CloudFront error during deploy. The response body contained the boto3 traceback. | All exception-to-client leaks in `deploy.py` + 20+ admin endpoints (users, domains, generations, operations, tokens, sites, admin_old) now return generic messages; full tracebacks are logged via `logger.exception`. |
| 7 | Weak password policy | Medium | **FIXED (2026-04-24)** | Sign up with `abc123`. Accepted. | New shared validator `validate_password_strength` in `app/utils/input_sanitizer.py`: 12 chars + lowercase + uppercase + digit + symbol. Wired into signup, reset-password, change-password. |
| 8 | Path traversal in file delete | Medium | **FIXED (2026-04-24)** | `DELETE /api/uploads/../../etc/passwd`. | `storage.delete_file` resolves the target against `UPLOAD_DIR` and rejects any path that escapes the upload root. Upload URLs are also DB-scoped to the caller at the route layer. |

A fuller triage list (18 items, CRITICAL → LOW) is in the team's security memo. Items 2, 3, 4, 5, 6, 7, 8 are now closed. Item 1 (carousels) remains open and is the only outstanding end-user-visible bug.

## Unfinished items — current state

| Item | State | Notes |
|---|---|---|
| **Prompt Manager live integration** | UI + DB + admin endpoints complete; generation pipeline still reads `prompt_pipeline.py` hardcoded prompts. | Wiring: make `backend/app/utils/prompt_pipeline.py` load the published version from the `prompt_versions` table, fall back to the in-file defaults. ~1 day. |
| **Token-system removal** | Both "generation limit" and "token budget" enforcement paths exist. Client has not confirmed whether tokens should remain. | If removed, keep the per-month generation cap (`users.max_generations_per_month`) as the primary control; drop the `token_transactions` charge logic. |
| **File-upload generation** (PDF / text / images) | Backend upload endpoints exist (`/api/uploads/*`) but the generator does not ingest uploaded files into the stage-0 brief. | Needs PDF/DOCX text extraction + image-placeholder mapping. Full spec in the team backlog. |
| **AI Agent FAQ (landing page)** | Design decided; not built. | Replacement for the static FAQ accordion on `meydanfzai.com`. |
| **E-commerce module** | Architectural plan exists (`docs/ecommerce-feature-plan.md`). Not started. | ~9-week MVP; separate shop microservice. Parked pending client sign-off. |
| **UAE production migration** | Phase 0 complete (code hygiene, CI/CD split dev→us-east-1 + main→me-central-1, email abstraction). Phases 1+ pending. | Details in the team backlog. |
| **Capacity plan: 500–1000 concurrent generations** | Sizing analysis done. Not implemented. | Critical path: LLM provider tier upgrades (Anthropic + OpenAI). RDS r6g.xlarge + RDS Proxy + worker autoscaling needed. Expected run-rate $7K–$15K / month at 1000 concurrent. |

## Technical debt — recommended for revisiting

- **`backend/app/routes/generator.py`** is >4 000 lines and owns too many concerns (session, streaming, SSE, moderation, file ingest). Split into `generator_stream.py`, `generator_session.py`, `generator_uploads.py`.
- **`backend/app/routes/admin_old.py`** is the previous-generation admin router; `backend/app/routes/admin/` is the current one. `admin_old.py` is still mounted for a handful of backward-compatible routes. Plan a deprecation sweep.
- **Tenant schema DDL** is applied on signup by raw SQL. It should go through Alembic templated migrations so a schema repair tool can diff and apply.
- **No refresh tokens** — users are forced to log in again at `JWT_EXPIRE_MINUTES` expiry. Consider sliding-window refresh for better UX.
- **Legacy `backend/app/templates_data/` HTML files** are no longer read by the pipeline and are listed as deleted in `git status`; the deletion was never committed. Clean up.
- **`backend/debug_output/*`** (generated site artefacts) should be moved to an S3 bucket or dropped entirely from the repo.
- **Tailwind post-processing** (`premium_postcss.py`) is bespoke. If the generator adopts Tailwind v4 / v5, this needs rework.
- **Route 53 records** in AWS are not authoritative (Cloudflare is). Clean up the stale zone to avoid confusion during incident response.

## Support contacts — post-handover support period

The valid contact window is the agreed support period in the master services agreement (typically 30 days from delivery). Beyond that, contact the Meydan AI lead.

| Name | Role | Email | Phone | Response window |
|---|---|---|---|---|
| Ashutosh | Technical lead (vendor) — backend, generation pipeline, deploy | ashuken266@gmail.com | *(to be filled in the delivered workbook)* | Same-business-day, weekdays 09:00–18:00 GST |
| *(Frontend engineer)* | Frontend, editor, admin UI | *(tbd)* | *(tbd)* | Same-business-day |
| *(DevOps / AWS contact)* | Infra, incidents, CloudWatch, AWS billing | *(tbd)* | *(tbd)* | 1 h pager for production outages (P1) |
| *(Meydan AI lead)* | Client-side owner — escalation, scope, next phase | *(tbd)* | *(tbd)* | 1 business day |

> The handover workbook's contacts sheet is the authoritative list — if this document disagrees, the workbook wins.

## How to escalate during an outage

1. Check CloudWatch dashboard `meydan-production` — red panels show what's broken.
2. Check the provider status pages: https://status.anthropic.com, https://status.openai.com, https://status.aws.amazon.com, https://www.cloudflarestatus.com, https://status.resend.com.
3. If the LLM circuit breaker is stuck open, reset with `POST /api/admin/circuit/{openai|anthropic}/reset`.
4. If the site is entirely down: check ALB target health in the AWS console; if targets are unhealthy, trigger `aws ecs update-service --force-new-deployment` for the affected service.
5. If DNS is the problem: the authoritative zone is **Cloudflare**, not Route 53.
6. For data incidents, follow the DR playbook in `infrastructure/aws/OPERATIONS-GUIDE.md`.

A correlation ID from the failed request (returned as `X-Correlation-ID` on every response) is the fastest way to trace a user-reported issue through CloudWatch Logs.
