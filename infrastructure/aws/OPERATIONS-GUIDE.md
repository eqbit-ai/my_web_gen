# Meydan AWS Operations Guide

## What's Deployed

| Component | AWS Resource | Purpose |
|-----------|-------------|---------|
| **Alarms + SNS** | CloudFormation stack `meydan-dev-alarms` | 11 alarms → email alerts |
| **Dashboard** | CloudWatch `Meydan-dev-Overview` | Single-pane ops view |
| **WAF** | CloudFormation stack `meydan-dev-waf` | XSS/SQLi protection on ALB |
| **S3 Lifecycle** | `meydan-dev-deployed-sites` bucket | Auto-archive old sites |
| **Custom Metrics** | Namespace `Meydan/dev` | App-level metrics in CloudWatch |
| **Correlation IDs** | Every request header `X-Correlation-ID` | End-to-end request tracing |

---

## 1. CloudWatch Dashboard

**Open it:**
```
https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=Meydan-dev-Overview
```

**What you see:**
- **Row 1** — Request count, P95/P99 latency, 5xx/4xx error rate
- **Row 2** — LLM call duration (OpenAI vs Anthropic), LLM errors, circuit breaker state
- **Row 3** — Job queue depth, jobs completed/failed, rate limit hits
- **Row 4** — ECS CPU, RDS CPU + connections, ALB request count + response time

**Tip:** Change the time range (top-right) to `1h` for recent activity or `1w` to spot trends.

---

## 2. Alarms & Alerts

**View alarms:**
```bash
aws cloudwatch describe-alarms --alarm-name-prefix meydan-dev --region us-east-1 --query 'MetricAlarms[*].{Name:AlarmName,State:StateValue}' --output table
```

**Alarms configured:**

| Alarm | Triggers When | Action |
|-------|--------------|--------|
| `api-5xx-spike` | >10 server errors in 5 min | Email |
| `api-p99-latency` | P99 > 5 seconds for 3 min | Email |
| `rate-limit-spike` | >50 rate-limited requests in 5 min | Email |
| `worker-queue-depth` | Queue > 100 jobs for 5 min | Email |
| `worker-job-failures` | >5 failed jobs in 10 min | Email |
| `circuit-openai-open` | OpenAI circuit breaker opens | Email |
| `circuit-anthropic-open` | Anthropic circuit breaker opens | Email |
| `rds-cpu-high` | RDS CPU > 80% for 5 min | Email |
| `rds-connections-high` | RDS connections > 80 for 5 min | Email |
| `alb-target-5xx` | >20 ALB target 5xx in 5 min | Email |

**IMPORTANT:** Check your email (`meydan.ai.center@gmail.com`) and confirm the SNS subscription — alarms won't send until confirmed.

**Test an alarm manually:**
```bash
aws cloudwatch set-alarm-state --alarm-name meydan-dev-api-5xx-spike --state-value ALARM --state-reason "Manual test" --region us-east-1
```

---

## 3. Debugging with Correlation IDs

Every API request gets a unique `X-Correlation-ID`. It flows through:
```
Client → API (logs) → Redis job → Worker (logs)
```

**Step 1: Get the correlation ID**
- Check browser DevTools → Network tab → Response Headers → `X-Correlation-ID`
- Or from the API response headers

**Step 2: Trace in CloudWatch Logs**

Go to: CloudWatch → Logs Insights → Select `/ecs/meydan-dev-api` and `/ecs/meydan-dev-worker`

```
fields @timestamp, @message
| filter correlation_id = "PASTE-YOUR-UUID-HERE"
| sort @timestamp asc
```

This shows every log line for that request across both services.

---

## 4. Common Log Queries

Open: CloudWatch → Logs Insights → Select log group(s)

**Find recent errors:**
```
fields @timestamp, logger, correlation_id, @message
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

**Slow API requests (>3 seconds):**
```
fields @timestamp, correlation_id, @message
| filter @message like /\[REQUEST\]/ and duration_ms > 3000
| sort @timestamp desc
| limit 50
```

**LLM failures:**
```
fields @timestamp, @message
| filter logger like /circuit_breaker/ and level = "ERROR"
| sort @timestamp desc
```

**Worker job failures:**
```
fields @timestamp, @message
| filter logger = "app.worker" and level = "ERROR"
| sort @timestamp desc
```

**Error count by source:**
```
fields logger
| filter level = "ERROR"
| stats count() as errors by logger
| sort errors desc
```

---

## 5. Custom Metrics

Metrics are pushed to CloudWatch every 60 seconds under namespace `Meydan/dev`.

**View via CLI:**
```bash
# API request count (last 1 hour)
aws cloudwatch get-metric-statistics \
  --namespace Meydan/dev \
  --metric-name requests_total \
  --dimensions Name=Service,Value=api \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Sum \
  --region us-east-1

