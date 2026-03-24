"""
Form submission routes — public endpoint for website visitors + authenticated inbox for site owners.

Public:  POST /submit/{site_id}  — receives contact form submissions (no auth)
Private: GET  /submissions       — list submissions for user's sites
         GET  /unread-count      — badge count
         PATCH /submissions/{id}/read — mark as read
         DELETE /submissions/{id}     — delete submission
"""

import html as html_lib
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import func, select

from app.database import async_session
from app.models.form_submission import FormSubmission
from app.models.site import Site
from app.utils.auth import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# ── Helpers ─────────────────────────────────────────────────────────────

THANK_YOU_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thank You</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#f8f9fa;padding:20px}
.card{text-align:center;padding:3rem 2rem;border-radius:16px;background:#fff;box-shadow:0 4px 24px rgba(0,0,0,.08);max-width:420px;width:100%}
.icon{width:64px;height:64px;margin:0 auto 1rem;border-radius:50%;background:#ecfdf5;display:flex;align-items:center;justify-content:center}
.icon svg{color:#10b981}
h1{font-size:1.5rem;color:#111827;margin-bottom:.5rem}
p{color:#6b7280;font-size:.9375rem;line-height:1.6}
a{color:#3b82f6;text-decoration:none;font-weight:500}
a:hover{text-decoration:underline}
.back{margin-top:1.5rem}
</style></head>
<body><div class="card">
<div class="icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div>
<h1>Thank You!</h1>
<p>Your message has been received.<br>We'll get back to you soon.</p>
<p class="back"><a href="javascript:history.back()">← Go back</a></p>
</div></body></html>"""

HONEYPOT_FIELDS = {"_hp", "website", "url", "fax"}
MAX_FORM_SIZE = 10_000  # 10KB


def _strip_html(text: str) -> str:
    """Strip HTML tags from submitted text to prevent stored XSS."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    return html_lib.escape(re.sub(r"<[^>]+>", "", text)).strip()


def _sanitize_fields(fields: dict) -> dict:
    """Clean all field values."""
    clean = {}
    for key, value in fields.items():
        k = _strip_html(str(key))[:100]
        if isinstance(value, str):
            clean[k] = _strip_html(value)[:5000]
        elif isinstance(value, (int, float, bool)):
            clean[k] = value
        elif isinstance(value, list):
            clean[k] = [_strip_html(str(v))[:1000] for v in value[:20]]
        else:
            clean[k] = _strip_html(str(value))[:1000]
    return clean


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


# ── Public Submission Endpoint ──────────────────────────────────────────


@router.options("/submit/{site_id}")
async def submit_form_preflight(site_id: str, request: Request):
    """Handle CORS preflight for form submissions from deployed sites."""
    from fastapi.responses import Response
    origin = request.headers.get("origin", "*")
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "86400",
        },
    )


@router.post("/submit/{site_id}", response_class=HTMLResponse)
async def submit_form(site_id: str, request: Request):
    """Receive a contact form submission from a deployed website.

    Accepts both application/json and application/x-www-form-urlencoded.
    Returns an HTML "thank you" page (for traditional form POST).
    """
    # Parse form data
    content_type = request.headers.get("content-type", "")
    try:
        if "application/json" in content_type:
            fields = await request.json()
        else:
            form = await request.form()
            fields = dict(form)
    except Exception:
        return HTMLResponse(THANK_YOU_HTML, status_code=200)

    if not isinstance(fields, dict) or not fields:
        return HTMLResponse(THANK_YOU_HTML, status_code=200)

    # Check total size
    raw_size = sum(len(str(v)) for v in fields.values())
    if raw_size > MAX_FORM_SIZE:
        return HTMLResponse(THANK_YOU_HTML, status_code=200)

    # Honeypot check — silently accept but don't store
    for hp_field in HONEYPOT_FIELDS:
        if fields.get(hp_field):
            logger.debug("Honeypot triggered for site %s", site_id)
            return HTMLResponse(THANK_YOU_HTML, status_code=200)

    # Sanitize
    source_page = _strip_html(str(fields.pop("_page", "")))[:255] or None
    # Remove internal fields
    for internal in ("_hp", "_page", "_token"):
        fields.pop(internal, None)

    fields = _sanitize_fields(fields)

    # Must have at least one meaningful field
    meaningful = any(
        fields.get(f) for f in ("name", "email", "message", "phone", "subject")
    )
    if not meaningful and len(fields) < 2:
        return HTMLResponse(THANK_YOU_HTML, status_code=200)

    # Verify site exists and is published
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.status == "published")
        )
        site = result.scalar_one_or_none()
        if not site:
            return HTMLResponse(THANK_YOU_HTML, status_code=200)

        submission = FormSubmission(
            site_id=site.id,
            fields=fields,
            ip_address=_get_client_ip(request),
            user_agent=str(request.headers.get("user-agent", ""))[:500],
            source_page=source_page,
        )
        db.add(submission)
        await db.commit()

        # Send email notification to site owner (fire-and-forget)
        try:
            from app.models.user import User
            from app.utils.email import send_form_notification

            owner_result = await db.execute(select(User).where(User.id == site.user_id))
            owner = owner_result.scalar_one_or_none()
            if owner and owner.email:
                send_form_notification(owner.email, site.name or "Your Website", fields, source_page)
        except Exception as e:
            logger.warning(f"[FORMS] Failed to send notification email: {e}")

    logger.info("Form submission received")

    # CORS headers for cross-origin form submissions from deployed S3 sites
    origin = request.headers.get("origin", "*")
    cors_headers = {"Access-Control-Allow-Origin": origin}

    # Return JSON if client prefers it (AJAX), otherwise HTML
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        from fastapi.responses import JSONResponse
        return JSONResponse({"success": True, "message": "Submission received"}, headers=cors_headers)

    return HTMLResponse(THANK_YOU_HTML, status_code=200, headers=cors_headers)


# ── Authenticated Inbox Endpoints ───────────────────────────────────────


@router.get("/submissions")
async def list_submissions(
    site_id: str | None = Query(None),
    is_read: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(require_auth),
):
    """List form submissions for the current user's sites."""
    async with async_session() as db:
        # Base query — join to verify ownership (IDOR protection)
        base = (
            select(FormSubmission)
            .join(Site, FormSubmission.site_id == Site.id)
            .where(Site.user_id == user["user_id"])
        )

        if site_id:
            base = base.where(FormSubmission.site_id == site_id)
        if is_read is not None:
            base = base.where(FormSubmission.is_read == is_read)

        # Total count
        count_q = select(func.count()).select_from(base.subquery())
        total = (await db.execute(count_q)).scalar() or 0

        # Unread count (across all user's sites)
        unread_q = (
            select(func.count())
            .select_from(
                select(FormSubmission.id)
                .join(Site, FormSubmission.site_id == Site.id)
                .where(Site.user_id == user["user_id"], FormSubmission.is_read == False)  # noqa: E712
                .subquery()
            )
        )
        unread_count = (await db.execute(unread_q)).scalar() or 0

        # Fetch submissions with site name
        query = (
            select(FormSubmission, Site.name.label("site_name"))
            .join(Site, FormSubmission.site_id == Site.id)
            .where(Site.user_id == user["user_id"])
        )
        if site_id:
            query = query.where(FormSubmission.site_id == site_id)
        if is_read is not None:
            query = query.where(FormSubmission.is_read == is_read)

        query = query.order_by(FormSubmission.submitted_at.desc()).limit(limit).offset(offset)
        rows = (await db.execute(query)).all()

    submissions = []
    for sub, site_name in rows:
        submissions.append({
            "id": str(sub.id),
            "site_id": str(sub.site_id),
            "site_name": site_name,
            "fields": sub.fields,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
            "is_read": sub.is_read,
            "ip_address": sub.ip_address,
            "source_page": sub.source_page,
        })

    return {
        "submissions": submissions,
        "total": total,
        "unread_count": unread_count,
    }


@router.get("/unread-count")
async def unread_count(user: dict = Depends(require_auth)):
    """Get unread submission count for badge display."""
    async with async_session() as db:
        q = (
            select(func.count())
            .select_from(
                select(FormSubmission.id)
                .join(Site, FormSubmission.site_id == Site.id)
                .where(Site.user_id == user["user_id"], FormSubmission.is_read == False)  # noqa: E712
                .subquery()
            )
        )
        count = (await db.execute(q)).scalar() or 0
    return {"unread_count": count}


class MarkReadRequest(BaseModel):
    is_read: bool = True


@router.patch("/submissions/{submission_id}/read")
async def mark_submission_read(submission_id: str, user: dict = Depends(require_auth)):
    """Mark a submission as read."""
    async with async_session() as db:
        result = await db.execute(
            select(FormSubmission)
            .join(Site, FormSubmission.site_id == Site.id)
            .where(FormSubmission.id == submission_id, Site.user_id == user["user_id"])
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise HTTPException(status_code=404, detail="Submission not found")

        sub.is_read = True
        await db.commit()
    return {"success": True}


@router.delete("/submissions/{submission_id}")
async def delete_submission(submission_id: str, user: dict = Depends(require_auth)):
    """Delete a submission."""
    async with async_session() as db:
        result = await db.execute(
            select(FormSubmission)
            .join(Site, FormSubmission.site_id == Site.id)
            .where(FormSubmission.id == submission_id, Site.user_id == user["user_id"])
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise HTTPException(status_code=404, detail="Submission not found")

        await db.delete(sub)
        await db.commit()
    return {"success": True}
