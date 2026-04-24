# 5. Code Structure

## Repo root — 2 levels deep

```
meydan-ai/
├── backend/                 FastAPI service + worker. Runs in Python 3.12.
│   ├── alembic/             DB migrations (one file per schema change).
│   ├── app/                 Application code — see below.
│   ├── scripts/             One-off ops scripts (seeders, audits).
│   ├── tests/               Pytest suite.
│   ├── Dockerfile           Multi-stage build, non-root user.
│   ├── entrypoint.sh        Runs `alembic upgrade head`, then exec's CMD.
│   ├── gunicorn.conf.py     Prod server config (Uvicorn workers).
│   └── requirements.txt     Pinned dependencies.
│
├── frontend/                React 18 SPA (Create React App).
│   ├── public/              Static shell (index.html, icons).
│   ├── src/                 Application code — see below.
│   ├── Dockerfile           Build + nginx static serve.
│   └── package.json         JS dependencies.
│
├── .github/workflows/       **Real** CI/CD lives here.
│   ├── ci.yml               Lint + test + security scan + frontend build + SonarCloud.
│   ├── deploy-dev.yml       Triggered on push to `dev` → us-east-1 (account 371170753756).
│   └── deploy-prod.yml      Triggered on push to `main` → me-central-1 (account 290172088819).
│
├── infrastructure/aws/      Hand-written AWS infra-as-config (first-time provisioning).
│   ├── cloudformation.yml   Parameterised stack for a new environment.
│   ├── ecs-task-api.json    ECS task definition for the API service.
│   ├── ecs-task-worker.json ECS task definition for the worker service.
│   ├── ecs-service-*.json   ECS service definitions.
│   ├── alb.json             ALB + listener + target groups.
│   ├── alarms.yml           CloudWatch alarms.
│   ├── dashboard.json       CloudWatch dashboard JSON.
│   ├── waf.yml              AWS WAF managed-rule groupings.
│   ├── s3-lifecycle.json    S3 lifecycle rules for log / artefact buckets.
│   ├── deploy.sh            Orchestration script used by CI.
│   ├── deploy-observability.sh  Applies dashboards + alarms.
│   ├── github-deploy.yml    Reference GitHub Actions workflow (superseded by `.github/workflows/`).
│   └── OPERATIONS-GUIDE.md  Ops-team runbook (on-call, recovery).
│
├── docs/                    Documentation (this handover package lives here).
├── docker-compose.yml       Local multi-container dev stack.
├── nginx.conf               Reverse proxy config for the frontend image.
└── sonar-project.properties Static analysis config (SonarCloud).
```

## `backend/app/` — 3 levels deep

```
backend/app/
├── main.py                  FastAPI entrypoint: middlewares, routers, lifespan.
├── database.py              SQLAlchemy async engine + session factory.
├── worker.py                Long-running job consumer (generation pipeline).
│
├── middleware/              Cross-cutting request concerns.
│   ├── correlation.py       Assigns + propagates X-Correlation-ID.
│   ├── rate_limiter.py      Redis sliding-window rate limit.
│   ├── security.py          HSTS, CSP, X-Frame-Options, etc.
│   └── request_tracker.py   In-flight request counting for graceful shutdown.
│
├── models/                  SQLAlchemy ORM models (one per table).
│   ├── user.py, site.py, project.py, audit.py, edit_log.py,
│   ├── domain.py, generation_log.py, token_transaction.py, token_request.py,
│   ├── form_submission.py, login_event.py, password_reset.py, media.py,
│   ├── announcement.py, prompt_version.py, page_view.py
│
├── routes/                  HTTP endpoints — one file per bounded context.
│   ├── auth.py              Signup / login / email verify / password reset.
│   ├── generator.py         Streaming generation + session sync.
│   ├── sections.py          Per-section edit endpoints (text, style, nav, footer).
│   ├── projects.py          List / rename / delete user projects.
│   ├── deploy.py            Deploy / redeploy / domain-connect for a site.
│   ├── domains.py           Domain search + purchase (OpenProvider).
│   ├── dns.py               Cloudflare DNS CRUD per site.
│   ├── forms.py             Public form submit + admin inbox.
│   ├── uploads.py           File uploads + remote-URL ingest.
│   ├── images.py            Pexels / Unsplash search proxy.
│   ├── templates.py         10 premium starter templates.
│   ├── components.py        Section / component library (preview / swap).
│   ├── site_features.py     Export ZIP, custom code, page-view tracking.
│   ├── jobs.py              Generic async job status.
│   ├── landing_chat.py      Public landing-page chatbot.
│   ├── edit_feedback.py     Thumbs up / down on generated edits.
│   ├── health.py, metrics_route.py
│   └── admin/               Admin-only endpoints (grouped).
│       ├── users.py, tokens.py, sites.py, domains.py,
│       ├── generations.py, analytics.py, edit_logs.py,
│       ├── operations.py, stats.py, deps.py (require_admin)
│
├── utils/                   Reusable modules — most of the business logic lives here.
│   ├── prompt_pipeline.py   THE prompt templates for all 4 LLM stages.
│   ├── llm_clients.py       OpenAI + Anthropic client wrappers + model IDs.
│   ├── circuit_breaker.py   Per-provider breaker (5 failures → open 60 s).
│   ├── auth.py              JWT encode/decode, password hashing.
│   ├── edit_logger.py, edit_categorizer.py   Edit-log helpers.
│   ├── usage_limits.py      Per-user generation / site caps.
│   ├── token_tracker.py     Charges a user for a completed LLM call.
│   ├── s3_deploy.py         The deploy pipeline: HTML hardening → S3 → CloudFront.
│   ├── cloudfront_acm.py    CloudFront distribution + ACM cert lifecycle.
│   ├── cloudflare.py        Cloudflare DNS API client.
│   ├── route53.py           Legacy/alternate DNS client (not authoritative).
│   ├── openprovider.py      Domain registrar client.
│   ├── email.py             Provider-agnostic email (Resend or SES).
│   ├── image_resolver.py, image_packs.py, image_optimizer.py   Imagery.
│   ├── redis_client.py, session_store.py   Redis + session helpers.
│   ├── content_moderation.py Pre-generation prompt moderation.
│   ├── input_sanitizer.py   Request sanitisation.
│   ├── plan_validator.py    Stage-1 JSON schema check.
│   ├── quality_scorer.py, lighthouse_check.py, responsive_check.py, seo_checker.py
│   ├── multi_page.py        Multi-page site assembly.
│   ├── form_handler.py      Injects form POST URL into deployed sites.
│   ├── design_tokens.py, design_system.py, font_pairings.py
│   ├── components.py, section_templates.py, section_parser.py, templates.py
│   ├── contact_widgets.py, animations.py, interactive_templates.py
│   ├── premium_postcss.py   Tailwind-like post-processing of generated CSS.
│   ├── safe_regex.py        ReDoS-resistant regex wrappers (used by deploy pipeline).
│   ├── metrics.py, cloudwatch_metrics.py, logging_config.py, sentry_setup.py
│   ├── audit_log.py         Writes rows to the audit_logs table.
│   └── patterns/            Layout patterns referenced by the Stage-1 planner.
│
└── templates_data/          (Legacy — previous template HTML files; now unused.)
```

