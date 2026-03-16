"""
Admin stats and dashboard overview endpoints.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.metrics import get_metrics
from app.utils.redis_client import get_redis

from .deps import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Stats"])


@router.get("/stats")
async def admin_stats(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard overview stats."""
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0

    active_users = 0
    try:
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        result = await db.execute(
            select(func.count(User.id)).where(User.last_login >= seven_days_ago)
        )
        active_users = result.scalar() or 0
    except Exception:
        pass

    metrics = get_metrics()
    total_generations = metrics.get("counters", {}).get("generations_total", 0)

    active_sessions = 0
    queue_depth = 0
    try:
        r = await get_redis()
        # Count only sessions that have a TTL (active) or all session keys
        async for _key in r.scan_iter(match="session:*", count=100):
            active_sessions += 1
        queue_depth = await r.llen("queue:generate")
    except Exception as e:
        logger.warning("Failed to get Redis stats: %s", e)

    from app.utils.circuit_breaker import get_circuit_status

    circuit_states = get_circuit_status()

    return {
        "total_users": total_users,
        "active_users_7d": active_users,
        "total_generations": total_generations,
        "active_sessions": active_sessions,
        "queue_depth": queue_depth,
        "circuit_breakers": circuit_states,
    }
