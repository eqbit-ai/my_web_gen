"""
Gunicorn configuration for production deployment.

Usage:
    gunicorn -c gunicorn.conf.py app.main:app
"""

import multiprocessing

# ---------------------------------------------------------------------------
# Server socket
# ---------------------------------------------------------------------------
bind = "0.0.0.0:8000"

# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
worker_class = "uvicorn.workers.UvicornWorker"

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
# 300s to accommodate long-running SSE streams and website generation jobs.
timeout = 300
graceful_timeout = 30
keepalive = 5

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
