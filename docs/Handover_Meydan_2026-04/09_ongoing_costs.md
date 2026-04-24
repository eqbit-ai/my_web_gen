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
