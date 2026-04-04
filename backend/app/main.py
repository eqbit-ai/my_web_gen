"""
Meydan Free Zone - Website Generator Backend
"""

import asyncio
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
from app.middleware.correlation import CorrelationIDMiddleware
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
            # Track error rates for CloudWatch alarms
            if status_code >= 500:
                app_metrics.increment("errors_5xx")
            elif status_code >= 400:
                app_metrics.increment("errors_4xx")
            if not silent:
                method = scope.get("method", "")
                from app.middleware.correlation import get_correlation_id
                cid = get_correlation_id()
                logger.info(
                    f"[REQUEST] {method} {path} {status_code} in {duration_ms}ms",
                    extra={"correlation_id": cid, "status_code": status_code, "duration_ms": duration_ms},
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("server_starting", extra={"app": "Meydan Website Generator"})

    # Initialize Sentry (only if SENTRY_DSN is set)
    init_sentry()

    # Initialize database
    await init_db()

    # Fix NOT NULL constraints on optional user columns (one-time migration)
    try:
        from sqlalchemy import text
        from app.database import async_session
        async with async_session() as db:
            await db.execute(text("ALTER TABLE users ALTER COLUMN company_name DROP NOT NULL"))
            await db.execute(text("ALTER TABLE users ALTER COLUMN full_name DROP NOT NULL"))
            await db.execute(text("ALTER TABLE users ALTER COLUMN mobile DROP NOT NULL"))
            await db.execute(text("ALTER TABLE users ALTER COLUMN license_number DROP NOT NULL"))
            # Usage limits columns
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS edit_count INTEGER NOT NULL DEFAULT 0"))
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS max_generations INTEGER NOT NULL DEFAULT 2"))
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS max_edits INTEGER NOT NULL DEFAULT 30"))
            # One-time fix: reset generation_count for users where count exceeds max (test data)
            await db.execute(text("UPDATE users SET generation_count = 0 WHERE generation_count > max_generations"))
            # Site recipient email column
            await db.execute(text("ALTER TABLE sites ADD COLUMN IF NOT EXISTS recipient_email VARCHAR"))
            # Soft-delete column
            await db.execute(text("ALTER TABLE sites ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ"))
            # Add deleted_at to all tenant project tables
            tenant_schemas = await db.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'"))
            for (schema,) in tenant_schemas.fetchall():
                has_projects = await db.execute(text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = '{schema}' AND table_name = 'projects')"))
                if has_projects.scalar():
                    await db.execute(text(f'ALTER TABLE "{schema}".projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ'))
            await db.commit()
            logger.info("db_migration: schema updated")
    except Exception as e:
        # Already done or column doesn't exist — safe to ignore
        logger.debug(f"db_migration: skipped ({e})")

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

    # Start CloudWatch metrics flusher (non-blocking, logs warning if AWS creds missing)
    _cw_task = None
    try:
        from app.utils.cloudwatch_metrics import start_metrics_flusher
        _cw_task = await start_metrics_flusher(service="api")
    except Exception as e:
        logger.warning("cloudwatch_metrics_init_failed", extra={"error": str(e)})

    yield

    # Cancel CloudWatch flusher
    if _cw_task:
        _cw_task.cancel()
        try:
            await _cw_task
        except asyncio.CancelledError:
            pass

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

# Public CORS paths — these accept requests from ANY origin (deployed sites on S3/custom domains)
_PUBLIC_CORS_PREFIXES = ("/api/forms/submit", "/api/sites/track")


class PublicCORSMiddleware:
    """Allow any origin for public endpoints (form submit, page tracking).

    Deployed sites live on S3 or custom domains — we can't predict their origins.
    This runs BEFORE the main CORSMiddleware to handle these paths with open CORS.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if not any(path.startswith(p) for p in _PUBLIC_CORS_PREFIXES):
            return await self.app(scope, receive, send)

        # Extract origin from headers
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin", b"*").decode()

        if scope["method"] == "OPTIONS":
            # Handle preflight
            response_headers = [
                (b"access-control-allow-origin", origin.encode()),
                (b"access-control-allow-methods", b"POST, OPTIONS, GET"),
                (b"access-control-allow-headers", b"Content-Type"),
                (b"access-control-max-age", b"86400"),
                (b"content-length", b"0"),
            ]

            async def send_preflight(message):
                pass

            await send({"type": "http.response.start", "status": 204, "headers": response_headers})
            await send({"type": "http.response.body", "body": b""})
            return

        # For actual requests, inject CORS header into response (replacing any existing one to prevent duplicates)
        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = [
                    (k, v) for k, v in message.get("headers", [])
                    if k.lower() != b"access-control-allow-origin"
                ]
                headers.append((b"access-control-allow-origin", origin.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_cors)


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
app.add_middleware(PublicCORSMiddleware)  # Runs FIRST (outermost) for public endpoints
app.add_middleware(CorrelationIDMiddleware)  # Outermost — assigns X-Correlation-ID before anything else

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
