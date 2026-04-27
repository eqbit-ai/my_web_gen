# 5. Code Structure

A map of the repository. Open this file before opening the code.

```
meydan-website-generator/
├── backend/                    Python · FastAPI · the brains.
│   ├── app/
│   │   ├── main.py             FastAPI app factory; middleware + router wiring.
│   │   ├── database.py         Async SQLAlchemy engine + tenant-schema dispatch.
│   │   ├── models/             SQLAlchemy ORM models (User, Site, EditLog, ...).
│   │   ├── schemas/            Pydantic request / response models.
│   │   ├── routes/             HTTP endpoints — one file per concern.
│   │   │   ├── auth.py             /api/auth/*  (signup, login, verify, reset)
│   │   │   ├── generator.py        /api/generator/*  (SSE generation pipeline)
│   │   │   ├── projects.py         /api/projects/*  (CRUD on saved sites)
│   │   │   ├── deploy.py           /api/deploy/*    (S3 + CloudFront + ACM)
│   │   │   ├── domains.py          /api/domains/*   (custom-domain purchase)
│   │   │   ├── admin/              /api/admin/*     (operator surface; sub-routers)
│   │   │   └── landing_chat.py     /api/landing/chat  (public FAQ chatbot)
│   │   ├── utils/              Cross-cutting helpers.
│   │   │   ├── llm_clients.py      AsyncAnthropic + AsyncOpenAI singletons; circuit breaker decorator.
│   │   │   ├── prompt_pipeline.py  Stage 0-3 prompts; the four-stage generation orchestration.
│   │   │   ├── content_moderation.py   Keyword + LLM moderation (fail-closed).
│   │   │   ├── input_sanitizer.py  XSS / SQLi / password-strength / email validation.
│   │   │   ├── s3_deploy.py        Customer-site upload + URL generation.
│   │   │   ├── cloudfront_acm.py   Custom domain SSL flow.
│   │   │   ├── email.py            Resend / SES provider abstraction.
│   │   │   └── storage.py          User uploads bucket access.
│   │   ├── middleware/         FastAPI middleware (correlation IDs, rate-limiting, security headers, request tracker).
│   │   ├── worker.py           Async worker process; consumes Redis queue, runs pipeline.
│   │   └── alembic/            Database migrations (one file per change).
│   ├── tests/                  pytest suites (unit + integration).
│   ├── Dockerfile              Multi-stage; final image runs gunicorn + UvicornWorker.
│   ├── entrypoint.sh           alembic upgrade head, then gunicorn.
│   └── .env.example            Every env var the backend reads.
│
├── frontend/                   React 18 · CRA · the user-facing UI.
│   ├── public/                 favicon, manifest, OG image, video poster.
│   ├── src/
│   │   ├── App.js              Route table; auth-guarded shell.
│   │   ├── App.css             Global dark-theme generator styles.
│   │   ├── meydan-theme.css    Light theme for landing / auth.
│   │   ├── config.js           apiUrl resolution (same-origin in prod, localhost in dev).
│   │   ├── components/
│   │   │   ├── Landing.jsx         Marketing page.
│   │   │   ├── Login.jsx + Signup.jsx
│   │   │   ├── Dashboard.jsx       Post-login site list.
│   │   │   ├── WebsiteGenerator.jsx  Editor workspace (chat + preview + Monaco).
│   │   │   ├── admin/              Admin SPA (one component per page; see /admin routes).
│   │   │   └── shared/             Modals, toasts, error banner, etc.
│   │   ├── services/
│   │   │   ├── api.js              Authenticated fetch wrapper; JWT in localStorage.
│   │   │   └── adminApi.js         Admin endpoint helpers.
│   │   └── hooks/              Reusable React hooks.
│   ├── nginx.conf              Production nginx config — serves /build with SPA fallback.
│   └── Dockerfile              Multi-stage (node build → nginx runtime).
│
├── infrastructure/             AWS infra-as-config (first-time provisioning).
│   ├── aws/
│   │   ├── cloudformation.yml      Parameterised stack template.
│   │   ├── ecs-task-api.json       Dev API task def (live source of truth lives in ECS).
│   │   ├── ecs-task-worker.json    Dev Worker task def.
│   │   ├── ecs-task-api-prod.json  Prod API task def template (Singapore).
│   │   ├── ecs-task-worker-prod.json  Prod Worker task def template.
│   │   ├── alarms.yml              CloudWatch alarms stack.
│   │   ├── waf.yml                 WAF rules stack.
│   │   ├── dashboard.json          CloudWatch dashboard JSON.
│   │   └── deploy.sh               One-shot bring-up script.
│   ├── migration/                  Helper scripts for cross-region data moves.
│   │   ├── pg_dump_us_east.sh
│   │   ├── pg_restore_singapore.sh
│   │   ├── s3_sync_uploads.sh
│   │   └── verify_migration.sh
│   └── README.md                   Pinned region + sizing decisions.
│
├── .github/workflows/          Real CI/CD.
│   ├── ci.yml                  Lint + test + security scan + frontend build + SonarCloud.
│   ├── deploy-dev.yml          Push to `dev` → us-east-1 (account 371170753756).
│   └── deploy-prod.yml         Push to `main` → ap-southeast-1 Singapore (account 290172088819).
│
├── docs/                       Long-form docs.
│   ├── Handover_Meydan_2026-04/    This bundle.
│   └── ecommerce-feature-plan.{md,pdf}  Architectural plan for the parked e-commerce feature.
│
├── nginx.conf                  Local-dev edge proxy (when running docker-compose).
├── docker-compose.yml          Local dev stack (PG + Redis + frontend + backend + worker).
├── sonar-project.properties    SonarCloud config.
└── README.md                   Top-level repo overview.
```

## Where each concern lives

| Concern | Path |
|---|---|
| **Business logic** | `backend/app/routes/` (one router per resource) + `backend/app/utils/prompt_pipeline.py` (generation orchestration) |
| **Prompts** | `backend/app/utils/prompt_pipeline.py` (defaults). Live overrides in DB table `prompt_versions` via the admin Prompt Manager. |
| **Third-party clients** | `backend/app/utils/llm_clients.py` (OpenAI, Anthropic), `backend/app/utils/email.py` (Resend / SES), `backend/app/utils/cloudfront_acm.py` (ACM, CloudFront), `backend/app/utils/s3_deploy.py` (S3) |
| **Config** | `backend/.env.example` (all env vars + comments), `backend/app/config.py` (typed settings), live ECS task definitions for prod values |
| **Auth** | `backend/app/routes/auth.py` (issue), `backend/app/middleware/` (verify), `backend/app/utils/jwt.py` |
| **Tenant isolation** | `backend/app/database.py::get_tenant_db` (sets `search_path`) |
