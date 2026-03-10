"""
Lightweight in-process metrics collector.

No external dependencies — counters and histograms are kept in memory.
Histogram buckets are automatically trimmed to prevent unbounded growth.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Metrics:
    counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    histograms: Dict[str, list] = field(default_factory=lambda: defaultdict(list))
    _start_time: float = field(default_factory=time.time)


_metrics = Metrics()


def increment(name: str, value: int = 1):
    """Increment a named counter."""
    _metrics.counters[name] += value


def observe(name: str, value: float):
    """Record a value in a named histogram (e.g. request duration)."""
    hist = _metrics.histograms[name]
    hist.append(value)
    # Trim to prevent unbounded growth — keep last 500 observations
    if len(hist) > 1000:
        hist[:] = hist[-500:]


def get_metrics() -> Dict[str, Any]:
    """Return a snapshot of all metrics."""
    result: Dict[str, Any] = {
        "uptime_seconds": round(time.time() - _metrics._start_time, 1),
        "counters": dict(_metrics.counters),
        "histograms": {},
    }
    for name, values in _metrics.histograms.items():
        if values:
            sorted_v = sorted(values)
            n = len(sorted_v)
            result["histograms"][name] = {
                "count": n,
                "avg": round(sum(sorted_v) / n, 2),
                "p50": sorted_v[n // 2],
                "p95": sorted_v[int(n * 0.95)],
                "p99": sorted_v[int(n * 0.99)],
                "max": sorted_v[-1],
            }
    return result
