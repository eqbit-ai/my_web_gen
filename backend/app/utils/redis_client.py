"""
Redis client for job queue management.

Jobs are stored as Redis hashes with the structure:
  job:{job_id} -> {status, type, result, error, created_at, updated_at, user_id, ...}

Job statuses: pending -> processing -> completed | failed
"""

import json
import os
import time
import uuid

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=500,
            socket_connect_timeout=5,
            socket_timeout=10,
            retry_on_timeout=True,
        )
    return _pool


async def close_redis():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Job helpers ──────────────────────────────────────────────────────────

JOB_PREFIX = "job:"
JOB_TTL = 3600  # Jobs expire after 1 hour
MAX_QUEUE_DEPTH = 2000  # Reject new jobs when queue exceeds this


async def get_queue_depth() -> int:
    """Return current number of jobs in the queue."""
    r = await get_redis()
    return await r.llen("queue:generate")


async def create_job(
    job_type: str,
    payload: dict,
    user_id: str,
) -> str:
    """Create a new job and push it to the queue. Returns job_id.
    Raises ValueError if queue is at capacity."""
    r = await get_redis()

    # Backpressure: reject if queue is overloaded
    depth = await r.llen("queue:generate")
    if depth >= MAX_QUEUE_DEPTH:
        raise ValueError(f"Queue is full ({depth} jobs pending). Please try again later.")

    job_id = str(uuid.uuid4())
    now = time.time()

    job_data = {
        "id": job_id,
        "type": job_type,
        "status": "pending",
        "payload": json.dumps(payload),
        "result": "",
        "error": "",
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
        "progress": 0,
        "progress_message": "Queued...",
    }

    pipe = r.pipeline()
    pipe.hset(f"{JOB_PREFIX}{job_id}", mapping=job_data)
    pipe.expire(f"{JOB_PREFIX}{job_id}", JOB_TTL)
    # Push to the processing queue
    pipe.lpush("queue:generate", job_id)
    # Index by user for fast lookups
    pipe.zadd(f"user_jobs:{user_id}", {job_id: now})
    pipe.expire(f"user_jobs:{user_id}", JOB_TTL)
    await pipe.execute()

    return job_id


async def get_job(job_id: str) -> dict | None:
    """Get job data by ID."""
    r = await get_redis()
    data = await r.hgetall(f"{JOB_PREFIX}{job_id}")
    if not data:
        return None
    # Parse JSON fields
    if data.get("payload"):
        data["payload"] = json.loads(data["payload"])
    if data.get("result"):
        try:
            data["result"] = json.loads(data["result"])
        except (json.JSONDecodeError, TypeError):
            pass
    # Convert numeric fields
    for field in ("created_at", "updated_at", "progress"):
        if field in data:
            try:
                data[field] = float(data[field])
            except (ValueError, TypeError):
                pass
    return data


async def update_job(job_id: str, **fields):
    """Update specific fields on a job."""
    r = await get_redis()
    updates = {"updated_at": time.time()}
    for k, v in fields.items():
        if k == "result" and isinstance(v, dict):
            updates[k] = json.dumps(v)
        else:
            updates[k] = v
    await r.hset(f"{JOB_PREFIX}{job_id}", mapping=updates)


async def get_user_jobs(user_id: str, limit: int = 20) -> list[dict]:
    """Get recent jobs for a user using sorted set index (O(log n))."""
    r = await get_redis()
    # Get job IDs from the per-user sorted set (newest first)
    job_ids = await r.zrevrange(f"user_jobs:{user_id}", 0, limit - 1)

    if not job_ids:
        return []

    jobs = []
    for jid in job_ids:
        data = await r.hgetall(f"{JOB_PREFIX}{jid}")
        if not data:
            continue
        if data.get("result"):
            try:
                data["result"] = json.loads(data["result"])
            except (json.JSONDecodeError, TypeError):
                pass
        jobs.append(data)
    return jobs
