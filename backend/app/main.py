"""
Meydan Free Zone - Website Generator Backend
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

load_dotenv()

from app.utils.logging_config import setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

from app.database import init_db
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.request_tracker import (
    RequestTrackerMiddleware,
    install_signal_handlers,
    wait_for_inflight_requests,
)
from app.middleware.security import SecurityHeadersMiddleware
from app.routes import admin as admin_routes
from app.routes import auth as auth_routes
from app.routes import components as component_routes
from app.routes import deploy as deploy_routes
from app.routes import dns as dns_routes
from app.routes import domains as domain_routes
from app.routes import forms as form_routes
from app.routes import site_features as site_feature_routes
from app.routes import generator as generator_routes
from app.routes import health, metrics_route
from app.routes import images as image_routes
from app.routes import jobs as job_routes
from app.routes import projects as project_routes
from app.routes import sections as section_routes
from app.routes import templates as template_routes
from app.routes import uploads as upload_routes
from app.utils import metrics as app_metrics
from app.utils.redis_client import close_redis, get_redis
from app.utils.sentry_setup import init_sentry


class RequestLoggingMiddleware:
    """Pure ASGI middleware — logs every request with method, path, status_code, duration_ms.
    Also records request count and duration metrics."""

    def __init__(self, app: ASGIApp):
        self.app = app

    # Paths to skip logging (noisy health checks, etc.)
    SILENT_PATHS = {"/api/health", "/health", "/api/health/"}

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        silent = path in self.SILENT_PATHS

        start = time.time()
        status_code = 500  # default in case send is never called

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.time() - start) * 1000, 2)
            app_metrics.increment("requests_total")
            app_metrics.observe("request_duration_ms", duration_ms)
            if not silent:
                method = scope.get("method", "")
                logger.info(f"[REQUEST] {method} {path} {status_code} in {duration_ms}ms")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("server_starting", extra={"app": "Meydan Website Generator"})

    # Initialize Sentry (only if SENTRY_DSN is set)
    init_sentry()

    # Initialize database
    await init_db()

    # Initialize Redis connection
    try:
        r = await get_redis()
        pong = await r.ping()
        logger.info("redis_connected", extra={"ping": pong})
    except Exception as e:
        logger.warning("redis_unavailable", extra={"error": str(e)})

    # Install graceful shutdown signal handlers
    install_signal_handlers()

    logger.info("server_ready", extra={"url": "http://localhost:8000"})

    yield

    # Wait for in-flight requests to drain
    await wait_for_inflight_requests()
    await close_redis()
    logger.info("server_shutdown")


app = FastAPI(
    title="Meydan Website Generator",
    description="AI Website Generator for Meydan Free Zone",
    version="2.0.0",
    lifespan=lifespan,
)

# Allowed CORS origins (configurable via env var, comma-separated)
_allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000",
).split(",")

# Middleware (applied bottom-to-top: CORS → Security → Rate Limiter → Request Tracker → Logging)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestTrackerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
app.include_router(generator_routes.router, prefix="/api/generator", tags=["Generator"])
app.include_router(project_routes.router, prefix="/api/projects", tags=["Projects"])
app.include_router(image_routes.router, prefix="/api/images", tags=["Images"])
app.include_router(component_routes.router, prefix="/api/components", tags=["Components"])
app.include_router(section_routes.router, prefix="/api/sections", tags=["Sections"])
app.include_router(job_routes.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(deploy_routes.router, prefix="/api/deploy", tags=["Deploy"])
app.include_router(dns_routes.router, prefix="/api/dns", tags=["DNS"])
app.include_router(template_routes.router, prefix="/api/templates", tags=["Templates"])
app.include_router(upload_routes.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(domain_routes.router, prefix="/api/domains", tags=["Domains"])
app.include_router(form_routes.router, prefix="/api/forms", tags=["Forms"])
app.include_router(site_feature_routes.router, prefix="/api/sites", tags=["Site Features"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Admin"])
app.include_router(metrics_route.router, prefix="/api/metrics", tags=["Metrics"])

# Static file serving for uploads
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
os.makedirs(str(UPLOADS_DIR), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
