import time

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.utils.auth import decode_access_token
from app.utils.redis_client import get_redis

RATE_LIMIT_RULES = [
    {
        "prefixes": ["/api/generator/iterate", "/api/sections/"],
        "limit": 20,
        "window": 60,
        "key_prefix": "rl:edit",
    },
    {
        "prefixes": ["/api/generator/"],
        "limit": 5,
        "window": 60,
        "key_prefix": "rl:gen",
    },
    {
        "prefixes": ["/api/auth/"],
        "limit": 60,
        "window": 60,
        "key_prefix": "rl:auth",
        "by_ip": True,
    },
    {
        "prefixes": ["/api/"],
        "limit": 300,
        "window": 60,
        "key_prefix": "rl:api",
    },
]

SKIP_PATHS = {"/health", "/api/health", "/healthz", "/"}
# Paths under /api/generator/ that should NOT count against the strict gen limit
GEN_SKIP_SUFFIXES = ["/sync-session", "/session/", "/restore-session"]


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path

        if path in SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        rule = self._match_rule(path)
        if rule is None:
            await self.app(scope, receive, send)
            return

        identity = self._resolve_identity(request, rule)
        redis_key = f"{rule['key_prefix']}:{identity}"

        try:
            remaining, retry_after = await self._check_rate_limit(redis_key, rule["limit"], rule["window"])
        except Exception:
            await self.app(scope, receive, send)
            return

        if remaining < 0:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rule["limit"]),
                    "X-RateLimit-Remaining": "0",
                },
            )
            await response(scope, receive, send)
            return

        # Inject rate limit headers into the response
        headers_to_add = {
            "x-ratelimit-limit": str(rule["limit"]),
            "x-ratelimit-remaining": str(max(remaining, 0)),
        }

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for k, v in headers_to_add.items():
                    headers.append((k.encode(), v.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _match_rule(self, path: str):
        for rule in RATE_LIMIT_RULES:
            for prefix in rule["prefixes"]:
                if path.startswith(prefix):
                    # Don't apply strict gen limit to lightweight session endpoints
                    if rule["key_prefix"] == "rl:gen" and any(s in path for s in GEN_SKIP_SUFFIXES):
                        continue
                    return rule
        return None

    def _resolve_identity(self, request: Request, rule: dict) -> str:
        if rule.get("by_ip"):
            return self._get_client_ip(request)

        token = self._extract_token(request)
        if token:
            payload = decode_access_token(token)
            if payload and "user_id" in payload:
                return f"user:{payload['user_id']}"

        return f"ip:{self._get_client_ip(request)}"

    def _extract_token(self, request: Request) -> str | None:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def _check_rate_limit(self, key: str, limit: int, window: int) -> tuple[int, int]:
        """Sliding window rate limit check. Returns (remaining, retry_after_seconds)."""
        redis = await get_redis()
        now = time.time()
        window_start = now - window

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()

        current_count = results[2]
        remaining = limit - current_count

        retry_after = 0
        if remaining < 0:
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window - now) + 1

        return remaining, retry_after
