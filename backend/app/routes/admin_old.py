"""
Admin panel API routes.

All endpoints require a valid JWT with is_admin=True in the payload.
Gracefully handles missing tables (audit_logs, etc.) by returning empty results.
"""

import logging
import platform
import sys
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db
from app.models.user import User
from app.utils.auth import decode_access_token
from app.utils.circuit_breaker import get_circuit_status, reset_circuit
from app.utils.metrics import get_metrics
from app.utils.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# ═══════════════════════════════════════════════════════════════════════
# ADMIN AUTH DEPENDENCY
# ═══════════════════════════════════════════════════════════════════════


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify the caller has admin privileges."""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


# ═══════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════


class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company_name: str
    license_number: str
    db_schema: str | None = None
    created_at: datetime | None = None
    last_login: datetime | None = None
    generation_count: int = 0
    is_active: bool = True
    is_admin: bool = False
    token_balance: int = 1_000_000
    tokens_used: int = 0


class UserDetailResponse(AdminUserResponse):
    projects_count: int = 0


class MessageResponse(BaseModel):
    message: str


# ═══════════════════════════════════════════════════════════════════════
# HELPER: safe column access
# ═══════════════════════════════════════════════════════════════════════


def _safe_getattr(obj, attr, default=None):
    """Get attribute from SQLAlchemy model, returning default if column doesn't exist."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def _user_to_dict(user: User) -> dict:
    """Convert User model to dict, handling missing columns gracefully."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "company_name": user.company_name,
        "license_number": user.license_number,
        "db_schema": user.db_schema,
        "created_at": _safe_getattr(user, "created_at"),
        "last_login": _safe_getattr(user, "last_login"),
        "generation_count": _safe_getattr(user, "generation_count", 0),
        "is_active": _safe_getattr(user, "is_active", True),
        "is_admin": _safe_getattr(user, "is_admin", False),
        "token_balance": _safe_getattr(user, "token_balance", 1_000_000),
        "tokens_used": _safe_getattr(user, "tokens_used", 0),
    }


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ═══════════════════════════════════════════════════════════════════════


@router.get("/stats")
async def admin_stats(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard overview stats."""
    # Total users
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0

    # Active users (last 7 days) — graceful if last_login column missing
    active_users = 0
    try:
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        result = await db.execute(select(func.count(User.id)).where(User.last_login >= seven_days_ago))
        active_users = result.scalar() or 0
    except Exception:
        pass  # Column may not exist yet

    # Total generations from metrics
    metrics = get_metrics()
    total_generations = metrics.get("counters", {}).get("generations_total", 0)

    # Redis stats
    active_sessions = 0
    queue_depth = 0
    try:
        r = await get_redis()
        # Count active sessions (keys matching session:*)
        active_sessions = 0
        async for _ in r.scan_iter(match="session:*", count=100):
            active_sessions += 1
        # Pending jobs in queue
        queue_depth = await r.llen("queue:generate")
    except Exception as e:
        logger.warning("Failed to get Redis stats: %s", e)

    # Circuit breaker states
    circuit_states = get_circuit_status()

    return {
        "total_users": total_users,
        "active_users_7d": active_users,
        "total_generations": total_generations,
        "active_sessions": active_sessions,
        "queue_depth": queue_depth,
        "circuit_breakers": circuit_states,
    }