# Queue depth (last 1 hour)
aws cloudwatch get-metric-statistics \
  --namespace Meydan/dev \
  --metric-name queue_depth \
  --dimensions Name=Service,Value=worker \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 --statistics Maximum \
  --region us-east-1
```

**Available metrics:**

| Metric | Service | What it tracks |
|--------|---------|---------------|
| `requests_total` | api | Total HTTP requests |
| `errors_5xx` | api | Server errors |
| `errors_4xx` | api | Client errors |
| `rate_limit_hits` | api | 429 responses served |
| `request_duration_ms_p95` | api | P95 latency |
| `request_duration_ms_p99` | api | P99 latency |
| `llm_openai_duration_ms_p95` | api | OpenAI call P95 |
| `llm_anthropic_duration_ms_p95` | api | Anthropic call P95 |
| `llm_openai_calls` | api | OpenAI call count |
| `llm_anthropic_calls` | api | Anthropic call count |
| `llm_openai_errors` | api | OpenAI failures |
| `llm_anthropic_errors` | api | Anthropic failures |
| `circuit_breaker_state` | api | 0=closed, 1=half_open, 2=open |
| `queue_depth` | worker | Pending jobs in Redis |
| `jobs_completed` | worker | Successfully finished jobs |
| `jobs_failed` | worker | Failed jobs |

---

## 6. WAF (Web Application Firewall)

**View blocked requests:**
```bash
aws wafv2 get-sampled-requests \
  --web-acl-arn $(aws cloudformation describe-stacks --stack-name meydan-dev-waf --query 'Stacks[0].Outputs[?OutputKey==`WebACLArn`].OutputValue' --output text --region us-east-1) \
  --rule-metric-name AWSManagedRulesCommonRuleSet \
  --scope REGIONAL \
  --time-window StartTime=$(date -u -v-1H +%Y-%m-%dT%H:%M:%S),EndTime=$(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-items 10 \
  --region us-east-1
```

**WAF rules active:**
- `AWSManagedRulesCommonRuleSet` — blocks XSS, SQLi, bad bots (SizeRestrictions_BODY excluded for LLM payloads)
- `AWSManagedRulesKnownBadInputsRuleSet` — blocks Log4j, SSRF patterns
- `RateLimitRule` — blocks IPs exceeding 2000 requests per 5 minutes

---

## 7. S3 Lifecycle

Applied to bucket `meydan-dev-deployed-sites`:
- Files move to **Infrequent Access** after 90 days (cheaper storage)
- **Incomplete multipart uploads** cleaned up after 7 days
- **Old versions** deleted after 30 days (if versioning is on)

No action needed — runs automatically.

---

## 8. Deploy Observability to Other Environments

When you're ready for staging or production:

```bash
cd infrastructure/aws

# Staging
./deploy-observability.sh staging

# Production
./deploy-observability.sh production
```

This creates separate stacks (`meydan-staging-alarms`, `meydan-production-waf`, etc.) with the same configuration. Remember to:
1. Update `dashboard.json` references from `dev` to the target env (or parameterize)
2. Confirm the new SNS email subscription
3. Deploy the backend code to the target ECS cluster

---

## 9. Quick Health Checks

```bash
# ECS service status
aws ecs describe-services --cluster meydan-dev-cluster \
  --services meydan-dev-api meydan-dev-worker meydan-dev-frontend \
  --region us-east-1 \
  --query 'services[*].{name:serviceName,running:runningCount,desired:desiredCount}' \
  --output table

# API health
curl -s https://meydan-dev-alb-889896533.us-east-1.elb.amazonaws.com/api/health | python3 -m json.tool

# Deep health (includes Redis, DB, circuit breakers)
curl -s https://meydan-dev-alb-889896533.us-east-1.elb.amazonaws.com/api/health/deep | python3 -m json.tool

# Recent CloudWatch logs (API)
aws logs tail /ecs/meydan-dev-api --since 5m --region us-east-1

# Recent CloudWatch logs (Worker)
aws logs tail /ecs/meydan-dev-worker --since 5m --region us-east-1
```

---

## 10. Cost Notes

- **CloudWatch custom metrics**: ~$0.30/metric/month × ~16 metrics = ~$5/month
- **CloudWatch alarms**: $0.10/alarm/month × 11 = ~$1.10/month
- **WAF**: $5/month + $0.60 per million requests
- **SNS email**: Free (first 1000 notifications)
- **S3 lifecycle**: Saves money by moving old sites to IA tier

**Total observability cost: ~$12/month for dev**
