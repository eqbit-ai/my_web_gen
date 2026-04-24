# 1. System Overview

**Read time: 5 minutes.**

## What it is
Meydan AI is a web application that lets a Meydan Free Zone business generate, edit, preview, and deploy a complete marketing website from a short text brief, without writing code.

## Who uses it
Small and mid-sized businesses licensed in Meydan Free Zone (UAE), who sign up with their company details and trade licence number and need a live website in hours rather than weeks.

## Tech stack
- **Language**: Python 3.12 (backend), JavaScript / React 18 (frontend)
- **Frameworks**: FastAPI (async), React (Create React App), SQLAlchemy async
- **Hosting**: AWS ECS Fargate (API + worker + frontend), S3 + CloudFront (deployed customer sites & static assets)
- **Database**: PostgreSQL 15 on RDS (schema-per-tenant isolation)
- **Cache / queue**: Redis (ElastiCache) — rate limits, job queue, session cache
- **Main AI models**: OpenAI GPT-4.1 (planning) and Anthropic Claude Sonnet 4 (HTML and JS generation)

## Top three external dependencies and their failure modes
1. **Anthropic API** — generates the HTML and JavaScript for every site and every in-editor edit. If it is down, no new generations or edits succeed; existing sites and the dashboard keep working. A circuit breaker opens after 5 consecutive failures and recovers automatically after 60 seconds.
2. **OpenAI API** — produces the JSON plan for every site (stage 1 of the pipeline). If it is down, generation fails at the first stage before any Anthropic cost is incurred. Same circuit-breaker behaviour as Anthropic.
3. **AWS S3 + CloudFront** — hosts every deployed customer site. If S3 is unavailable in the active region, *new* deploys fail but already-deployed sites continue to serve from CloudFront edge caches. If CloudFront misbehaves, previously-deployed sites stop serving — this is the highest-blast-radius dependency.

A secondary set — Resend (transactional email), OpenProvider (domain registration), Cloudflare (authoritative DNS for meydanfzai.com), and Pexels/Unsplash (stock imagery) — can each fail without taking the product down, but will break specific workflows (signup verification, domain purchase, DNS changes, image search).

## One-sentence summary
A multi-tenant, AI-driven website builder that turns a business brief into a deployed site on a custom or Meydan-subdomain, with an admin plane for approving tenants, capping usage, and observing costs.
