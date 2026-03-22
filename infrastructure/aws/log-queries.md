# CloudWatch Insights — Saved Queries

## Trace a single request (by correlation ID)
```
fields @timestamp, @message
| filter correlation_id = "PASTE_UUID_HERE"
| sort @timestamp asc
```

## Find errors (last 1 hour)
```
fields @timestamp, logger, correlation_id, @message
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

## Slow API requests (>3s)
```
fields @timestamp, correlation_id, @message
| filter @message like /\[REQUEST\]/ and duration_ms > 3000
| sort @timestamp desc
| limit 50
```

## LLM failures (circuit breaker)
```
fields @timestamp, @message
| filter logger like /circuit_breaker/ and level = "ERROR"
| sort @timestamp desc
| limit 50
```

## Worker job failures
```
fields @timestamp, @message
| filter logger = "app.worker" and level = "ERROR"
| sort @timestamp desc
| limit 50
```

## Rate limit hits
```
fields @timestamp, @message
| filter @message like /Rate limit exceeded/
| stats count() by bin(5m)
```

## Error aggregation by logger
```
fields @timestamp, logger
| filter level = "ERROR"
| stats count() as error_count by logger
| sort error_count desc
```

## Queue depth over time
```
fields @timestamp, @message
| filter @message like /metrics_flushed/
| stats avg(queue_depth) by bin(5m)
```
