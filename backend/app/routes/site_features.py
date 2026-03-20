"""
Site features — ZIP export, custom code injection, and page view tracking.

Endpoints:
  GET  /api/sites/{site_id}/export       — Download site as ZIP
  PUT  /api/sites/{site_id}/custom-code  — Save custom head/body code
  GET  /api/sites/{site_id}/custom-code  — Get custom head/body code
  POST /api/sites/track/{site_id}        — Record a page view (public, no auth)
  GET  /api/sites/{site_id}/analytics    — Get page view analytics (auth)
"""

import io
import logging
import zipfile
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import func, select

from app.database import async_session
from app.models.page_view import PageView
from app.models.site import Site
from app.utils.auth import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ═══════════════════════════════════════════════════════════════════════
# FEATURE 1: ZIP EXPORT
# ═══════════════════════════════════════════════════════════════════════


@router.get("/{site_id}/export")
async def export_site_zip(site_id: str, user: dict = Depends(require_auth)):
    """Download a deployed site as a ZIP file containing all HTML/CSS/JS files."""
    import os

    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        if not site.cloudflare_project_name:
            raise HTTPException(status_code=400, detail="Site has no deployment to export")

    # Download files from S3
    bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "")
    region = os.getenv("AWS_REGION", "me-central-1")
    if not bucket:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        region_name=region,
    )

    prefix = site.cloudflare_project_name
    aws_account_id = os.getenv("AWS_ACCOUNT_ID", "")
    try:
        list_kwargs = {"Bucket": bucket, "Prefix": f"{prefix}/"}
        if aws_account_id:
            list_kwargs["ExpectedBucketOwner"] = aws_account_id
        response = s3.list_objects_v2(**list_kwargs)
        objects = response.get("Contents", [])
    except ClientError as e:
        raise HTTPException(status_code=502, detail=f"Failed to list S3 files: {e}") from e

    if not objects:
        raise HTTPException(status_code=404, detail="No files found for this site")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    site_name = site.name or prefix

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for obj in objects:
            key = obj["Key"]
            # Strip prefix to get relative path: "my-site/index.html" → "index.html"
            relative_path = key[len(prefix):].lstrip("/")
            if not relative_path:
                continue

            try:
                get_kwargs = {"Bucket": bucket, "Key": key}
                if aws_account_id:
                    get_kwargs["ExpectedBucketOwner"] = aws_account_id
                file_obj = s3.get_object(**get_kwargs)
                file_content = file_obj["Body"].read()
                zf.writestr(relative_path, file_content)
            except ClientError:
                logger.warning("Failed to download %s from S3", key)
                continue

    zip_buffer.seek(0)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in site_name)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.zip"'},
    )


# ═══════════════════════════════════════════════════════════════════════
# FEATURE 2: CUSTOM CODE INJECTION
# ═══════════════════════════════════════════════════════════════════════


class CustomCodeRequest(BaseModel):
    head_code: str = ""  # HTML/JS for <head>
    body_code: str = ""  # HTML/JS for before </body>


@router.get("/{site_id}/custom-code")
async def get_custom_code(site_id: str, user: dict = Depends(require_auth)):
    """Get custom code for a site."""
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

    return {
        "head_code": site.custom_head_code or "",
        "body_code": site.custom_body_code or "",
    }


@router.put("/{site_id}/custom-code")
async def update_custom_code(site_id: str, req: CustomCodeRequest, user: dict = Depends(require_auth)):
    """Save custom head/body code for a site. Takes effect on next deploy."""
    # Basic size limit
    if len(req.head_code) > 50000 or len(req.body_code) > 50000:
        raise HTTPException(status_code=400, detail="Custom code too large (max 50KB each)")

    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        site.custom_head_code = req.head_code.strip() or None
        site.custom_body_code = req.body_code.strip() or None
        await db.commit()

    return {"success": True, "message": "Custom code saved. Redeploy to apply."}


# ═══════════════════════════════════════════════════════════════════════
# FEATURE 3: PAGE VIEW TRACKING
# ═══════════════════════════════════════════════════════════════════════


