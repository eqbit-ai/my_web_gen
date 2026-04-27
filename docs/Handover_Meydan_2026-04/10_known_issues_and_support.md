# 10. Known Issues and Support

Everything not finished, and everyone who still needs to be called when things break.

## Open bugs

| # | Title | Severity | Status | Steps to reproduce | Workaround |
|---|---|---|---|---|---|
| 1 | Carousels / sliders do not function in generated sites | Medium | **CLOSED** (2026-04-27) | Carousel section now ships a known-good helper script that wires prev / next + autoplay against the standardised section markup. Verified end-to-end in dev. | — |
| 2 | LinkedIn iframes 404 / X-Frame-Options reject | Low | **CLOSED** (2026-04-27) | Stage 2 prompt updated to never emit iframes pointing at social-media platforms; `s3_deploy.py` post-processes any leftover social iframes into branded link cards. | — |
| 3 | Duplicate CSS / JS in some generated sites | Low | **CLOSED** (2026-04-27) | Deploy pipeline now runs a dedup pass before upload; animation-library snippet is included once at the bottom. Deployed-site bundle size dropped ~5–8%. | — |
| 4 | LLM occasionally generates dark hero with dark text → invisible | Medium | **CLOSED** (2026-04-27) | Stage 2 prompt tightened with explicit contrast rules; post-generation colour-contrast checker rejects WCAG-AA-failing combinations and falls back to a safe palette. | — |
| 5 | Password-reset tokens exposed in HTTP response when `DEV_MODE=true` | High (config) | **CLOSED** (2026-04-24) | Call `POST /api/auth/forgot-password` with `DEV_MODE=true`. Token appears in body. | Default for `DEV_MODE` is `false`. Prod task def must keep it `false`. |
| 6 | IDOR across deploy and section endpoints | High (security) | **CLOSED** (2026-04-24) | Get a JWT for user A. `POST /api/deploy` with user B's `session_id`. | All `/api/sections/*` and the main `/api/deploy` now verify `session.user_id == auth.user_id`. |
| 7 | SQL injection surface via tenant schema name | High (security) | **CLOSED** | A trade licence with a `"` could break out of `SET search_path TO "{schema}"`. | `database._validate_schema_name` rejects anything not `[a-zA-Z0-9_]+`. |
| 8 | Content moderation fails open on LLM error | Medium (security) | **CLOSED** (2026-04-24) | Block egress to OpenAI; submit a prompt that would normally be rejected. | `check_prompt_safety_llm` now fails **closed**. Operators can flip `MODERATION_LLM_ENABLED=false` for keyword-only. |
| 9 | Exception details leaked to client in deploy + admin routes | Medium (security) | **CLOSED** (2026-04-24) | Trigger any backend exception. Response body contained the boto3 traceback. | `deploy.py` and 20+ admin endpoints now return generic messages; tracebacks logged via `logger.exception`. |
| 10 | Weak password policy | Medium (security) | **CLOSED** (2026-04-24) | Sign up with `abc123`. Accepted. | `validate_password_strength` enforces 12 chars + upper + lower + digit + symbol. Wired into signup, reset-password, change-password. |
| 11 | Path traversal in file delete | Medium (security) | **CLOSED** (2026-04-24) | `DELETE /api/uploads/../../etc/passwd`. | `storage.delete_file` resolves path against `UPLOAD_DIR` and rejects escapes. |

## Open configuration / CI issues

| # | Title | Severity | Fix |
|---|---|---|---|
| C1 | **`SONAR_TOKEN` missing from GitHub repo secrets** | Low | SonarCloud Analysis job in `ci.yml` is red on every push. Add the token at Settings → Secrets → Actions, or remove the SonarCloud step. |
| C2 | **`deploy-prod.yml` `wait services-stable` occasionally times out on a successful deploy** | Low | The `aws ecs wait` polls 40 × 15 s = 10 min. Slow rollouts exceed it. Treat as green if `/api/health` returns 200 within 5 min of push. Permanent fix: raise the wait or move to a follow-up step polling `/api/health`. |
| C3 | **Legacy `production` and `staging` branches** unwired | Cosmetic | Safe to delete: `git push origin --delete production staging`. |
| C4 | **me-central-1 leftover ElastiCache cluster stuck in `creating`** | Low | `meydan-prod-redis` in me-central-1 (UAE) has been in `creating` since 2026-04-23. AWS refuses delete in this state. Open AWS Support ticket — text prepared during migration session. |
| C5 | **me-central-1 leftover S3 bucket** `meydan-prod-deployed-sites` | Cosmetic | 192 objects, 48 MB, charges pennies. Delete after Singapore is confirmed serving live for 30 days. |

## Unfinished items — current state

