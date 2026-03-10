"""
Graceful shutdown middleware for FastAPI (pure ASGI).

Tracks in-flight requests and orchestrates clean shutdown on SIGTERM/SIGINT.
During shutdown, new requests receive 503 (except health checks), and the
process waits up to 30 seconds for in-flight requests to drain before exiting.
"""

import asyncio
import logging
import signal

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("request_tracker")

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_inflight_count: int = 0
_inflight_lock: asyncio.Lock | None = None
_shutting_down: bool = False
_shutdown_event: asyncio.Event | None = None

GRACE_PERIOD_SECONDS: int = 30
HEALTH_CHECK_PATHS: frozenset[str] = frozenset({"/health", "/healthz", "/ready", "/api/health"})


def _get_lock() -> asyncio.Lock:
    global _inflight_lock
    if _inflight_lock is None:
        _inflight_lock = asyncio.Lock()
    return _inflight_lock


def _get_shutdown_event() -> asyncio.Event:
    global _shutdown_event
    if _shutdown_event is None:
        _shutdown_event = asyncio.Event()
    return _shutdown_event


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_inflight_count() -> int:
    return _inflight_count


def is_shutting_down() -> bool:
    return _shutting_down


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------


def _handle_shutdown_signal(signum: int, _frame: object) -> None:
    global _shutting_down
    sig_name = signal.Signals(signum).name
    logger.info("Received %s — initiating graceful shutdown", sig_name)
    _shutting_down = True
    try:
        loop = asyncio.get_running_loop()
        loop.call_soon_threadsafe(_get_shutdown_event().set)
    except RuntimeError:
        pass


def install_signal_handlers() -> None:
    global _shutting_down
    # Reset shutdown state on startup (important for uvicorn --reload)
    _shutting_down = False
    signal.signal(signal.SIGTERM, _handle_shutdown_signal)
    signal.signal(signal.SIGINT, _handle_shutdown_signal)
    logger.info("Graceful-shutdown signal handlers installed")


# ---------------------------------------------------------------------------
# Drain helper
# ---------------------------------------------------------------------------


async def wait_for_inflight_requests() -> None:
    if _inflight_count == 0:
        logger.info("No in-flight requests — shutting down immediately")
        return

    logger.info(
        "Waiting up to %ds for %d in-flight request(s) to complete",
        GRACE_PERIOD_SECONDS,
        _inflight_count,
    )

    elapsed = 0.0
    poll_interval = 0.25
    while _inflight_count > 0 and elapsed < GRACE_PERIOD_SECONDS:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    if _inflight_count > 0:
        logger.warning(
            "Grace period expired with %d request(s) still in flight — forcing shutdown",
            _inflight_count,
        )
    else:
        logger.info("All in-flight requests drained in %.1fs", elapsed)


# ---------------------------------------------------------------------------
# Middleware (pure ASGI)
# ---------------------------------------------------------------------------


class RequestTrackerMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        global _inflight_count
        path = scope.get("path", "")
        is_health = path in HEALTH_CHECK_PATHS

        if _shutting_down and not is_health:
            response = JSONResponse(
                status_code=503,
                content={"detail": "Server is shutting down. Please retry shortly."},
                headers={"Retry-After": "5"},
            )
            await response(scope, receive, send)
            return

        _inflight_count += 1
        try:
            await self.app(scope, receive, send)
        finally:
            _inflight_count -= 1
