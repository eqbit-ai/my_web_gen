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
