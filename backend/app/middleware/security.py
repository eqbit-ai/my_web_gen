"""
Security middleware (pure ASGI) — adds security headers, sanitizes request bodies,
enforces size limits.
"""

import re
import json
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_REQUEST_SIZE = 10 * 1024 * 1024
HTML_TAG_RE = re.compile(r"<[^>]+>")

SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"SAMEORIGIN"),
    (b"x-xss-protection", b"1; mode=block"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
]


def _strip_html_tags(value: str) -> str:
    return HTML_TAG_RE.sub("", value)


def _sanitize_dict(data: dict) -> dict:
    sanitized = {}
    code_fields = {
        "currentHtml", "currentCss", "currentJs",
        "elementHtml", "html", "css", "js",
    }
    for key, value in data.items():
        if isinstance(value, str):
            if key not in code_fields:
                sanitized[key] = _strip_html_tags(value)
            else:
                sanitized[key] = value
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_dict(item) if isinstance(item, dict)
                else _strip_html_tags(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check content-length header for size limit
        headers_raw = dict(scope.get("headers", []))
        content_length = headers_raw.get(b"content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            response = JSONResponse(
                status_code=413,
                content={"detail": "Request body too large (max 10MB)"},
            )
            await response(scope, receive, send)
            return

        # For JSON POST/PUT/PATCH, sanitize the body
        method = scope.get("method", "GET")
        content_type = headers_raw.get(b"content-type", b"").decode("utf-8", errors="ignore")
        needs_sanitize = method in ("POST", "PUT", "PATCH") and "application/json" in content_type

        # Skip body sanitization for SSE streaming endpoints to avoid blocking
        path = scope.get("path", "")
        is_streaming = path.endswith("-stream") or path.endswith("/stream")

        actual_receive = receive
        if needs_sanitize and not is_streaming:
            body_parts = []
            body_complete = False

            async def buffered_receive():
                nonlocal body_complete
                if not body_complete:
                    # Buffer the full body
                    while True:
                        message = await receive()
                        body = message.get("body", b"")
                        body_parts.append(body)
                        if not message.get("more_body", False):
                            body_complete = True
                            break

                    full_body = b"".join(body_parts)
                    if len(full_body) > MAX_REQUEST_SIZE:
                        return {"type": "http.request", "body": full_body}

                    if full_body:
                        try:
                            data = json.loads(full_body)
                            if isinstance(data, dict):
                                sanitized = _sanitize_dict(data)
                                full_body = json.dumps(sanitized).encode("utf-8")
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass

                    return {"type": "http.request", "body": full_body}
                else:
                    return {"type": "http.request", "body": b""}

            actual_receive = buffered_receive

        # Inject security headers into response
        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(SECURITY_HEADERS)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, actual_receive, send_with_security_headers)
