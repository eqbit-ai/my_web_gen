"""
Admin endpoints for edit logs — the dataset for prompt-pattern analysis.

GET  /api/admin/edit-logs                 — paginated list with filters
GET  /api/admin/edit-logs/stats           — counts by category/edit_kind/success
POST /api/admin/edit-logs/categorize     — manually trigger Phase B tagging
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.edit_log import EditFeedback, EditLog

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Edit Logs"])


@router.get("/edit-logs")
async def list_edit_logs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    category: str | None = None,
    edit_kind: str | None = None,
    success: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    q = select(EditLog).order_by(EditLog.created_at.desc())
    if category:   q = q.where(EditLog.category == category)
    if edit_kind:  q = q.where(EditLog.edit_kind == edit_kind)
    if success is not None: q = q.where(EditLog.success.is_(success))

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await db.execute(q.limit(limit).offset(offset))).scalars().all()

    return {
        "total": total or 0,
        "items": [{
            "id": str(r.id),
            "user_id": str(r.user_id) if r.user_id else None,
            "project_id": str(r.project_id) if r.project_id else None,
            "session_id": r.session_id,
            "correlation_id": r.correlation_id,
            "prompt": r.prompt,
            "edit_kind": r.edit_kind,
            "target_page": r.target_page,
            "category": r.category,
            "sections_edited": r.sections_edited,
            "full_rewrite": r.full_rewrite,
            "routing_confidence": r.routing_confidence,
            "success": r.success,
            "error_kind": r.error_kind,
            "duration_ms": r.duration_ms,
            "output_chars_delta": r.output_chars_delta,
            "created_at": _serialize_datetime(r.created_at),
        } for r in rows],
    }


@router.get("/edit-logs/stats")
async def edit_log_stats(
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    total = await db.scalar(select(func.count()).select_from(EditLog))
    by_kind = (await db.execute(
        select(EditLog.edit_kind, func.count()).group_by(EditLog.edit_kind)
    )).all()
    by_category = (await db.execute(
        select(EditLog.category, func.count()).group_by(EditLog.category)
    )).all()
    success_rate = await db.execute(
        select(EditLog.success, func.count()).group_by(EditLog.success)
    )
    sr = {bool(k): v for k, v in success_rate.all()}
    fb_counts = (await db.execute(
        select(EditFeedback.rating, func.count()).group_by(EditFeedback.rating)
    )).all()

    return {
        "total": total or 0,
        "by_kind": [{"kind": k, "count": v} for k, v in by_kind],
        "by_category": [{"category": k or "uncategorized", "count": v} for k, v in by_category],
        "success_rate": {
            "succeeded": sr.get(True, 0),
            "failed": sr.get(False, 0),
        },
        "feedback": [{"rating": r, "count": v} for r, v in fb_counts],
        "uncategorized": (await db.scalar(
            select(func.count()).select_from(EditLog).where(EditLog.category.is_(None))
        )) or 0,
    }


@router.post("/edit-logs/categorize")
async def trigger_categorize(
    batch: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _admin = Depends(require_admin),
):
    """Phase B: tag uncategorized prompts via Claude Haiku."""
    from app.utils.edit_categorizer import categorize_pending
    n = await categorize_pending(db, batch=batch)
    return {"categorized": n}
