"""
Health check routes — used by ALB target group health checks.
"""

import asyncio

from fastapi import APIRouter
from starlette.responses import StreamingResponse

router = APIRouter()


@router.get("/health/sse-test")
async def sse_test():
    """Minimal SSE test endpoint."""

    async def gen():
        for i in range(3):
            yield f"data: tick {i}\n\n"
            await asyncio.sleep(1)
        yield "data: done\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/health")
async def health_check():
    """Basic health check for ALB. Returns 200 if the app is running."""
    from app.middleware.request_tracker import is_shutting_down

    return {
        "status": "draining" if is_shutting_down() else "ok",
        "service": "meydan-website-generator",
    }


@router.get("/health/deep")
async def deep_health_check():
    """Deep health check — verifies Redis, DB, and LLM circuit breakers."""
    from app.middleware.request_tracker import get_inflight_count, is_shutting_down
    from app.utils.circuit_breaker import get_circuit_status

    checks = {"api": "ok"}

    try:
        from app.utils.redis_client import get_redis

        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    try:
        from sqlalchemy import text

        from app.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    circuits = get_circuit_status()
    for name, info in circuits.items():
        checks[f"llm_{name}"] = info["state"]

    all_ok = all(v == "ok" or v == "closed" for v in checks.values())

    return {
        "status": "draining" if is_shutting_down() else ("ok" if all_ok else "degraded"),
        "checks": checks,
        "inflight_requests": get_inflight_count(),
        "circuits": circuits,
    }
