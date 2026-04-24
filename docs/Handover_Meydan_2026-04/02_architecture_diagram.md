# 2. Architecture Diagram

## Diagram

See `assets/architecture.png` (rendered) and `assets/architecture.drawio` (editable source — open with diagrams.net / draw.io).

A text rendering of the same diagram, legible on its own:

```
                        ┌──────────────────────────────┐
                        │          End user            │
                        │  (browser, meydanfzai.com)   │
                        └──────────────┬───────────────┘
                                       │ HTTPS
                                       ▼
                        ┌──────────────────────────────┐
                        │     CloudFront (CDN)         │
                        │  E368CULECTE3G5 + others     │
                        └──────┬──────────────┬────────┘
                               │              │
                ┌──────────────▼──────┐   ┌───▼─────────────────┐
                │ S3: app static bundle│   │ S3: per-tenant site │
                │ (React build)        │   │  buckets (deployed) │
                └──────────────────────┘   └─────────────────────┘
                               │
                               │ /api/* (XHR)
                               ▼
                        ┌──────────────────────────────┐
                        │  ALB (Application LB)        │
                        │   TLS terminate, 60s idle    │
                        └──────────────┬───────────────┘
                                       │
                        ┌──────────────▼───────────────┐
                        │  ECS Fargate: API service    │
                        │  FastAPI + gunicorn/uvicorn  │
                        └────┬────────────┬─────────┬──┘
                             │            │         │
                     ┌───────▼────┐  ┌────▼────┐  ┌─▼──────────┐
                     │ RDS Postgres│  │ Redis   │  │ ECS Fargate│
                     │  (schema    │  │ (Elasti │  │  Worker    │
                     │   per tenant)│ │  Cache) │  │ (jobs)     │
                     └─────────────┘  └─────────┘  └─┬──────────┘
                                                    │
                   ┌────────────────────────────────┼──────────────────────────────┐
                   │                                │                              │
           ┌───────▼────────┐              ┌────────▼────────┐          ┌──────────▼──────────┐
           │ OpenAI API     │              │ Anthropic API   │          │ OpenProvider (domain)│
           │ GPT-4.1 plan   │              │ Claude Sonnet 4 │          │ Cloudflare (DNS)     │
           │                │              │ HTML + JS       │          │ Resend (email)       │
           └────────────────┘              └─────────────────┘          │ Pexels / Unsplash    │
                                                                         └──────────────────────┘
```

## Caption — request path for "Generate a website"

1. The user submits a brief from the React app (`frontend/src/components/WebsiteGenerator.jsx`).
2. The browser issues `POST /api/generator/generate-stream` through CloudFront → ALB → an **API** Fargate task.
3. The API authenticates the JWT, checks Redis rate limits and usage caps, then enqueues a generation job in Redis and streams Server-Sent Events back to the browser.
4. A **Worker** Fargate task picks up the job and runs the 4-stage pipeline:
   - **Stage 0 — Enhance**: GPT-4.1-mini expands the brief.
   - **Stage 1 — Plan**: GPT-4.1 produces a JSON plan (brand, tokens, sections).
   - **Stage 2 — HTML**: Claude Sonnet 4 produces Tailwind-classed HTML.
   - **Stage 3 — JS**: Claude Sonnet 4 produces vanilla-JS interactions.
5. Each stage writes progress back to Redis; the API streams those updates to the browser as SSE events.
6. The completed HTML/CSS/JS is persisted in the tenant's PostgreSQL schema and, if the user clicks Deploy, uploaded to the tenant's S3 bucket, fronted by CloudFront, with DNS pointed by Cloudflare (custom domain) or a wildcard Meydan subdomain.

All LLM calls go through a per-provider circuit breaker (`backend/app/utils/circuit_breaker.py`). All requests are tagged with an `X-Correlation-ID` that follows the call from browser → API → worker → CloudWatch logs.

## File formats

- `assets/architecture.png` — rendered, ship-ready image.
- `assets/architecture.drawio` — editable source; open in https://app.diagrams.net or the VS Code extension.

> If the `assets/` files are missing at the time you read this, regenerate them from this ASCII spec — it is the source of truth for box / arrow layout.
