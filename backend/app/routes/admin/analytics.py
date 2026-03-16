"""
Admin analytics endpoints: growth trends, generation success rates, token consumption.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.redis_client import get_redis

from .deps import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Analytics"])


@router.get("/analytics/growth")
async def analytics_growth(
    days: int = Query(default=30, ge=7, le=90),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily/weekly user growth trends."""
    now = datetime.now(UTC)
    start_date = now - timedelta(days=days)

    # Daily signups
    daily_signups = []
    try:
        result = await db.execute(text("""
            SELECT DATE(created_at) as day, COUNT(*) as count
            FROM users
            WHERE created_at >= :start
            GROUP BY DATE(created_at)
            ORDER BY day
        """), {"start": start_date})
        daily_signups = [{"date": str(r[0]), "count": r[1]} for r in result.fetchall()]
    except Exception:
        pass

    # Daily active users
    daily_active = []
    try:
        result = await db.execute(text("""
            SELECT DATE(last_login) as day, COUNT(*) as count
            FROM users
            WHERE last_login >= :start AND last_login IS NOT NULL
            GROUP BY DATE(last_login)
            ORDER BY day
        """), {"start": start_date})
        daily_active = [{"date": str(r[0]), "count": r[1]} for r in result.fetchall()]
    except Exception:
        pass

    # User status breakdown
    status_breakdown = []
    try:
        result = await db.execute(text("""
            SELECT
                CASE WHEN is_active THEN 'Active' ELSE 'Disabled' END as status,
                COUNT(*) as count
            FROM users GROUP BY is_active
        """))
        status_breakdown = [{"name": r[0], "value": r[1]} for r in result.fetchall()]
    except Exception:
        pass

    # Total users
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0

    # New users this week
    week_ago = now - timedelta(days=7)
    week_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    new_this_week = week_result.scalar() or 0

    return {
        "period_days": days,
        "total_users": total_users,
        "new_this_week": new_this_week,
        "daily_signups": daily_signups,
        "daily_active": daily_active,
        "status_breakdown": status_breakdown,
    }


@router.get("/analytics/generation-success")
async def analytics_generation_success(
    days: int = Query(default=30, ge=7, le=90),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generation success/fail rates over time."""
    start_date = datetime.now(UTC) - timedelta(days=days)

    # Daily generation counts by status
    daily_stats = []
    try:
        result = await db.execute(text("""
            SELECT
                DATE(created_at) as day,
                status,
                COUNT(*) as count
            FROM generation_logs
            WHERE created_at >= :start
            GROUP BY DATE(created_at), status
            ORDER BY day
        """), {"start": start_date})

        # Group by day
        day_map = {}
        for r in result.fetchall():
            day = str(r[0])
            if day not in day_map:
                day_map[day] = {"date": day, "completed": 0, "failed": 0, "pending": 0}
            status = r[1]
            if status in day_map[day]:
                day_map[day][status] = r[2]
            else:
                day_map[day][status] = r[2]

        daily_stats = list(day_map.values())
    except Exception:
        pass

    # Stage failure breakdown
    stage_failures = []
    try:
        result = await db.execute(text("""
            SELECT stage_failed, COUNT(*) as count
            FROM generation_logs
            WHERE status = 'failed' AND stage_failed IS NOT NULL
                AND created_at >= :start
            GROUP BY stage_failed
            ORDER BY count DESC
        """), {"start": start_date})
        stage_failures = [{"stage": r[0], "count": r[1]} for r in result.fetchall()]
    except Exception:
        pass

    # Redis job status snapshot
    job_status_counts = {"completed": 0, "failed": 0, "processing": 0, "pending": 0}
    try:
        r = await get_redis()
        async for key in r.scan_iter(match="job:*", count=200):
            status = await r.hget(key, "status")
            if status and status in job_status_counts:
                job_status_counts[status] += 1
    except Exception:
        pass

    job_statuses = [{"name": k.title(), "value": v} for k, v in job_status_counts.items() if v > 0]

    return {
        "period_days": days,
        "daily_stats": daily_stats,
        "stage_failures": stage_failures,
        "redis_job_statuses": job_statuses,
    }


@router.get("/analytics/token-consumption")
async def analytics_token_consumption(
    days: int = Query(default=30, ge=7, le=90),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Token consumption over time."""
    start_date = datetime.now(UTC) - timedelta(days=days)

    # Daily token spend from transactions
    daily_spend = []
    try:
        result = await db.execute(text("""
            SELECT
                DATE(created_at) as day,
                type,
                COALESCE(SUM(ABS(amount)), 0) as total_amount
            FROM token_transactions
            WHERE created_at >= :start
            GROUP BY DATE(created_at), type
            ORDER BY day
        """), {"start": start_date})

        day_map = {}
        for r in result.fetchall():
            day = str(r[0])
            if day not in day_map:
                day_map[day] = {"date": day, "granted": 0, "consumed": 0, "refunded": 0}
            txn_type = r[1]
            if txn_type == "grant":
                day_map[day]["granted"] = r[2]
            elif txn_type == "deduction":
                day_map[day]["consumed"] = r[2]
            elif txn_type == "refund":
                day_map[day]["refunded"] = r[2]

        daily_spend = list(day_map.values())
    except Exception:
        pass

    # Token balance distribution
    token_dist = []
    try:
        result = await db.execute(text("""
            SELECT
                CASE
                    WHEN token_balance <= 0 THEN 'Empty'
                    WHEN token_balance < 100000 THEN 'Low (<100K)'
                    WHEN token_balance < 500000 THEN 'Medium (100K-500K)'
                    WHEN token_balance < 1000000 THEN 'High (500K-1M)'
                    ELSE 'Full (1M+)'
                END as bucket,
                COUNT(*) as count
            FROM users
            GROUP BY bucket
            ORDER BY MIN(token_balance)
        """))
        token_dist = [{"name": r[0], "value": r[1]} for r in result.fetchall()]
    except Exception:
        pass

    # Top consumers
    top_generators = []
    try:
        result = await db.execute(text("""
            SELECT full_name, generation_count, tokens_used, token_balance
            FROM users
            WHERE generation_count > 0
            ORDER BY generation_count DESC
            LIMIT 10
        """))
        top_generators = [
            {"name": r[0], "generations": r[1], "tokens_used": r[2], "token_balance": r[3]}
            for r in result.fetchall()
        ]
    except Exception:
        pass

    return {
        "period_days": days,
        "daily_spend": daily_spend,
        "token_distribution": token_dist,
        "top_generators": top_generators,
    }