@router.post("/track/{site_id}")
async def track_page_view(site_id: str, request: Request):
    """Record a page view. Public endpoint (no auth) — called by tracking script on deployed sites."""
    # Parse body (optional — tracking pixel can be GET-based too)
    path = "/"
    referrer = None
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            path = body.get("path", "/")
            referrer = body.get("referrer", "")
        else:
            # Query params fallback (for pixel tracking)
            path = request.query_params.get("p", "/")
            referrer = request.query_params.get("r", "")
    except Exception:
        pass

    ip = _get_client_ip(request)
    ua = str(request.headers.get("user-agent", ""))[:500]

    # Verify site exists (lightweight check)
    async with async_session() as db:
        result = await db.execute(select(Site.id).where(Site.id == site_id))
        if not result.scalar_one_or_none():
            return {"ok": True}  # Silent — don't reveal site existence

        # Record view
        view = PageView(
            site_id=site_id,
            path=path[:500] if path else "/",
            referrer=referrer[:1000] if referrer else None,
            ip_address=ip,
            user_agent=ua,
        )
        db.add(view)

        # Increment site view counter
        await db.execute(
            Site.__table__.update()
            .where(Site.id == site_id)
            .values(view_count=Site.view_count + 1)
        )
        await db.commit()

    return {"ok": True}


# Also support GET for tracking pixel
@router.get("/track/{site_id}")
async def track_page_view_pixel(site_id: str, request: Request):
    """1x1 pixel tracking endpoint (GET-based for <img> tags)."""
    await track_page_view(site_id, request)
    # Return 1x1 transparent GIF
    pixel = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    return StreamingResponse(
        io.BytesIO(pixel),
        media_type="image/gif",
        headers={"Cache-Control": "no-store, no-cache", "Pragma": "no-cache"},
    )


@router.get("/{site_id}/analytics")
async def get_site_analytics(
    site_id: str,
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth),
):
    """Get page view analytics for a site."""
    async with async_session() as db:
        # Verify ownership
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Total views
        total_q = await db.execute(
            select(func.count()).where(
                PageView.site_id == site_id,
                PageView.viewed_at >= since,
            )
        )
        total_views = total_q.scalar() or 0

        # Unique visitors (by IP)
        unique_q = await db.execute(
            select(func.count(func.distinct(PageView.ip_address))).where(
                PageView.site_id == site_id,
                PageView.viewed_at >= since,
            )
        )
        unique_visitors = unique_q.scalar() or 0

        # Views per day
        daily_q = await db.execute(
            select(
                func.date_trunc("day", PageView.viewed_at).label("day"),
                func.count().label("views"),
            )
            .where(PageView.site_id == site_id, PageView.viewed_at >= since)
            .group_by("day")
            .order_by("day")
        )
        daily = [{"date": row.day.isoformat()[:10], "views": row.views} for row in daily_q.all()]

        # Top pages
        pages_q = await db.execute(
            select(PageView.path, func.count().label("views"))
            .where(PageView.site_id == site_id, PageView.viewed_at >= since)
            .group_by(PageView.path)
            .order_by(func.count().desc())
            .limit(10)
        )
        top_pages = [{"path": row.path, "views": row.views} for row in pages_q.all()]

        # Top referrers
        ref_q = await db.execute(
            select(PageView.referrer, func.count().label("views"))
            .where(
                PageView.site_id == site_id,
                PageView.viewed_at >= since,
                PageView.referrer.isnot(None),
                PageView.referrer != "",
            )
            .group_by(PageView.referrer)
            .order_by(func.count().desc())
            .limit(10)
        )
        top_referrers = [{"referrer": row.referrer, "views": row.views} for row in ref_q.all()]

    return {
        "site_id": site_id,
        "site_name": site.name,
        "period_days": days,
        "total_views": total_views,
        "unique_visitors": unique_visitors,
        "all_time_views": site.view_count,
        "daily": daily,
        "top_pages": top_pages,
        "top_referrers": top_referrers,
    }