@router.get("/analytics")
async def admin_analytics(
    days: int = Query(default=30, ge=7, le=90),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Time-series analytics for charts: daily signups, token distribution, etc."""
    now = datetime.now(UTC)
    start_date = now - timedelta(days=days)

    # ── Daily user signups ──
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

    # ── Token balance distribution (buckets) ──
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

    # ── Top users by generation count ──
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

    # ── User status breakdown ──
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

    # ── Recent logins (daily active users over time) ──
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

    # ── Generation jobs from Redis (status breakdown) ──
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
        "daily_signups": daily_signups,
        "daily_active": daily_active,
        "token_distribution": token_dist,
        "top_generators": top_generators,
        "status_breakdown": status_breakdown,
        "job_statuses": job_statuses,
    }


# ═══════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════


@router.get("/users")
async def list_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination."""
    result = await db.execute(select(User).order_by(User.id.desc()).limit(limit).offset(offset))
    users = result.scalars().all()

    # Total count for pagination
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar() or 0

    return {
        "users": [_user_to_dict(u) for u in users],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info for a specific user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = _user_to_dict(user)

    # Count projects in tenant schema
    projects_count = 0
    if user.db_schema:
        try:
            result = await db.execute(text(f'SELECT count(*) FROM "{user.db_schema}".projects'))
            projects_count = result.scalar() or 0
        except Exception:
            pass  # Table may not exist

    user_data["projects_count"] = projects_count
    return user_data


@router.post("/users/{user_id}/disable", response_model=MessageResponse)
async def disable_user(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Disable a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await db.execute(update(User).where(User.id == user_id).values(is_active=False))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disable user — is_active column may not exist yet: {e}",
        ) from e

    return {"message": f"User {user.email} has been disabled"}


@router.post("/users/{user_id}/enable", response_model=MessageResponse)
async def enable_user(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Re-enable a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await db.execute(update(User).where(User.id == user_id).values(is_active=True))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enable user — is_active column may not exist yet: {e}",
        ) from e

    return {"message": f"User {user.email} has been re-enabled"}


class GrantTokensRequest(BaseModel):
    amount: int


@router.post("/users/{user_id}/grant-tokens", response_model=MessageResponse)
async def grant_tokens(
    user_id: int,
    req: GrantTokensRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Grant additional tokens to a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    try:
        await db.execute(
            update(User).where(User.id == user_id).values(
                token_balance=User.token_balance + req.amount
            )
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to grant tokens: {e}") from e

    new_balance = _safe_getattr(user, "token_balance", 0) + req.amount
    return {"message": f"Granted {req.amount:,} tokens to {user.email}. New balance: {new_balance:,}"}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-initiated password reset — generates a temporary password."""
    import secrets

    from app.utils.auth import hash_password

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a random temporary password
    temp_password = secrets.token_urlsafe(12)

    await db.execute(
        update(User).where(User.id == user_id).values(
            hashed_password=hash_password(temp_password)
        )
    )
    await db.commit()

    return {
        "message": f"Password reset for {user.email}",
        "temporary_password": temp_password,
    }


@router.get("/token-stats")
async def token_stats(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate token usage stats across all users."""
    try:
        result = await db.execute(text("""
            SELECT
                COUNT(*) as total_users,
                SUM(tokens_used) as total_tokens_consumed,
                SUM(token_balance) as total_tokens_remaining,
                AVG(tokens_used) as avg_tokens_per_user
            FROM users
        """))
        row = result.first()

        # Top token consumers
        top_result = await db.execute(text("""
            SELECT id, email, full_name, company_name, tokens_used, token_balance
            FROM users ORDER BY tokens_used DESC LIMIT 10
        """))
        top_users = [
            {"id": r[0], "email": r[1], "full_name": r[2], "company_name": r[3],
             "tokens_used": r[4], "token_balance": r[5]}
            for r in top_result.fetchall()
        ]

        # Users with zero balance
        zero_result = await db.execute(text("SELECT COUNT(*) FROM users WHERE token_balance <= 0"))
        zero_balance = zero_result.scalar() or 0

        return {
            "total_users": row[0] or 0,
            "total_tokens_consumed": row[1] or 0,
            "total_tokens_remaining": row[2] or 0,
            "avg_tokens_per_user": round(row[3] or 0),
            "users_zero_balance": zero_balance,
            "top_consumers": top_users,
        }
    except Exception as e:
        logger.warning(f"Token stats error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# GENERATION ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════════════


@router.get("/generations")
async def list_generations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: int | None = Query(default=None),
    admin=Depends(require_admin),
):
    """Recent generation activity from Redis job history."""
    try:
        r = await get_redis()

        # Scan for job keys
        job_keys = []
        async for key in r.scan_iter(match="job:*", count=200):
            job_keys.append(key)

        # Fetch job data
        jobs = []
        for key in job_keys:
            data = await r.hgetall(key)
            if not data:
                continue
            # Filter by user_id if specified
            if user_id and data.get("user_id") != str(user_id):
                continue
            jobs.append(
                {
                    "id": data.get("id", ""),
                    "type": data.get("type", ""),
                    "status": data.get("status", ""),
                    "user_id": data.get("user_id", ""),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "progress": data.get("progress", 0),
                    "progress_message": data.get("progress_message", ""),
                    "error": data.get("error", ""),
                }
            )

        # Sort by created_at descending
        jobs.sort(key=lambda j: float(j.get("created_at") or 0), reverse=True)

        total = len(jobs)
        jobs = jobs[offset : offset + limit]

        return {
            "generations": jobs,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to fetch generation logs: %s", e)
        return {
            "generations": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════════════
# CONTENT MODERATION
# ═══════════════════════════════════════════════════════════════════════


@router.get("/moderation")
async def moderation_queue(
    limit: int = Query(default=50, ge=1, le=200),
    admin=Depends(require_admin),
):
    """List flagged prompts from the moderation queue."""
    try:
        r = await get_redis()
        # Get flagged items from sorted set (newest first)
        items = await r.zrevrange("moderation:flagged", 0, limit - 1, withscores=True)

        flagged = []
        for item_json, score in items:
            try:
                import json

                item = json.loads(item_json)
                item["flagged_at"] = score
                flagged.append(item)
            except Exception:
                flagged.append({"raw": item_json, "flagged_at": score})

        return {"flagged": flagged, "total": await r.zcard("moderation:flagged")}
    except Exception as e:
        logger.warning("Failed to fetch moderation queue: %s", e)
        return {"flagged": [], "total": 0, "error": str(e)}


@router.post("/moderation/{action}")
async def moderation_action(
    action: str,
    item_id: str = Query(...),
    admin=Depends(require_admin),
):
    """Moderate a flagged item: approve, reject, or ban."""
    if action not in ("approve", "reject", "ban"):
        raise HTTPException(status_code=400, detail="Action must be: approve, reject, or ban")

    try:
        r = await get_redis()

        if action == "approve":
            # Remove from flagged set — scan and remove matching item
            items = await r.zrange("moderation:flagged", 0, -1)
            for item in items:
                if item_id in item:
                    await r.zrem("moderation:flagged", item)
                    break
            return {"message": f"Item {item_id} approved and removed from queue"}

        elif action == "reject":
            items = await r.zrange("moderation:flagged", 0, -1)
            for item in items:
                if item_id in item:
                    await r.zrem("moderation:flagged", item)
                    break
            return {"message": f"Item {item_id} rejected and removed from queue"}

        elif action == "ban":
            # Remove item and add user to banned set
            items = await r.zrange("moderation:flagged", 0, -1)
            for item in items:
                if item_id in item:
                    try:
                        import json

                        data = json.loads(item)
                        banned_user = data.get("user_id")
                        if banned_user:
                            await r.sadd("moderation:banned_users", str(banned_user))
                    except Exception:
                        pass
                    await r.zrem("moderation:flagged", item)
                    break
            return {"message": f"Item {item_id} removed, user banned"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moderation action failed: {e}") from e


# ═══════════════════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════════════════


@router.get("/system")
async def system_info(admin=Depends(require_admin)):
    """System health and resource usage."""
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "uptime_seconds": get_metrics().get("uptime_seconds", 0),
    }

    # CPU and memory via psutil (optional)
    try:
        import psutil

        info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total_mb": round(mem.total / (1024 * 1024), 1),
            "used_mb": round(mem.used / (1024 * 1024), 1),
            "percent": mem.percent,
        }
        proc = psutil.Process()
        info["process_memory_mb"] = round(proc.memory_info().rss / (1024 * 1024), 1)
    except ImportError:
        info["memory"] = {"error": "psutil not installed"}

    # Redis info
    try:
        r = await get_redis()
        redis_info = await r.info(section="memory")
        info["redis"] = {
            "used_memory_mb": round(int(redis_info.get("used_memory", 0)) / (1024 * 1024), 2),
            "connected_clients": redis_info.get("connected_clients", "unknown"),
        }
        # Queue sizes
        info["redis"]["queue_generate"] = await r.llen("queue:generate")
    except Exception as e:
        info["redis"] = {"error": str(e)}

    # Database connection pool stats
    try:
        pool = engine.pool
        info["database_pool"] = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    except Exception as e:
        info["database_pool"] = {"error": str(e)}

    # Circuit breaker states
    info["circuit_breakers"] = get_circuit_status()

    # Metrics summary
    info["metrics"] = get_metrics()

    return info


# ═══════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════


@router.post("/circuit/{provider}/reset", response_model=MessageResponse)
async def reset_circuit_breaker(
    provider: str,
    admin=Depends(require_admin),
):
    """Manually reset a circuit breaker to closed state."""
    success = await reset_circuit(provider)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No circuit breaker found for provider '{provider}'",
        )
    return {"message": f"Circuit breaker for '{provider}' reset to CLOSED"}
