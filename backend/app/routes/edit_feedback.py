"""
User-facing feedback endpoint for the chat thumbs up / thumbs down on a
completed AI edit. Writes to edit_feedback table joined to edit_logs.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.edit_log import EditFeedback, EditLog
from app.utils.auth import decode_access_token

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


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
        # Most common case: the user thumbs-reacted to the "generation complete"
        # message, which is NOT an edit and has no EditLog row. Treat this as
        # a silent no-op so the UI still shows "thanks for feedback" rather
        # than an error toast. Actual edits always have edit_log_id populated.
        return {"ok": True, "recorded": False, "reason": "no_edit_to_rate"}

    try:
        uid = int(user["user_id"]) if user.get("user_id") is not None else None
    except (ValueError, TypeError):
        uid = None
    db.add(EditFeedback(
        edit_log_id=edit_log_id,
        user_id=uid,
        rating=body.rating,
        comment=(body.comment or None),
    ))
    await db.commit()
    return {"ok": True, "recorded": True}
