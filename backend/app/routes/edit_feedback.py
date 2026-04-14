"""
User-facing feedback endpoint for the chat thumbs up / thumbs down on a
completed AI edit. Writes to edit_feedback table joined to edit_logs.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.edit_log import EditFeedback, EditLog
from app.utils.auth import require_auth

router = APIRouter()


class FeedbackRequest(BaseModel):
    edit_log_id: str | None = None
    # Fallback: if frontend doesn't have the edit_log_id (e.g. edits made
    # before this feature shipped), we can locate the most recent edit by
    # session_id within the last hour.
    session_id: str | None = None
    rating: str = Field(..., pattern="^(up|down)$")
    comment: str | None = Field(default=None, max_length=2000)


@router.post("/edit-feedback")
async def submit_feedback(
    body: FeedbackRequest,
    user: dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    edit_log_id = body.edit_log_id

    if not edit_log_id and body.session_id:
        # Fallback lookup: latest edit on this session
        result = await db.execute(
            select(EditLog.id)
            .where(EditLog.session_id == body.session_id)
            .order_by(EditLog.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            edit_log_id = str(row)

    if not edit_log_id:
        raise HTTPException(status_code=400, detail="No edit_log_id and no recent edit found for this session.")

    db.add(EditFeedback(
        edit_log_id=edit_log_id,
        user_id=user["user_id"],
        rating=body.rating,
        comment=(body.comment or None),
    ))
    await db.commit()
    return {"ok": True}
