# 6. API Reference

All endpoints are served by the FastAPI app at `https://meydanfzai.com/api`. OpenAPI JSON is exposed at `/api/openapi.json`; Swagger UI is available at `/api/docs` in non-production environments (gated by `ENVIRONMENT != "production"`).

## Authentication

- **Scheme**: Bearer JWT in the `Authorization` header.
  `Authorization: Bearer <token>`
- **Obtain a token**: `POST /api/auth/login` with `{ "email": "...", "password": "..." }`. The response contains `access_token` and `user`. Tokens expire after `JWT_EXPIRE_MINUTES` (default 1440 / 24 h).
- **Claims**: `user_id`, `license_number`, `db_schema`, `exp`. Admin-only endpoints additionally require `is_admin=true` on the `users` row.
- **Refresh**: no refresh token — the frontend re-authenticates by asking the user to log in again when the token expires (401 response).
- **Public endpoints** (no auth): `POST /api/forms/submit/{site_id}`, `POST /api/landing/chat`, `GET /api/health*`, `GET /api/images/search`, `GET /api/templates*`, `GET /api/components*`.

## Error codes

All errors return JSON `{ "detail": "<message>" }` with one of:

| Code | Meaning | Notes |
|---|---|---|
| 400 | Validation error | Check `detail` for Pydantic field errors. |
| 401 | Unauthenticated | Missing or expired token. |
| 403 | Forbidden | Logged in but not authorised (e.g. non-admin hitting `/api/admin/*`, or user acting on another tenant's site). |
| 404 | Not found | Resource does not exist or is soft-deleted. |
| 409 | Conflict | Duplicate signup, site name already taken, etc. |
| 413 | Payload too large | Upload exceeds per-route cap. |
| 422 | Unprocessable entity | FastAPI / Pydantic validation, structured list in `detail`. |
| 429 | Too many requests | Rate limit hit — see **Rate limits** below. |
| 451 | Unavailable for legal reasons | Content moderation rejected the prompt. |
| 500 | Server error | Always logged with a correlation ID. Include `X-Correlation-ID` from the response headers when filing a ticket. |
| 503 | Upstream unavailable | LLM circuit breaker open, or S3/CloudFront fault during deploy. |

## Rate limits

Redis sliding-window, enforced by `app/middleware/rate_limiter.py`:
- **Per authenticated user**: 60 requests / minute global; generation endpoints additionally limited to 10 / hour.
- **Per IP (unauthenticated)**: 30 requests / minute.
- **Per-user monthly generation cap**: stored on `users.max_generations_per_month`, default 50 on approval.
- On breach: `429 Too Many Requests` with `Retry-After` header in seconds.

## Endpoint catalogue

Format for each endpoint:
`METHOD PATH` — purpose. Inputs → outputs.

### Health
- `GET /api/health` — liveness probe. → `{"status":"ok"}`
- `GET /api/health/deep` — checks DB + Redis. → `{"db":"ok","redis":"ok"}` or 503.
- `GET /api/health/sse-test` — SSE ping for debugging.
- `POST /api/health/migrate` — admin-only, runs `alembic upgrade head`. Input: none. Output: summary of applied revisions.

### Auth (`/api/auth`)
- `POST /signup` — create a tenant. Input: `{email, password, full_name, company_name, license_number}`. Output: `{message, user_id}`.
- `POST /verify-email` — confirm email. Input: `{token}`.
- `POST /resend-verification` — resend link. Input: `{email}`.
- `POST /login` — authenticate. Input: `{email, password}`. Output: `{access_token, user}`.
- `GET /me` — current user profile (auth). Output: full user object including plan limits.
- `POST /forgot-password` — send reset email. Input: `{email}`.
- `POST /reset-password` — complete reset. Input: `{token, new_password}`.
- `POST /change-password` — authenticated password change. Input: `{current_password, new_password}`.
- `POST /token-request` — user asks for more generation tokens. Input: `{amount, reason}`.
- `GET /token-requests` — list the caller's own requests.

### Generator (`/api/generator`) — the core site builder
- `POST /generate-stream` — start a generation. Server-Sent Events stream. Input: `{brief, niche?, files?, template_id?}`. Events: `stage`, `progress`, `partial_html`, `done`, `error`. Output body on `done`: `{site_id, html, css, js, plan}`.
- `POST /upload-files` — attach reference files to an ongoing session. Multipart.
- `POST /restore-session` — reopen a prior generation session.
- `POST /sync-session` — persist in-editor state (auto-save).

### Sections (`/api/sections`) — per-section edits
- `GET /{session_id}` — full current section tree.
- `POST /reorder` — move a section. Input: `{session_id, from, to}`.
- `POST /delete` — remove a section. Input: `{session_id, section_id}`.
- `POST /duplicate` — clone a section.
- `POST /regenerate` — LLM regenerate one section. Input: `{session_id, section_id, instruction}`.
- `POST /update-text` — in-place text edit, no LLM. Input: `{session_id, section_id, path, value}`.
- `POST /update-style` — style tweak. Input: `{session_id, section_id, css_vars}`.
- `POST /update-nav` — edit global nav.
- `POST /update-footer` — edit global footer.
- `POST /update-meta` — SEO title / description / og-image.
- `POST /update-contact` — update contact-details widget across pages.
- `POST /toggle-visibility` — hide/show section.
- `POST /insert` — insert a section from the library.

### Projects (`/api/projects`)
- `GET /` — list the caller's sites.
- `GET /{project_id}` — detail (HTML + plan + metadata).
- `PATCH /{project_id}` — rename / describe.
- `DELETE /{project_id}` — soft-delete.

### Deploy (`/api/deploy`)
- `POST /` — deploy a site. Input: `{site_id, subdomain?, custom_domain?}`. Output: `{deploy_url, cloudfront_distribution_id, status}`.
- `POST /{site_id}/redeploy` — rebuild + reupload without touching DNS.
- `GET /{site_id}/status` — current deploy status.
- `GET /` — caller's deploy history.
- `POST /{site_id}/offline` — take a site offline (bucket policy flip).
- `POST /{site_id}/connect-domain` — point a user-owned domain at an existing deploy.
- `GET /{site_id}/domain-status` — ACM validation + CNAME status.
- `DELETE /{site_id}/disconnect-domain` — revert to Meydan subdomain.
- `GET /{site_id}/available-domains` — suggestions list.
- `DELETE /{site_id}` — delete S3 objects + CloudFront for a site.
- `GET /aws/status` — cross-region infra health summary.

### Domains (`/api/domains`) — OpenProvider registrar integration
- `GET /search?q=` — availability + pricing.
- `POST /purchase` — register a new domain. Input: `{domain, tld, contact}`.
- `POST /{domain_id}/retry-activation` — retry after registrar error.
- `GET /` — caller's domains.
- `GET /{domain_id}` — one domain.
- `POST /{domain_id}/connect` / `disconnect` — attach to a site.
- `PUT /{domain_id}/nameservers` — set custom NS.
- `GET/POST/DELETE /{domain_id}/dns` — CRUD DNS records at the registrar.
- `POST /{domain_id}/renew`, `PUT /{domain_id}/auto-renew` — lifecycle.
- `PUT /{domain_id}/contact`, `GET /{domain_id}/contact` — whois / registrant data.
- `PUT /{domain_id}/transfer-lock`, `…/whois-privacy`.
- `POST /{domain_id}/request-transfer`, `DELETE /{domain_id}/cancel-transfer`.
- `POST /{domain_id}/sync` — resync state from registrar.
- `GET /provider/status` — upstream health.

### DNS (`/api/dns`) — Cloudflare authoritative DNS per site
- `GET /{site_id}/records` — list records.
- `POST /{site_id}/records` — create record.
- `DELETE /{site_id}/records` — delete record.
- `GET /{site_id}/nameservers` — current NS values.

### Forms (`/api/forms`)
- `POST /submit/{site_id}` — public; receives a contact-form submission from a deployed site. Input: form-encoded body. Writes to `form_submissions`, emails the site owner. Rate-limited by IP.
- `GET /submissions` — caller's inbox (auth).
- `GET /unread-count` — badge count.
- `PATCH /submissions/{submission_id}/read` — mark read.
- `DELETE /submissions/{submission_id}` — soft-delete.

### Uploads (`/api/uploads`)
- `POST /upload` — multipart file upload. Output: `{url, filename, size}`.
- `GET /gallery` — the caller's uploaded assets.
- `GET /list/{project_id}` — assets for one project.
- `DELETE /{filename}` — remove an asset.
- `POST /from-url` — ingest from a URL.
- `POST /transform` — crop / resize (Pillow).

### Images (`/api/images`)
- `GET /search?q=&provider=pexels|unsplash` — stock imagery search proxy.

### Components (`/api/components`) — section library
- `GET /` — all section types.
- `GET /types` — categories.
- `GET /{component_type}` — variants within a type.
- `POST /generate` — LLM-generate a new component variant.
- `POST /preview-swap` — dry-run a swap (returns HTML diff).
- `POST /swap` — commit a swap.

### Templates (`/api/templates`) — 10 premium starters
- `GET /` — list.
- `GET /{template_id}` — detail.
- `GET /{template_id}/preview` — HTML preview.

### Site features (`/api/sites`)
- `GET /{site_id}/export` — download a ZIP of the current site.
- `GET/PUT /{site_id}/custom-code` — user-supplied `<head>` / `<body>` injections.
- `POST /track/{site_id}` — public; pageview ping from deployed sites.
- `GET /track/{site_id}` — admin: pageview series.
- `GET /{site_id}/analytics` — analytics for one site.

### Jobs (`/api/jobs`)
- `POST /submit` — enqueue a generic job.
- `GET /{job_id}` — status + result.
- `GET /` — caller's jobs.
- `DELETE /{job_id}` — cancel (best-effort).

### Edit feedback (`/api`)
- `POST /edit-feedback` — thumbs up/down on a recent edit. Input: `{edit_log_id, rating, comment?}`.

### Landing chat (`/api/landing`)
- `POST /chat` — public marketing-page chat. Input: `{message, session_id?}`. Output: `{reply, session_id}`.

### Metrics (`/api/metrics`)
- `GET /` — Prometheus-formatted metrics, gated by `METRICS_API_KEY`.

### Admin (`/api/admin`) — all endpoints require `is_admin=true`
Representative subset (full catalogue in `backend/app/routes/admin/`):
- **Users**: `GET /users`, `GET /users/{user_id}`, `POST /users/{user_id}/approve|disable|enable|reset-password|grant-tokens|set_limits`.
- **Stats**: `GET /stats`, `GET /system`.
- **Tokens**: `GET /tokens/transactions`, `POST /tokens/grant`, `GET /tokens/pool`, `GET /tokens/expiring`, `GET /tokens/requests`, `POST /tokens/requests/{id}/review`, `GET /tokens/consumption`.
- **Generations**: `GET /generations`, `/generations/queue`, `/generations/failed`, `/generations/redis-failed`, `POST /generations/{id}/retry`, `GET /generations/success-rate`.
- **Analytics**: `GET /analytics/growth|generation-success|token-consumption`.
- **Edit logs**: `GET /edit-logs`, `/edit-logs/stats`, `POST /edit-logs/categorize`.
- **Operations**: `GET /templates`, `PATCH /templates/{id}`, `GET /audit-logs`, CRUD `/announcements`, `GET /prompts`, `POST /prompts/{key}`, `POST /prompts/{key}/{version}/publish`, `POST /circuit/{provider}/reset`, `GET /moderation`, `POST /moderation/{action}`.

## Example request / response

### Login
```http
POST /api/auth/login HTTP/1.1
Host: meydanfzai.com
Content-Type: application/json

{"email":"founder@example.ae","password":"•••••••••"}
```
```json
200 OK
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 42,
    "email": "founder@example.ae",
    "full_name": "Jane Founder",
    "approved": true,
    "is_admin": false,
    "tokens_remaining": 842315,
    "max_sites": 2
  }
}
```

### Generate a site (SSE)
```http
POST /api/generator/generate-stream HTTP/1.1
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{"brief":"Boutique Dubai flower shop, modern, warm tones","niche":"flower_shop"}
```
```
event: stage
data: {"stage":"enhance","progress":0.1}

event: stage
data: {"stage":"plan","progress":0.3}

event: partial_html
data: {"html":"<section...>...</section>"}

event: done
data: {"site_id":"7a3c...","html":"...","plan":{...}}
```

### Deploy
```http
POST /api/deploy HTTP/1.1
Authorization: Bearer ...
Content-Type: application/json

{"site_id":"7a3c...","subdomain":"petal-studio"}
```
```json
200 OK
{
  "deploy_url": "https://petal-studio.meydanfzai.com",
  "cloudfront_distribution_id": "E2XXXXXXXX",
  "status": "deployed"
}
```

## OpenAPI
The FastAPI-generated OpenAPI document is the authoritative, always-up-to-date reference. Pull it with:
```
curl https://meydanfzai.com/api/openapi.json > openapi.json
```
