"""
Correlation ID middleware — assigns a unique ID to every request.

The ID propagates through logs, Redis job payloads, and worker processing
so that a single request can be traced end-to-end across services.

Usage:
    from app.middleware.correlation import get_correlation_id
    cid = get_correlation_id()  # returns current request's correlation ID
"""

import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

# ContextVar accessible from anywhere in the same async call chain
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

HEADER_NAME = "x-correlation-id"


def get_correlation_id() -> str:
    """Return the current correlation ID (empty string if not in a request context)."""
    return _correlation_id.get()


def set_correlation_id(cid: str) -> None:
    """Manually set the correlation ID (used by the worker when processing jobs)."""
    _correlation_id.set(cid)


class CorrelationIDMiddleware:
    """ASGI middleware that reads or generates X-Correlation-ID for every HTTP request."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract from incoming headers or generate a new one
        headers = dict(scope.get("headers", []))
        raw = headers.get(HEADER_NAME.encode(), b"")
        cid = raw.decode() if raw else str(uuid.uuid4())

        # Set in ContextVar for this request's lifetime
        token = _correlation_id.set(cid)

        try:
            # Inject into response headers
            async def send_with_cid(message):
                if message["type"] == "http.response.start":
                    resp_headers = list(message.get("headers", []))
                    resp_headers.append((HEADER_NAME.encode(), cid.encode()))
                    message = {**message, "headers": resp_headers}
                await send(message)

            await self.app(scope, receive, send_with_cid)
        finally:
            _correlation_id.reset(token)
