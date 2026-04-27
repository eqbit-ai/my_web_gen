# 1. System Overview

## What it is

An AI-powered website generator that produces a deployed, brand-consistent business website from a short brief in under 90 seconds.

## Who uses it

Small and mid-sized businesses licensed in Meydan Free Zone (UAE), who sign up with their company details and trade-licence number and need a live website in hours rather than weeks.

## Tech stack

| Layer | Choice |
|---|---|
| **Frontend** | React 18 (Create React App), React Router v6, GSAP animations, Monaco editor, custom CSS |
| **Backend** | Python 3.12, FastAPI (async), gunicorn + UvicornWorker |
| **Database** | PostgreSQL 15 (RDS Multi-AZ), tenant-per-schema isolation |
| **Cache + queue** | Redis 7 (ElastiCache) |
| **Hosting** | AWS ECS Fargate (`ap-southeast-1`), ALB, S3 static hosting for deployed customer sites |
| **Edge** | AWS CloudFront (CDN + SSL via ACM) + AWS WAF |
| **DNS** | AWS Route 53 (apex `meydanfzai.com` and customer custom domains) |
| **Email** | Resend (transactional) |
| **AI models** | OpenAI `gpt-4.1-mini` (enhance) + `gpt-4.1` (plan) and Anthropic `claude-sonnet-4-6` (HTML + JS generation) |

## Top three external dependencies

| Dependency | What breaks if it goes down | Mitigation in code |
|---|---|---|
| **Anthropic API** | Stage 2 (HTML) and Stage 3 (JS) generation halts. Users see an error page before any HTML is produced. | Circuit breaker opens after 5 failures (60s recovery); user gets a clean retry message. |
| **OpenAI API** | Stage 0 (enhance) and Stage 1 (plan) halt; pre-generation moderation fails closed → all new prompts blocked. | Same circuit-breaker pattern. Operator can flip `MODERATION_LLM_ENABLED=false` for keyword-only mode in an outage. |
| **AWS CloudFront** | The CDN edge for the platform and for every customer-deployed custom domain. If CloudFront has a region-wide degradation, customer sites slow / 5xx. | CloudFront has its own multi-region failover; outages are rare. Origin (ALB / S3) remains directly reachable, so an emergency runbook can re-point DNS straight at origin while CloudFront recovers. |
