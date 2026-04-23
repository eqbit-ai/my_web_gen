"""
CloudWatch custom metrics bridge.

Reads from the in-memory metrics collector and flushes to CloudWatch
every 60 seconds. This powers dashboards, alarms, and auto-scaling.

Namespace: Meydan/{Environment}
Dimensions: Service (api | worker)
"""

import asyncio
import logging
import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.utils import metrics as app_metrics
from app.utils.circuit_breaker import get_circuit_status
from app.utils.redis_client import get_queue_depth

logger = logging.getLogger(__name__)

FLUSH_INTERVAL = 60  # seconds
NAMESPACE = f"Meydan/{os.getenv('ENVIRONMENT', 'dev')}"
REGION = os.getenv("AWS_REGION", "me-central-1")

# Cache the previous counter values so we can emit deltas (rate per interval)
_prev_counters: dict[str, int] = {}


def _cw_client():
    """Create a CloudWatch client (lazy, one per flush)."""
    return boto3.client("cloudwatch", region_name=REGION)


def _build_metric_data(service: str) -> list[dict]:
    """Build the MetricData list from current in-memory metrics."""
    global _prev_counters

    snapshot = app_metrics.get_metrics()
    counters = snapshot.get("counters", {})
    histograms = snapshot.get("histograms", {})
    dims = [{"Name": "Service", "Value": service}]
    now = time.time()

    data: list[dict] = []

    # ── Counter deltas ──────────────────────────────────────────
    counter_names = [
        "requests_total", "errors_5xx", "errors_4xx",
        "rate_limit_hits", "generations_total",
        "llm_openai_calls", "llm_anthropic_calls",
        "llm_openai_errors", "llm_anthropic_errors",
        "jobs_completed", "jobs_failed",
    ]
    for name in counter_names:
        current = counters.get(name, 0)
        prev = _prev_counters.get(name, 0)
        delta = current - prev
        _prev_counters[name] = current
        if delta > 0:
            data.append({
                "MetricName": name,
                "Dimensions": dims,
                "Value": delta,
                "Unit": "Count",
            })

    # ── Histogram percentiles ───────────────────────────────────
    histogram_configs = [
        ("request_duration_ms", "Milliseconds"),
        ("llm_call_duration_ms", "Milliseconds"),
        ("llm_openai_duration_ms", "Milliseconds"),
        ("llm_anthropic_duration_ms", "Milliseconds"),
    ]
    for name, unit in histogram_configs:
        h = histograms.get(name)
        if not h:
            continue
        for stat in ("p95", "p99", "avg"):
            val = h.get(stat)
            if val is not None:
                data.append({
                    "MetricName": f"{name}_{stat}",
                    "Dimensions": dims,
                    "Value": round(val, 2),
                    "Unit": unit,
                })

    # ── Queue depth (from Redis) ────────────────────────────────
    # This is set externally before flush via _inject_queue_depth
    queue_depth = counters.get("_queue_depth", 0)
    data.append({
        "MetricName": "queue_depth",
        "Dimensions": dims,
        "Value": queue_depth,
        "Unit": "Count",
    })

    # ── Circuit breaker states ──────────────────────────────────
    state_map = {"closed": 0, "half_open": 1, "open": 2}
    try:
        for provider, status in get_circuit_status().items():
            state_val = state_map.get(status.get("state", "closed"), 0)
            data.append({
                "MetricName": "circuit_breaker_state",
                "Dimensions": dims + [{"Name": "Provider", "Value": provider}],
                "Value": state_val,
                "Unit": "None",
            })
    except Exception:
        pass

    return data


async def _flush_once(service: str):
    """Flush current metrics to CloudWatch."""
    try:
        # Snapshot queue depth into counters so _build_metric_data can read it
        try:
            depth = await get_queue_depth()
            app_metrics._metrics.counters["_queue_depth"] = depth
        except Exception:
            pass

        data = _build_metric_data(service)
        if not data:
            return

        # CloudWatch accepts max 1000 metric data points per call
        cw = _cw_client()
        for i in range(0, len(data), 20):
            batch = data[i:i + 20]
            cw.put_metric_data(Namespace=NAMESPACE, MetricData=batch)

        logger.debug("metrics_flushed", extra={"count": len(data), "namespace": NAMESPACE})
    except (BotoCoreError, ClientError) as e:
        logger.warning("cloudwatch_flush_failed", extra={"error": str(e)})
    except Exception as e:
        logger.warning("cloudwatch_flush_error", extra={"error": str(e)})


async def start_metrics_flusher(service: str = "api"):
    """Background loop that flushes metrics to CloudWatch every FLUSH_INTERVAL seconds.

    Returns the asyncio.Task so the caller can cancel it on shutdown.
    """
    async def _loop():
        # Wait a bit before first flush to let the app warm up
        await asyncio.sleep(10)
        while True:
            try:
                await _flush_once(service)
            except asyncio.CancelledError:
                # Final flush on shutdown
                await _flush_once(service)
                raise
            except Exception as e:
                logger.warning("metrics_loop_error", extra={"error": str(e)})
            await asyncio.sleep(FLUSH_INTERVAL)

    task = asyncio.create_task(_loop())
    logger.info("cloudwatch_metrics_started", extra={"service": service, "interval": FLUSH_INTERVAL, "namespace": NAMESPACE})
    return task
