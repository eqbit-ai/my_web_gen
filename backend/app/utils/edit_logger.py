"""
Edit-log helper. Fire-and-forget logger that writes one row per edit attempt
without forcing edit endpoints to thread a `db` session through.

Phase A (now): writes a row per attempt. category column is left NULL.
Phase B (later): the categorize_pending() worker fills category in batches
via Claude Haiku. The same row is then queryable by category for evals.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Optional

from app.database import async_session
from app.models.edit_log import EditFeedback, EditLog

logger = logging.getLogger(__name__)


def log_edit_bg(
    *,
    user_id,
    project_id=None,
    session_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    prompt: str,
    edit_kind: str,
    target_page: Optional[str] = None,
    sections_edited: Optional[list[str]] = None,
    full_rewrite: bool = False,
    routing_confidence: Optional[float] = None,
    success: bool = False,
    error_kind: Optional[str] = None,
    duration_ms: Optional[int] = None,
    output_chars_delta: Optional[int] = None,
):
    """Schedule a write to edit_logs without blocking the calling request."""
    payload = dict(
        user_id=_coerce_uuid(user_id),
        project_id=_coerce_uuid(project_id),
        session_id=session_id,
        correlation_id=correlation_id,
        prompt=(prompt or "").strip()[:8000],
        edit_kind=edit_kind,
        target_page=target_page,
        sections_edited=",".join(sections_edited)[:255] if sections_edited else None,
        full_rewrite=bool(full_rewrite),
        routing_confidence=routing_confidence,
        success=bool(success),
        error_kind=error_kind,
        duration_ms=int(duration_ms) if duration_ms is not None else None,
        output_chars_delta=int(output_chars_delta) if output_chars_delta is not None else None,
    )
    try:
        asyncio.create_task(_write(payload))
    except RuntimeError:
        # No running loop (e.g. unit tests) — silently skip.
        pass


async def _write(payload: dict):
    try:
        async with async_session() as db:
            db.add(EditLog(**payload))
            await db.commit()
    except Exception:
        logger.exception("[edit_logger] failed to persist edit log")


def _coerce_uuid(v):
    if v is None:
        return None
    if isinstance(v, uuid.UUID):
        return v
    try:
        return uuid.UUID(str(v))
    except Exception:
        return None


# ── Stopwatch helper for routes that want duration_ms ────────────────────
class Stopwatch:
    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        return False

    @property
    def ms(self) -> int:
        return int((time.perf_counter() - self._t0) * 1000)


# ── Feedback writer (used by /api/edit-feedback endpoint) ───────────────
async def write_feedback(db, *, edit_log_id, user_id, rating: str, comment: Optional[str]):
    if rating not in ("up", "down"):
        raise ValueError("rating must be 'up' or 'down'")
    db.add(EditFeedback(
        edit_log_id=_coerce_uuid(edit_log_id),
        user_id=_coerce_uuid(user_id),
        rating=rating,
        comment=(comment or None) and comment[:2000],
    ))
    await db.commit()
