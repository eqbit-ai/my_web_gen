# 9. Ongoing Costs

> **Authoritative source**: the **Ongoing Costs sheet** in the handover workbook. The numbers below are engineering estimates. Update the workbook from AWS Cost Explorer and the provider billing pages on the day of delivery.

## Snapshot — what's live and billing today

### Production (`ap-southeast-1`, account `290172088819`)

| Resource | Sizing | $ / month |
|---|---:|---:|
| RDS PostgreSQL `db.t4g.medium` Multi-AZ + 20 GB gp3 | 2 vCPU, 4 GB | ~$140 |
| ElastiCache Redis `cache.t3.small` | 1 node | ~$30 |
| ALB | + LCU + WAF rules | ~$25 |
| ECS Fargate API — 2 tasks min, autoscale 6 max (2 vCPU / 4 GB) | $83 / task / mo at min | $166 idle → $498 peak |
| ECS Fargate Worker — 1 task min, autoscale 8 max (2 vCPU / 4 GB) | $83 / task / mo | $83 idle → $663 peak |
| ECS Fargate Frontend — 2 tasks fixed (1 vCPU / 2 GB) | $42 / task / mo | $84 |
| WAF | rules + WCU | ~$10 |
| CloudWatch logs + alarms + dashboard | | ~$20 |
| Secrets Manager (12 secrets) | $0.40 / secret | $5 |
| ECR + S3 + small misc | | ~$5 |
| **Idle (no traffic)** | | **~$570** |
| **Peak (200 concurrent generations sustained)** | | **~$1,520** |
| **Realistic monthly bill (B2B SaaS pattern, 4–6 hr active per day)** | | **~$700 – $900** |

### Dev (`us-east-1`, account `371170753756`) — testing only post-migration

| Resource | Sizing | $ / month |
|---|---:|---:|
| RDS PostgreSQL `db.t3.medium` single-AZ | 2 vCPU, 4 GB | ~$60 |
| ElastiCache Redis `cache.t3.small` | 1 node | ~$24 |
| ALB | | ~$16 |
| ECS Fargate API + Worker + Frontend | fixed counts | ~$70 |
| **Subtotal — running 24/7** | | **~$170** |

> **Optimisation**: the user has indicated dev should be scaled to 0 between testing sessions. If that lands, dev burn drops to ~$30 / month (RDS storage + Redis idle + ALB), regaining ~$140 / month.

## Third-party services

| Service | Plan | Monthly | Billing cycle | Notes |
|---|---|---:|---|---|
| **OpenAI** | (production tier) | **$300 – $5,000** | Monthly post-pay | At observed rate (~$0.04 per generation for stages 0+1), 1,000 sites/mo ≈ $40; 50,000 sites/mo ≈ $2,000. **Tier upgrades are critical-path for scale** — see `10_known_issues_and_support.md`. |
| **Anthropic** | (production tier) | **$1,000 – $12,000** | Monthly post-pay | Stages 2+3 dominate cost (~$0.21 per generation). Same tier-upgrade caveat. |
| **Resend** | (Transactional) | $20 – $100 | Monthly | Welcome emails, password reset, generation notifications, custom-domain alerts. |
| **OpenProvider** | (Domain reseller) | $0 fixed + per-domain | Per-purchase | Each customer-purchased domain (~$10 – $25 / year retail margin). Pass-through cost. |
| **AWS CloudFront** | Pay-as-you-go | $5 – $50 | Monthly | First 1 TB egress / month free; thereafter ~$0.085 / GB in ap-southeast-1. Per-customer-domain distributions add $0 fixed (request-priced). One distribution per custom domain currently. |
| **Pexels API** | Free | $0 | — | Stock photos for generated sites. |
| **Unsplash API** | Free | $0 | — | Same. |
| **Sentry** (optional) | Developer | $0 – $26 | Monthly | Error tracking. Currently disabled — `SENTRY_DSN` is unset. |
| **SonarCloud** | Open-source | $0 | — | Code quality scans — currently red on every push because `SONAR_TOKEN` is missing from GitHub repo secrets. Fix or remove the SonarCloud step from `ci.yml`. |

## Cost-per-active-user estimate

**Assumptions**:
- Each *active user* generates 3 sites per month (typical SMB onboarding).
- Each generation costs ~$0.25 in LLM tokens (Stage 0–3 combined).
- Each generation hits the API ~30 times during the editing session (CRUD, edit-stream, deploy).
- AWS infrastructure cost is amortised across all active users at a given month.

**Per-active-user cost**:
- LLM: 3 generations × $0.25 = **$0.75**
- AWS variable (extra ECS task-time, S3 puts, CloudWatch ingestion): **~$0.10**
- Email + DNS + misc: **~$0.05**
- **Variable cost per active user: ~$0.90 / month**
- **Fixed cost**: $700 – $900 monthly. Per-user fixed cost falls fast with scale (e.g. 1,000 active users → ~$0.80 / user fixed; 10,000 active users → ~$0.08 / user fixed).
- **All-in per-active-user at 1,000 active users / month: ~$1.70**.

## Free tiers, trial periods, and cutover dates

| Service | Free tier ends when | Action when it ends |
|---|---|---|
| **AWS new-account credits** | The prod account `290172088819` does not currently have promotional credits applied; if the client transfers AWS credits, apply via Billing → Credits before regular charges land. | N/A unless transferred. |
| **AWS CloudFront** | First 1 TB egress / month is free permanently. Above that, ~$0.085 / GB in ap-southeast-1. | Watch the egress trend in CloudFront → Reports → Usage. |
| **Sentry Developer plan** | At 5,000 errors / month — automatic upgrade prompt. | Currently disabled; no immediate concern. |
| **Pexels / Unsplash** | Soft-rate-limited, never billed at our scale. | — |
| **Resend** | First 3,000 emails / month free, then $20 / mo for 50,000. | Already billing — verify in workbook. |
| **OpenAI / Anthropic** | Pay-as-you-go from token #1; no free tier. | Already billing. |

## Where to look on day-of-delivery

| Question | Where |
|---|---|
| "What did AWS bill us last month?" | AWS Cost Explorer, filter `Environment=production` and `Project=meydan-ai`. |
| "What did OpenAI bill us last month?" | platform.openai.com → Usage → Costs. |
| "What did Anthropic bill us last month?" | console.anthropic.com → Plans & billing. |
| "What's our run-rate this month?" | Combine the three above; the **Ongoing Costs sheet** in the workbook keeps the historical roll-up. |
