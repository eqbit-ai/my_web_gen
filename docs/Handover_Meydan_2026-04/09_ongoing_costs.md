# 9. Ongoing Costs

As specified in the brief, the authoritative cost data is delivered directly in the **Ongoing Costs sheet** of the handover workbook.

This document is a pointer — it lists the paid services that must appear on that sheet, so the reviewer can confirm nothing was left out. Do not treat the figures here as authoritative; the workbook is the source of truth.

## Services that must appear on the sheet

| Service | What it does | Plan to verify is listed |
|---|---|---|
| **AWS** (consolidated bill) | ECS Fargate (API + Worker + Frontend), RDS PostgreSQL, ElastiCache Redis, ALB, S3 (app + per-tenant site buckets + logs), CloudFront, CloudWatch, ACM (free), Route 53 (minimal), Secrets Manager, WAF, ECR. | Pay-as-you-go; list as a single line with an itemised breakdown in a sub-table. |
| **OpenAI API** | Stage 0 (enhance) + Stage 1 (plan) + landing-page chat. | Usage-based; include current month-to-date and a 30-day projection. |
| **Anthropic API** | Stage 2 (HTML) + Stage 3 (JS) + in-editor LLM edits. | Usage-based; same as above. |
| **Resend** | Transactional email (verification, password reset, form submissions, admin alerts). | Free up to 3 000 emails / month, then per-email pricing; list the plan and renewal date. |
| **OpenProvider** | Domain registration (resold to users). | Per-domain cost; list margin model separately. |
| **Cloudflare** | Authoritative DNS for `meydanfzai.com` + tenant DNS automation. | Free plan at time of handover; note any paid features in use. |
| **Pexels** | Stock imagery search. | Free tier, API-rate-limited; list even if $0. |
| **Unsplash** | Stock imagery search. | Free tier; same. |
| **Sentry** (optional) | Error reporting. Only if `SENTRY_DSN` is set in prod. | List plan + renewal. |
| **SonarCloud** (optional) | Static analysis / code quality. Dev-time only. | List if kept active post-handover. |
| **GitHub** | Repository hosting + Actions minutes. | Seat count + Actions overage. |
| **Domain: `meydanfzai.com`** | Registered at OpenProvider. | Annual renewal date. |

## Approximate monthly cost (snapshot)

> **These are engineering estimates, not invoices.** The Ongoing Costs sheet in the workbook carries the authoritative, invoice-backed numbers. Update the workbook from AWS Cost Explorer and the provider billing pages on the day of delivery.
>
> Figures are in **USD / month** unless stated. Two columns:
> - **Dev (today)** — the current us-east-1 dev environment. Low traffic (single-digit concurrent generations).
> - **Prod target** — the UAE prod target sized for **500–1 000 concurrent generations** (see capacity plan). Empty at handover; these are forecast numbers you will pay *if and when* you scale to that load.

### AWS breakdown

| AWS service | Dev (today) | Prod target | Notes |
|---|---:|---:|---|
| ECS Fargate — API | ~$25 | ~$350 | Dev: 1 task × 0.5 vCPU / 1 GB. Prod: 5–10 tasks × 2 vCPU / 4 GB autoscale. |
| ECS Fargate — Worker | ~$25 | ~$700 | Dev: 1 task. Prod: 10–20 tasks × 2 vCPU / 4 GB to absorb burst. |
| ECS Fargate — Frontend | ~$10 | ~$40 | Tiny nginx container; could be replaced with S3+CloudFront only at prod. |
| RDS PostgreSQL | ~$25 | ~$450 | Dev: db.t3.micro single-AZ. Prod: r6g.xlarge Multi-AZ + RDS Proxy. |
| ElastiCache Redis | ~$15 | ~$300 | Dev: cache.t3.micro. Prod: cache.r6g.large 2-node replication. |
| Application Load Balancer | ~$20 | ~$100 | Hourly fee + LCU + data-transfer. |
| S3 (app + tenant sites + logs) | ~$5 | ~$150 | Storage + egress scales roughly linearly with tenant count. |
| CloudFront (CDN) | ~$5 | ~$150 | Edge egress to customer-site visitors. |
| CloudWatch (logs, metrics, alarms) | ~$20 | ~$150 | Log retention is the big lever; see s3-lifecycle.json. |
| AWS WAF | ~$10 | ~$40 | Fixed + per-rule. |
| Secrets Manager | ~$4 | ~$10 | $0.40 / secret / month × ~10–25 secrets. |
| ECR (image registry) | ~$1 | ~$5 | Storage only; pulls within AWS are free. |
| NAT Gateway (private → internet for LLM) | ~$5 | ~$150 | Runs hot on worker egress to OpenAI/Anthropic. |
| ACM (TLS certs), Route 53 (zones) | $0 | ~$5 | ACM is free; Route 53 zones are $0.50 each if you keep the cosmetic zones. |
| **AWS subtotal** | **~$170** | **~$2 600** | |

