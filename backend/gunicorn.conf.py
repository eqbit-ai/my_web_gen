"""
Gunicorn configuration for production deployment.

Usage:
    gunicorn -c gunicorn.conf.py app.main:app
"""

import multiprocessing
import os

# ---------------------------------------------------------------------------
# Server socket
# ---------------------------------------------------------------------------
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------
_env_workers = int(os.environ.get("WORKERS", 0))
workers = _env_workers if _env_workers > 0 else min(multiprocessing.cpu_count() * 2 + 1, 16)
worker_class = "uvicorn.workers.UvicornWorker"

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
# 300s to accommodate long-running SSE streams and website generation jobs.
timeout = 300
graceful_timeout = 30
keepalive = 10

# ---------------------------------------------------------------------------
# Worker recycling (memory leak protection)
# ---------------------------------------------------------------------------
max_requests = 1000
max_requests_jitter = 50

# ---------------------------------------------------------------------------
# App loading
# ---------------------------------------------------------------------------
# Each worker must create its own asyncio event loop, so do NOT preload.
preload_app = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
accesslog = "-"
errorlog = "-"
loglevel = "info"

# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------
# Use /dev/shm for the worker heartbeat tmp file. This avoids disk I/O for
# the periodic health-check writes that Gunicorn uses to detect hung workers.
worker_tmp_dir = "/dev/shm"
