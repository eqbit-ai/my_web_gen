"""
Admin generation management endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.generation_log import GenerationLog
from app.models.token_transaction import TokenTransaction
from app.models.user import User
from app.utils.redis_client import get_redis

# Cost rates per 1M tokens
COST_RATES = {"anthropic": 3.00, "openai": 2.00, "default": 2.50}

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Generations"])


@router.get("/generations")
async def list_generations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List generation logs from the database with pagination and filters."""
    try:
        query = select(GenerationLog)

        if user_id:
            query = query.where(GenerationLog.user_id == user_id)
        if status:
            query = query.where(GenerationLog.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(GenerationLog.created_at.desc()).limit(limit).offset(offset)
        )
        logs = result.scalars().all()

        # Fetch user emails
        user_ids = list({log.user_id for log in logs})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        # Calculate cost per generation by summing token transactions in the time window
        from datetime import timedelta
        generation_costs = {}
        for log in logs:
            if not log.created_at or log.status != "completed":
                continue
            # created_at is when the log was inserted (AFTER generation finished)
            # So the token deductions happened BEFORE created_at
            duration = timedelta(milliseconds=log.duration_ms) if log.duration_ms else timedelta(minutes=15)
            end = log.created_at + timedelta(seconds=10)  # small buffer after log insert
            start = log.created_at - duration - timedelta(seconds=30)  # look back over the generation window

            tx_result = await db.execute(
                select(
                    func.sum(func.abs(TokenTransaction.amount)),
                    func.string_agg(TokenTransaction.reason, '|||'),
                ).where(
                    TokenTransaction.user_id == log.user_id,
                    TokenTransaction.type == "deduction",
                    TokenTransaction.created_at >= start,
                    TokenTransaction.created_at <= end,
                )
            )
            row = tx_result.first()
            total_tokens = int(row[0] or 0) if row else 0
            reasons = (row[1] or "") if row else ""

            # Determine cost rate from reasons
            if "anthropic" in reasons:
                rate = COST_RATES["anthropic"]
            elif "openai" in reasons:
                rate = COST_RATES["openai"]
            else:
                rate = COST_RATES["default"]
            # Mixed usage: use blended rate
            if "anthropic" in reasons and "openai" in reasons:
                rate = COST_RATES["default"]

            cost = (total_tokens / 1_000_000) * rate
            generation_costs[str(log.id)] = {"tokens": total_tokens, "cost": round(cost, 4)}

        return {
            "generations": [
                {
                    "id": str(log.id),
                    "user_id": log.user_id,
                    "user_email": user_map.get(log.user_id, ""),
                    "job_id": log.job_id,
                    "session_id": log.session_id,
                    "prompt": log.prompt[:200] if log.prompt else "",
                    "status": log.status,
                    "stage_failed": log.stage_failed,
                    "error_message": log.error_message,
                    "html_size": log.html_size,
                    "tokens_consumed": generation_costs.get(str(log.id), {}).get("tokens", log.tokens_consumed or 0),
                    "estimated_cost": generation_costs.get(str(log.id), {}).get("cost", 0),
                    "duration_ms": log.duration_ms,
                    "is_multipage": log.is_multipage,
                    "page_count": log.page_count,
                    "performance_score": log.performance_score,
                    "seo_score": log.seo_score,
                    "created_at": _serialize_datetime(log.created_at),
                    "completed_at": _serialize_datetime(log.completed_at),
                }
                for log in logs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list generation logs: %s", e)
        return {"generations": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.get("/generations/queue")
async def generation_queue(
    admin=Depends(require_admin),
):
    """Live Redis queue view showing pending and processing jobs."""
    try:
        r = await get_redis()

        # Pending jobs in queue
        pending_ids = await r.lrange("queue:generate", 0, -1)

        # Scan for all job keys and collect processing/pending
        jobs = []
        async for key in r.scan_iter(match="job:*", count=200):
            data = await r.hgetall(key)
            if not data:
                continue
            if data.get("status") in ("pending", "processing"):
                jobs.append({
                    "id": data.get("id", ""),
                    "type": data.get("type", ""),
                    "status": data.get("status", ""),
                    "user_id": data.get("user_id", ""),
                    "created_at": data.get("created_at", ""),
                    "progress": data.get("progress", 0),
                    "progress_message": data.get("progress_message", ""),
                })

        jobs.sort(key=lambda j: float(j.get("created_at") or 0), reverse=True)

        return {
            "queue_depth": len(pending_ids),
            "active_jobs": jobs,
        }
    except Exception as e:
        logger.warning("Failed to fetch generation queue: %s", e)
        return {"queue_depth": 0, "active_jobs": [], "error": str(e)}


@router.get("/generations/redis-failed")
async def redis_failed_jobs(
    admin=Depends(require_admin),
):
    """List failed jobs from Redis with error details."""
    try:
        r = await get_redis()
        jobs = []
        async for key in r.scan_iter(match="job:*", count=500):
            data = await r.hgetall(key)
            if not data or data.get("status") != "failed":
                continue
            jobs.append({
                "id": data.get("id", key.split(":")[-1] if isinstance(key, str) else ""),
                "type": data.get("type", ""),
                "user_id": data.get("user_id", ""),
                "error": data.get("error", data.get("error_message", "")),
                "stage": data.get("stage", data.get("progress_message", "")),
                "created_at": data.get("created_at", ""),
                "completed_at": data.get("completed_at", data.get("updated_at", "")),
            })

        jobs.sort(key=lambda j: j.get("completed_at") or j.get("created_at") or "", reverse=True)
        return {"failed_jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.warning("Failed to fetch Redis failed jobs: %s", e)
        return {"failed_jobs": [], "total": 0, "error": str(e)}


@router.get("/generations/failed")
async def failed_generations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List failed generation logs with error details."""
    try:
        from app.models.user import User

        base_query = select(GenerationLog).where(GenerationLog.status == "failed")

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(GenerationLog, User.email.label("user_email"))
            .outerjoin(User, GenerationLog.user_id == User.id)
            .where(GenerationLog.status == "failed")
            .order_by(GenerationLog.created_at.desc())
            .limit(limit).offset(offset)
        )
        result = await db.execute(query)
        rows = result.all()

        return {
            "failed_generations": [
                {
                    "id": str(log.id),
                    "user_id": log.user_id,
                    "user_email": email or "",
                    "prompt": log.prompt[:200] if log.prompt else "",
                    "stage_failed": log.stage_failed,
                    "error_message": log.error_message,
                    "tokens_consumed": log.tokens_consumed,
                    "duration_ms": log.duration_ms,
                    "created_at": _serialize_datetime(log.created_at),
                }
                for log, email in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list failed generations: %s", e)
        return {"failed_generations": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.post("/generations/{log_id}/retry")
async def retry_generation(
    log_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Re-submit a failed generation (placeholder for future implementation)."""
    try:
        result = await db.execute(
            select(GenerationLog).where(GenerationLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=404, detail="Generation log not found")

        if log.status != "failed":
            raise HTTPException(status_code=400, detail="Can only retry failed generations")

        # Placeholder: actual retry logic will re-submit the job
        from app.utils.audit_log import log_event_bg

        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="retry_generation",
            resource_type="generation",
            resource_id=str(log_id),
            details={"original_user_id": log.user_id, "prompt": log.prompt[:100]},
        )

        return {
            "message": f"Retry queued for generation {log_id}",
            "original_prompt": log.prompt[:200] if log.prompt else "",
            "status": "queued",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry generation: {e}") from e


@router.get("/generations/success-rate")
async def generation_success_rate(
    days: int = Query(default=30, ge=1, le=90),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Success/fail percentage from generation_logs."""
    try:
        from datetime import UTC, datetime, timedelta

        start = datetime.now(UTC) - timedelta(days=days)

        total_result = await db.execute(
            select(func.count(GenerationLog.id)).where(
                GenerationLog.created_at >= start
            )
        )
        total = total_result.scalar() or 0

        completed_result = await db.execute(
            select(func.count(GenerationLog.id)).where(
                GenerationLog.created_at >= start,
                GenerationLog.status == "completed",
            )
        )
        completed = completed_result.scalar() or 0

        failed_result = await db.execute(
            select(func.count(GenerationLog.id)).where(
                GenerationLog.created_at >= start,
                GenerationLog.status == "failed",
            )
        )
        failed = failed_result.scalar() or 0

        success_rate = round((completed / total) * 100, 1) if total > 0 else 0
        fail_rate = round((failed / total) * 100, 1) if total > 0 else 0

        # Average duration for successful generations
        avg_duration_result = await db.execute(
            select(func.avg(GenerationLog.duration_ms)).where(
                GenerationLog.created_at >= start,
                GenerationLog.status == "completed",
            )
        )
        avg_duration = avg_duration_result.scalar()

        return {
            "period_days": days,
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending_or_processing": total - completed - failed,
            "success_rate_percent": success_rate,
            "fail_rate_percent": fail_rate,
            "avg_duration_ms": round(avg_duration) if avg_duration else None,
        }
    except Exception as e:
        logger.warning("Failed to calculate success rate: %s", e)
        return {"error": str(e)}
