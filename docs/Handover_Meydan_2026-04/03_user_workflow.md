# 3. User Workflow

This document describes the product as a numbered journey from sign-up to a deployed website. Screenshots referenced below live in `assets/screenshots/user/`; filenames are listed next to each step so they can be filled in without re-numbering.

## Main path

### Step 1 — Landing page
- **User**: Opens `https://meydanfzai.com` and clicks **Sign up**.
- **System**: Serves the marketing landing page (React SPA from CloudFront). No authentication.
- **Sees next**: The sign-up form.
- Screenshot: `01_landing.png`

### Step 2 — Sign up
- **User**: Enters full name, company name, work email, password, and Meydan trade-licence number.
- **System**: Validates licence format, hashes password (bcrypt), creates a `users` row in `public.users`, creates a dedicated Postgres schema `tenant_{sanitized_license}`, sends a verification email via Resend. The user is flagged `approved=false, tokens=0`.
- **Sees next**: "Check your email" screen.
- Screenshot: `02_signup.png`

### Step 3 — Verify email
- **User**: Clicks the verification link in the Resend email.
- **System**: Validates the JWT in the URL, sets `email_verified_at`, redirects to login.
- **Sees next**: Login screen with a success banner.
- Screenshot: `03_verify_email.png`

### Step 4 — Log in (pending approval)
- **User**: Logs in with email + password.
- **System**: Issues a JWT (`user_id`, `license_number`, `db_schema` in payload) and returns the user profile. Because `approved=false`, the dashboard surface is disabled and a Pending screen is shown.
- **Sees next**: "Your account is pending approval" page.
- Screenshot: `04_pending_approval.png`

### Step 5 — Approval
- **Admin (out of band)**: Approves the user from the admin panel (see `04_admin_workflow.md`). This sets `approved=true` and grants a 1M-token allowance.
- **User**: On next login (or page refresh) lands on the Dashboard.

### Step 6 — Dashboard (post-login home)
- **User**: Sees a light-themed dashboard with their existing sites, a "Create new site" CTA, usage counters (generations remaining, sites remaining), and a form-submissions inbox.
- **System**: `GET /api/projects`, `GET /api/forms/submissions`, `GET /api/auth/me`.
- **Sees next**: Either opens an existing site or clicks **New website**.
- Screenshot: `06_dashboard.png`

### Step 7 — New site — business brief
- **User**: Picks a niche (or lets the system detect it), describes the business in 1–3 sentences, optionally uploads a logo or reference files.
- **System**: Validates inputs, runs content moderation (`backend/app/utils/content_moderation.py`), enqueues a generation job.
- **Sees next**: Generator workspace with a live-updating progress log.
- Screenshot: `07_brief.png`

### Step 8 — Generation (streaming)
- **User**: Watches stage labels update ("Understanding brief…", "Planning sections…", "Writing HTML…", "Adding interactions…"). Typical end-to-end: 45–90 s.
- **System**: The 4-stage pipeline (see `02_architecture_diagram.md`) emits SSE events via `POST /api/generator/generate-stream`. The final HTML/CSS/JS is persisted in the tenant schema.
- **Sees next**: Preview iframe with the rendered site and a chat-style editor panel.
- Screenshot: `08_generating.png`

### Step 9 — Edit via chat + direct manipulation
- **User**: Asks for changes in plain language ("make the hero darker", "replace the third image", "add a pricing section"), or double-clicks any element to edit text inline, or uses the Section Editor to reorder / duplicate / delete sections.
- **System**: Routes each request through the appropriate handler:
  - Text edits → `POST /api/sections/update-text` (no LLM call).
  - Style edits → `POST /api/sections/update-style`.
  - Structural / creative edits → LLM-backed endpoints on `/api/sections/*` or `/api/generator/*`.
  - Every change is written to `edit_logs` for analytics and undo.
- **Sees next**: Updated preview, streamed back in real time.
- Screenshot: `09_editor.png`

### Step 10 — Deploy
- **User**: Clicks **Deploy**. Chooses a Meydan subdomain (free) or registers a custom domain (paid, via OpenProvider).
- **System**:
  - `POST /api/deploy` — builds final HTML, uploads to a per-tenant S3 bucket, creates/updates a CloudFront distribution, issues an ACM certificate for custom domains, writes DNS at Cloudflare.
  - Invalidates CloudFront so changes are visible within 30–60 seconds.
- **Sees next**: A green banner with the live URL and a **View site** button.
- Screenshot: `10_deployed.png`

### Step 11 — Ongoing management
- **User**: Returns to the dashboard any time to re-deploy after edits, view form submissions, connect a different domain, or generate a second site (up to the site-count cap on their plan).

## Main error states

| Trigger | User-visible message | Recovery path |
|---|---|---|
| LLM circuit breaker open (OpenAI or Anthropic) | "We're having trouble reaching our AI provider. Try again in a minute." | User retries; breaker self-resets after 60 s (`circuit_breaker.py`). |
| Generation limit hit for the month | "You've used all your generations for this plan. Contact support to request more." | User clicks *Request tokens*; creates a `token_requests` row. Admin reviews. |
| Site count limit hit | "You've reached the website limit on your plan." | Admin raises the cap from the admin panel. |
| Deploy fails (S3 / CloudFront / ACM error) | "Deployment failed — our team has been notified." | Correlation ID is logged. Admin retries from `/api/deploy/{site_id}/redeploy`. |
| Email not received | "Didn't get the email? Resend." | `POST /api/auth/resend-verification`. |
| Domain purchase fails at OpenProvider | "Domain registration failed. Try a different domain or use a Meydan subdomain." | Purchase is atomic — no partial state. User picks a new domain. |
| Session expired (JWT) | Silent redirect to login. | User re-authenticates. |

Every error surfaces the correlation ID in the browser console so support can trace it in CloudWatch.