## `frontend/src/` — 2 levels deep

```
frontend/src/
├── App.js                   Route config, auth context bootstrap.
├── App.css                  Dark-theme styles for the generator surface.
├── light-ui.css,            Light-theme styles for the dashboard / auth / landing.
│   light-ui-generator.css
├── meydan-theme.css         Brand tokens (colors, fonts).
├── index.js, index.css      CRA entry.
├── config.js                API base URL + feature flags.
│
├── context/                 React context providers (auth, toast, etc.).
├── services/
│   ├── api.js               User-facing API client (axios wrapper + JWT).
│   └── adminApi.js          Admin-panel API client.
│
└── components/
    ├── LandingPage.jsx      Marketing home page.
    ├── Signup.jsx, Login.jsx, VerifyEmail.jsx
    ├── ForgotPassword.jsx, ResetPassword.jsx, ForceResetPassword.jsx
    ├── PendingApproval.jsx  Post-login gate for unapproved users.
    ├── Dashboard.jsx        Post-login home (sites, usage, inbox).
    ├── WebsiteGenerator.jsx Main generator workspace (preview + chat editor).
    ├── Preview.jsx          iframe with the generated HTML.
    ├── CodeEditor.jsx       Monaco-based code view.
    ├── SectionEditor.jsx, NavEditor.jsx, FooterEditor.jsx, SeoEditor.jsx,
    │   ContentForm.jsx, DesignSystemPanel.jsx
    ├── ComponentLibrary.jsx, GalleryPicker.jsx, SwapPreviewModal.jsx
    ├── LogoUploader.jsx, ImageLibrary.jsx
    ├── DeployModal.jsx      Deploy / domain flow.
    ├── Navbar.jsx, LightUI.jsx
    ├── AdminDashboard.jsx   Admin-panel root.
    └── admin/               Admin sub-pages (pending approvals, edit logs, etc.).
```

## Where to look for specific concerns

| I want to change… | Go to |
|---|---|
| How the site is generated | `backend/app/utils/prompt_pipeline.py` + `backend/app/worker.py` |
| Which models are used | `backend/app/utils/llm_clients.py` (`CLAUDE_MODEL`, `OPENAI_PLAN_MODEL`) |
| How sites get deployed to S3 | `backend/app/utils/s3_deploy.py` + `backend/app/routes/deploy.py` |
| Domain purchase flow | `backend/app/routes/domains.py` + `backend/app/utils/openprovider.py` |
| DNS (Cloudflare) | `backend/app/utils/cloudflare.py` + `backend/app/routes/dns.py` |
| Rate limits / throttling | `backend/app/middleware/rate_limiter.py` |
| JWT + login | `backend/app/routes/auth.py` + `backend/app/utils/auth.py` |
| Admin panel endpoints | `backend/app/routes/admin/` |
| Add a DB column | New Alembic revision in `backend/alembic/versions/` |
| Change an env var's shape | `backend/.env.example` then every reader via `os.getenv(...)` |
| CI/CD (what actually runs) | `.github/workflows/ci.yml`, `deploy-dev.yml`, `deploy-prod.yml` |
| CI/CD (scripts used by the workflows) | `infrastructure/aws/deploy.sh`, `deploy-observability.sh` |

## Configuration locations
- **Local dev**: `backend/.env` (copy `backend/.env.example`), `frontend/.env` (API base URL).
- **Production (AWS)**: env vars on the ECS task definitions in `infrastructure/aws/ecs-task-*.json`, with secrets resolved from AWS Secrets Manager.
- **Feature flags**: there is no dedicated flag system — toggles are env vars (e.g. `MODERATION_LLM_ENABLED`, `DEV_MODE`, `EMAIL_PROVIDER`).
