"""
Redis-backed session store — replaces in-memory `sessions` dict.

Sessions are stored as Redis hashes with JSON-serialized values.
This enables horizontal scaling (multiple API instances share state)
and survives server restarts.
"""

import json

from app.utils.redis_client import get_redis

SESSION_PREFIX = "session:"
SESSION_TTL = 7200  # 2 hours


async def get_session(session_id: str) -> dict | None:
    """Get a session by ID. Returns None if not found."""
    r = await get_redis()
    raw = await r.get(f"{SESSION_PREFIX}{session_id}")
    if not raw:
        return None
    return json.loads(raw)


async def save_session(session_id: str, data: dict):
    """Save/update a session. Resets TTL on every write."""
    r = await get_redis()
    await r.set(f"{SESSION_PREFIX}{session_id}", json.dumps(data), ex=SESSION_TTL)


async def delete_session(session_id: str):
    """Delete a session."""
    r = await get_redis()
    await r.delete(f"{SESSION_PREFIX}{session_id}")


async def session_exists(session_id: str) -> bool:
    """Check if a session exists without loading it."""
    r = await get_redis()
    return bool(await r.exists(f"{SESSION_PREFIX}{session_id}"))


# ── SSE Event Queue (for decoupled generation) ──────────────────────

EVENT_PREFIX = "sse_events:"
EVENT_TTL = 3600  # 1 hour


async def push_sse_event(session_id: str, event_type: str, data: dict):
    """Push an SSE event to the session's event queue."""
    r = await get_redis()
    key = f"{EVENT_PREFIX}{session_id}"
    payload = json.dumps({"event": event_type, "data": data})
    await r.rpush(key, payload)
    await r.expire(key, EVENT_TTL)


async def pop_sse_events(session_id: str, start: int = 0) -> list:
    """Get all SSE events from index `start` onwards. Non-blocking."""
    r = await get_redis()
    key = f"{EVENT_PREFIX}{session_id}"
    raw_events = await r.lrange(key, start, -1)
    events = []
    for raw in raw_events:
        try:
            events.append(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            pass
    return events


async def clear_sse_events(session_id: str):
    """Clear SSE event queue for a session."""
    r = await get_redis()
    await r.delete(f"{EVENT_PREFIX}{session_id}")
