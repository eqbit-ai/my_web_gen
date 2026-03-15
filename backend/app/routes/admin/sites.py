"""
Admin site management endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.site import Site
from app.models.user import User
from app.utils.redis_client import get_redis

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Sites"])


@router.get("/sites")
async def list_sites(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all sites with pagination and optional filters."""
    try:
        query = select(Site)

        if status:
            query = query.where(Site.status == status)
        if user_id:
            query = query.where(Site.user_id == user_id)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(Site.created_at.desc()).limit(limit).offset(offset)
        )
        sites = result.scalars().all()

        # Fetch user emails for display
        user_ids = list({s.user_id for s in sites})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        return {
            "sites": [
                {
                    "id": str(s.id),
                    "user_id": s.user_id,
                    "user_email": user_map.get(s.user_id, ""),
                    "name": s.name,
                    "domain": s.domain,
                    "status": s.status,
                    "is_multipage": s.is_multipage,
                    "page_count": s.page_count,
                    "last_deployed_at": _serialize_datetime(s.last_deployed_at),
                    "created_at": _serialize_datetime(s.created_at),
                    "updated_at": _serialize_datetime(s.updated_at),
                }
                for s in sites
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list sites: %s", e)
        return {"sites": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.get("/sites/{site_id}")
async def get_site_detail(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info for a specific site."""
    try:
        result = await db.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        # Get owner info
        user_result = await db.execute(
            select(User.email, User.full_name, User.company_name).where(User.id == site.user_id)
        )
        user_info = user_result.first()

        return {
            "id": str(site.id),
            "user_id": site.user_id,
            "owner": {
                "email": user_info[0] if user_info else "",
                "full_name": user_info[1] if user_info else "",
                "company_name": user_info[2] if user_info else "",
            } if user_info else None,
            "name": site.name,
            "domain": site.domain,
            "status": site.status,
            "is_multipage": site.is_multipage,
            "page_count": site.page_count,
            "last_deployed_at": _serialize_datetime(site.last_deployed_at),
            "created_at": _serialize_datetime(site.created_at),
            "updated_at": _serialize_datetime(site.updated_at),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch site: {e}") from e


@router.get("/sites/{site_id}/preview")
async def preview_site(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return read-only HTML of a user's site from Redis session or DB."""
    try:
        # Try Redis session first
        r = await get_redis()
        result = await db.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        # Try to find session data in Redis
        html = None
        async for key in r.scan_iter(match="session:*", count=200):
            session_data = await r.hgetall(key)
            if session_data.get("site_id") == str(site_id):
                html = session_data.get("html")
                break

        if not html:
            # Fallback: check if there's a session keyed by user
            session_key = f"session:{site.user_id}"
            session_data = await r.hgetall(session_key)
            html = session_data.get("html") if session_data else None

        return {
            "site_id": str(site.id),
            "name": site.name,
            "html": html,
            "found_in_cache": html is not None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview site: {e}") from e


@router.post("/sites/{site_id}/rebuild")
async def rebuild_site(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a force rebuild of a site (placeholder for future implementation)."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Placeholder: actual rebuild logic will be implemented with deployment pipeline
    from app.utils.audit_log import log_event_bg

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="force_rebuild_site",
        resource_type="site",
        resource_id=str(site_id),
        details={"site_name": site.name},
    )

    return {
        "message": f"Rebuild queued for site '{site.name}'",
        "site_id": str(site.id),
        "status": "queued",
    }