### Third-party breakdown

| Service | Dev (today) | Prod target | Notes |
|---|---:|---:|---|
| **OpenAI API** (GPT-4.1 + GPT-4.1-mini) | ~$30 | ~$600 | Stage 0 + Stage 1 per generation + landing-page chat. Per-generation ≈ $0.06. |
| **Anthropic API** (Claude Sonnet 4) | ~$50 | ~$3 500 | Stage 2 + Stage 3 per generation + every LLM-backed edit. Per-generation ≈ $0.25, per in-editor edit ≈ $0.05–0.15. |
| **Resend** (email) | $0 | ~$20–50 | Free tier ≤ 3 000 emails/mo. Pro $20 + overage afterwards. |
| **Cloudflare** (DNS) | $0 | $0 | Free plan is sufficient. |
| **Pexels** (images) | $0 | $0 | Free with rate caps. |
| **Unsplash** (images) | $0 | $0 | Free with rate caps. |
| **Sentry** (error tracking, optional) | $0 | ~$26 | Team plan when set up; currently disabled if `SENTRY_DSN` empty. |
| **SonarCloud** (static analysis, optional) | $0 | ~$10 | Paid only if kept after handover. |
| **GitHub** (repo + Actions) | ~$15 | ~$30 | ~3 seats × Team plan + Actions overage. |
| **OpenProvider** (domain registrar) | pass-through | pass-through | Cost of each domain is passed through to the user; margin set per the domains table. Not an operational expense. |
| **Domain: `meydanfzai.com`** | ~$1.25 | ~$1.25 | ~$15 / year at OpenProvider. |
| **Third-party subtotal** | **~$100** | **~$4 250** | |

### Totals

| | Dev (today) | Prod target |
|---|---:|---:|
| **All-in monthly cost** | **~$270 / mo** | **~$6 850 / mo** |

Range for prod at sustained 500–1 000 concurrent generations: **~$6 000 – $12 000 / mo**, depending mostly on LLM volume. Peak-hour bursts (when every worker is generating) can push the LLM line 2–3× for short windows — see `todo-prod-migration-capacity.md` in the team backlog.

### Per-generation economic unit

Rough unit cost to produce **one initial site** (all four LLM stages):

| Stage | Model | Rough tokens (in / out) | ≈ Cost |
|---|---|---|---|
| 0 — Enhance brief | GPT-4.1-mini | 3 000 / 1 000 | $0.003 |
| 1 — Plan (JSON) | GPT-4.1 | 5 000 / 4 000 | $0.055 |
| 2 — HTML | Claude Sonnet 4 | 8 000 / 10 000 | $0.174 |
| 3 — JS | Claude Sonnet 4 | 5 000 / 4 000 | $0.075 |
| **Total per site** | | | **~$0.31** |

In-editor edits typically cost **$0.05–$0.15** per edit (Claude Sonnet 4, smaller prompt + smaller completion).

At the target plan of 2 sites + ~20 edits per active user per month, LLM variable cost is **~$2–5 per active user per month**. Infrastructure is fixed-ish; the break-even point is around **~200 active users per month** at prod sizing.

## Required columns on the sheet (per the brief)

For each service:
1. Service name
2. Plan (e.g. "Pro", "Pay-as-you-go")
3. Monthly cost
4. Billing cycle (monthly, annual, usage)
5. Renewal date (where applicable)

## Derived figures that must appear

- **Cost per active user** — monthly total ÷ approved users with ≥ 1 site generated in the month.
- **Assumptions used** — at minimum:
  - Average generations per active user per month.
  - Average tokens per generation (input + output, per model).
  - Average deployed sites per active user.
  - Average S3 egress per site per month.
  - Currency (AED or USD) and FX rate used.

## Free tiers, trials, cutover dates to flag

- **Resend** — free 3 000 emails/month; cutover when monthly volume exceeds this.
- **Pexels / Unsplash** — free with rate caps; note expected caps at target user count.
- **Cloudflare** — free plan sufficient today; flag if usage nears paid-plan requirements (e.g. if Workers or Advanced Rate Limiting are added).
- **AWS** — no free tier applies at production scale; historical credits (if any) should be recorded on the sheet with the expiry date.
- **Sentry** — the hobby tier has an error-event cap; flag when production reaches ~70 % of cap.

## Where cost data lives in-system

- **LLM cost attribution** — the `token_transactions` table records model, prompt tokens, completion tokens, and computed USD cost per call. `GET /api/admin/tokens/consumption` aggregates these.
- **AWS spend** — authoritative in AWS Cost Explorer; filter by tag `Project=meydan-ai`. The CloudWatch dashboard surfaces ECS + RDS headline costs but is not billing-accurate.
- **Domains sold** — the `domains` table has `cost_paid` and `reseller_margin` columns populated from the OpenProvider callback.

When updating the workbook, pull fresh numbers from these three sources. The workbook sheet is the handover artefact — refresh it the day of delivery.
