# 6. API Reference

Base URL: `https://meydanfzai.com/api`. Interactive Swagger at `/docs` (only in non-production `ENVIRONMENT` values).

## Authentication

All non-public endpoints require a JWT in the `Authorization` header:

```
Authorization: Bearer <token>
```

Obtain a token via `POST /api/auth/login`. Token claims: `user_id`, `email`, `is_admin`, `license_number`, `db_schema`. Default expiry **24 hours** (`JWT_EXPIRE_MINUTES=1440`).

## Common error codes

| Status | Meaning |
|---|---|
| `400` | Validation failure — payload didn't match the schema. Body: `{"detail": "..."}`. |
| `401` | Missing / invalid / expired JWT. Body: `{"detail": "Authentication required"}`. |
| `403` | Authenticated but not authorised (e.g. non-admin hitting `/api/admin/*`, or trying to access another tenant's data). |
| `404` | Resource not found OR exists in another tenant (we deliberately conflate to prevent IDOR fishing). |
| `409` | Conflict — e.g. signup with an existing email; deploy slug collision. |
| `429` | Rate limited. `Retry-After` header tells you when. |
| `500` | Server error. Body: `{"detail": "Internal server error"}`. The full traceback is in CloudWatch keyed by the `X-Correlation-ID` header. |
| `503` | LLM circuit breaker open (provider failing). Retry after 60 s. |

## Rate limits

Sliding-window per `(user_id, route_class)` keyed in Redis.

| Route class | Limit |
|---|---|
| `/api/auth/*` | 10 req / 5 min per IP |
| `/api/landing/*` | 30 req / 5 min per IP |
| `/api/generator/*` | 20 req / hour per user |
| `/api/admin/*` | 200 req / min per admin |
| All other | 60 req / min per user |

---

## Endpoints

### `POST /api/auth/signup`

Create a new account. Triggers email verification.

**Request**:
```json
{
  "email": "founder@acme.com",
  "password": "ValidStrong#1Pass",
  "full_name": "Acme Founder",
  "company_name": "ACME Trading FZ-LLC",
  "license_number": "MZ-12345"
}
```

**Response 201**:
```json
{ "user_id": 1429, "pending_approval": true, "email_verified": false }
```

Errors: `409` if email exists; `400` for validation (e.g. weak password — must be 12+ chars with upper, lower, digit, symbol).

---

### `POST /api/auth/login`

**Request**:
```json
{ "email": "founder@acme.com", "password": "ValidStrong#1Pass" }
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { "id": 1429, "email": "founder@acme.com", "is_admin": false, "is_approved": true }
}
```

Errors: `401` with generic "Invalid credentials" (does not reveal whether email exists).

---

### `POST /api/auth/forgot-password`

**Request**: `{ "email": "founder@acme.com" }`
**Response 200**: `{"ok": true}` — always 200, regardless of whether the email exists (anti-enumeration).

---

### `GET /api/auth/me`

Returns the JWT-authenticated user's record.

**Response 200**:
```json
{ "id": 1429, "email": "founder@acme.com", "is_admin": false, "is_approved": true, "tokens_balance": 847200 }
```

---

### `POST /api/generator/generate-stream`

Streams generation events back via Server-Sent Events. Long-lived connection (up to 300 s).

**Request**:
```json
{ "niche": "trading", "prompt": "ACME Trading is an import-export business based in Dubai..." }
```

**Response 200** (`text/event-stream`):
```
event: stage
data: {"stage": "enhance", "progress": 0.10}

event: stage
data: {"stage": "plan", "progress": 0.25}

...

event: complete
data: {"site_id": "uuid-...", "preview_url": "/editor/uuid-..."}
```

Errors: `400` if moderation rejects; `429` if rate-limited; `503` if LLM circuit open.

---

### `POST /api/sections/{section_id}/edit`

Apply an LLM-driven edit to a single section. Returns the patched section HTML/CSS/JS.

**Request**: `{ "instruction": "make the hero text bigger and use brand red" }`
**Response 200**: `{ "html": "...", "css": "...", "js": "...", "edit_log_id": 8821 }`

---

### `POST /api/deploy`

Package the current draft and publish to S3.

**Request**: `{ "session_id": "uuid-..." }`
**Response 200**:
```json
{ "url": "https://acme-trading.s3-website.ap-southeast-1.amazonaws.com", "deployed_at": "2026-04-27T00:34:11Z" }
```

Errors: `403` if `session_id` doesn't belong to caller; `500` if upload fails (generic message; full traceback logged).

---

### `POST /api/domains/buy`

Purchase a domain via OpenProvider, attach to the user's deployed site.

**Request**: `{ "domain": "acme-trading.com", "registration_years": 1 }`
**Response 200**: `{ "domain": "acme-trading.com", "status": "pending_dns", "estimated_active_in_seconds": 600 }`

The flow is async — the DNS record (Route 53) is created, ACM cert is requested, the API returns immediately and the user is notified via email when the domain is active. ALB idle is 300 s, so the request must not block on DNS propagation; clients use the `purchaseDomainAndWait` helper that polls `GET /api/domains/{name}/status`.

---

### `POST /api/landing/chat`

Public FAQ chatbot — no auth required. Anthropic Sonnet 4.6 backed.

**Request**:
```json
{ "messages": [ { "role": "user", "content": "How long does generation take?" } ] }
```
**Response 200**: `{ "answer": "Generation takes about 60-90 seconds end-to-end..." }`

Rate-limited 30 req / 5 min / IP.

---

### Admin endpoints (all require `is_admin=true`)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/admin/overview` | Stats panels for the Overview page |
| `GET` | `/api/admin/users?q=&page=` | Paginated user search |
| `GET` | `/api/admin/users/{id}` | User detail |
| `POST` | `/api/admin/users/{id}/approve` | Flip `is_approved=true` and grant 1M tokens |
| `POST` | `/api/admin/users/{id}/reject` | Mark user rejected, send email |
| `POST` | `/api/admin/users/{id}/grant-tokens` | `{amount, reason}` — credits tokens |
| `POST` | `/api/admin/users/{id}/suspend` | Compliance hold |
| `GET` | `/api/admin/sites` | All deployed sites across tenants |
| `GET` | `/api/admin/generation-stats` | Token spend, latency by stage |
| `GET` | `/api/admin/prompts` | Prompt manager — list stages |
| `POST` | `/api/admin/prompts/{stage}/versions` | Submit new prompt version |
| `POST` | `/api/admin/prompts/{stage}/versions/{id}/publish` | Activate a version |
| `POST` | `/api/admin/prompts/{stage}/versions/{id}/rollback` | Revert to prior |
| `GET` | `/api/admin/audit-log?from=&to=&q=` | Audit trail (paginated, filterable) |
| `GET` | `/api/admin/system-health` | Circuit-breaker state, queue depth |
| `POST` | `/api/admin/circuit/{provider}/reset` | Force-close a circuit breaker |