| Item | State | Notes |
|---|---|---|
| **Prompt Manager — NOT WIRED, NOT TESTED** ⚠️ | UI renders. DB tables (`prompt_versions`) accept writes. Admin endpoints `GET/POST /api/admin/prompts/*` work and update the DB. **The Worker / generation pipeline does not read from the DB at all** — it uses hardcoded prompts in `backend/app/utils/prompt_pipeline.py`. Publishing a new version through the UI changes nothing about generation. End-to-end tests for the wiring do not exist. | Until wired, the only way to change a prompt is to edit `prompt_pipeline.py`, commit, and push to `main`. Wiring work: (1) make `prompt_pipeline.py` read active version from `prompt_versions` table with 60s in-process cache and fall-back to in-file defaults; (2) add a "preview with draft prompt" admin endpoint; (3) add unit test covering publish + rollback affecting generation output. ~1 day total. **This is the top unfinished item in the handover.** |
| **Token system rationalisation** | Both "generation limit" and "token budget" enforcement paths exist. | Client to confirm whether tokens stay or just per-month generation cap. If tokens go: drop `token_transactions` charging logic; keep `users.max_generations_per_month`. |
| **File-upload generation** (PDF / text / images) | Backend upload endpoints exist (`/api/uploads/*`) but the generator does not ingest uploads into the Stage 0 brief. | Needs PDF / DOCX text extraction + image-placeholder mapping. |
| **AI-Agent FAQ on landing page** | Design decided; not built. | Replacement for the static FAQ accordion. |
| **E-commerce module** | Architectural plan exists in `docs/ecommerce-feature-plan.{md,pdf}`. Not started. | ~9-week MVP. Parked pending client sign-off. |
| **Capacity plan: 500 – 1,000 concurrent generations** | Sizing analysis done. Not implemented. | Critical path is **LLM provider tier upgrades** — OpenAI Tier 4+ ($250 paid, 14d wait) and Anthropic Tier 4 + Higher Rate Limits form (1–2 weeks). Without those, AWS sizing is moot — 429s cap throughput at ~50 concurrent. |
| **Refresh tokens** | Not implemented. | Users are forced to re-login every `JWT_EXPIRE_MINUTES`. |

## Technical debt — recommended for revisiting

- **`backend/app/routes/generator.py`** is >4,000 lines and owns too many concerns (session, streaming, SSE, moderation, file ingest). Split into `generator_stream.py`, `generator_session.py`, `generator_uploads.py`.
- **`backend/app/routes/admin_old.py`** is the previous-gen admin router; current admin lives in `backend/app/routes/admin/`. `admin_old.py` is still mounted for back-compat. Plan a deprecation sweep.
- **Tenant schema DDL** is applied on signup by raw SQL. Move through Alembic templated migrations so a schema-repair tool can diff and apply.
- **Dev-side secrets injection** still uses plaintext env vars in the ECS task definition — Singapore prod is on Secrets Manager. Migrate dev to the same pattern.
- **`backend/debug_output/*`** (generated site artefacts) should be moved to S3 or dropped from the repo.
- **Tailwind post-processing** (`premium_postcss.py`) is bespoke. Tailwind v4 / v5 will need rework.
- **Stale Route 53 zones** exist in dev account from earlier setup. The prod account hosted zone is authoritative; clean up dev account zones to avoid confusion.

## Support contacts — post-handover support period

The valid contact window is the agreed support period in the master services agreement (typically 30 days from delivery). Beyond that, contact the Meydan AI lead.

| Name | Role | Email | Phone | Response window |
|---|---|---|---|---|
| Ashutosh | Technical lead (vendor) — backend, generation pipeline, deploy | ashuken266@gmail.com | *(in workbook)* | Same-business-day, weekdays 09:00–18:00 GST |
| *(Frontend engineer)* | Frontend, editor, admin UI | *(tbd)* | *(tbd)* | Same-business-day |
| *(DevOps / AWS contact)* | Infra, incidents, CloudWatch, AWS billing | *(tbd)* | *(tbd)* | 1 h pager for production outages (P1) |
| *(Meydan AI lead)* | Client-side owner — escalation, scope, next phase | *(tbd)* | *(tbd)* | 1 business day |

> The workbook's Contacts sheet is the authoritative list — if this document disagrees, the workbook wins.

## How to escalate during an outage

1. Check CloudWatch dashboard `meydan-production` (AWS console, `ap-southeast-1`) — red panels show what is broken.
2. Check provider status pages: `status.anthropic.com`, `status.openai.com`, `status.aws.amazon.com`, `status.resend.com`.
3. If an LLM circuit breaker is stuck open: `POST /api/admin/circuit/{openai|anthropic}/reset`.
4. If the site is entirely down: check ALB target health in the AWS console; if targets are unhealthy, `aws ecs update-service --force-new-deployment` for the affected service.
5. If DNS is the problem: the authoritative zone is **CloudFront**, not Route 53.
6. For data incidents, follow the DR playbook in `infrastructure/aws/OPERATIONS-GUIDE.md`.

A correlation ID from the failed request (returned as `X-Correlation-ID` on every response) is the fastest way to trace a user-reported issue through CloudWatch Logs.
