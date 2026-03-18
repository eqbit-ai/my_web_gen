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
                    "deployed_url": s.deployed_url,
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
            "deployed_url": site.deployed_url,
            "cloudfront_domain": site.cloudfront_domain,
            "cloudflare_project_name": site.cloudflare_project_name,
            "status": site.status,
            "is_multipage": site.is_multipage,
            "page_count": site.page_count,
            "session_id": site.session_id,
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
    """Return read-only HTML of a user's site from Redis session."""
    try:
        import json

        result = await db.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        r = await get_redis()
        html = None

        # 1) Try the site's stored session_id
        if site.session_id:
            raw = await r.get(f"session:{site.session_id}")
            if raw:
                session_data = json.loads(raw) if isinstance(raw, str) else raw
                # Multi-page: get index page HTML
                pages = session_data.get("pages")
                if pages and isinstance(pages, dict):
                    index_page = pages.get("index", {})
                    html = index_page.get("html") if isinstance(index_page, dict) else None
                if not html:
                    html = session_data.get("html")

        # 2) Fallback: scan recent sessions for this user
        if not html:
            async for key in r.scan_iter(match="session:*", count=200):
                raw = await r.get(key)
                if not raw:
                    continue
                try:
                    session_data = json.loads(raw) if isinstance(raw, str) else raw
                except (json.JSONDecodeError, TypeError):
                    continue
                if str(session_data.get("user_id")) == str(site.user_id):
                    pages = session_data.get("pages")
                    if pages and isinstance(pages, dict):
                        index_page = pages.get("index", {})
                        html = index_page.get("html") if isinstance(index_page, dict) else None
                    if not html:
                        html = session_data.get("html")
                    break

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


@router.get("/sites/{site_id}/versions")
async def list_site_versions(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List deployment versions for a site from S3 versioning."""
    import os
    from collections import defaultdict

    import boto3

    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    s3_prefix = site.cloudflare_project_name
    if not s3_prefix:
        return {"versions": [], "site_id": site_id}

    bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "meydan-dev-deployed-sites")
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))

    try:
        response = s3.list_object_versions(Bucket=bucket, Prefix=f"{s3_prefix}/")
        versions_raw = response.get("Versions", [])

        # Group by LastModified (rounded to minute = one deployment)
        deployments = defaultdict(list)
        for v in versions_raw:
            ts = v["LastModified"].strftime("%Y-%m-%d %H:%M")
            deployments[ts].append({
                "key": v["Key"],
                "version_id": v["VersionId"],
                "size": v["Size"],
                "is_latest": v.get("IsLatest", False),
            })

        # Sort by timestamp descending
        sorted_deps = sorted(deployments.items(), key=lambda x: x[0], reverse=True)

        result_versions = []
        for i, (ts, files) in enumerate(sorted_deps):
            total_size = sum(f["size"] for f in files)
            is_current = any(f["is_latest"] for f in files)
            result_versions.append({
                "deployment_time": ts,
                "file_count": len(files),
                "total_size": total_size,
                "total_size_kb": round(total_size / 1024, 1),
                "is_current": is_current,
                "version_id": files[0]["version_id"],  # Use first file's version as ref
                "files": files,
            })

        return {"versions": result_versions, "site_id": site_id, "site_name": site.name}

    except Exception as e:
        logger.error("Failed to list versions for site %s: %s", site_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {e}") from e


@router.post("/sites/{site_id}/restore/{deployment_time}")
async def restore_site_version(
    site_id: str,
    deployment_time: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Restore a site to a previous deployment version."""
    import os

    import boto3

    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    s3_prefix = site.cloudflare_project_name
    if not s3_prefix:
        raise HTTPException(status_code=400, detail="Site has no S3 prefix")

    bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "meydan-dev-deployed-sites")
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))

    try:
        response = s3.list_object_versions(Bucket=bucket, Prefix=f"{s3_prefix}/")
        versions_raw = response.get("Versions", [])

        # Find files from the target deployment time
        target_files = [
            v for v in versions_raw
            if v["LastModified"].strftime("%Y-%m-%d %H:%M") == deployment_time
        ]

        if not target_files:
            raise HTTPException(status_code=404, detail="No files found for that deployment time")

        # Copy each versioned file back as the current version
        restored = 0
        for f in target_files:
            copy_source = {"Bucket": bucket, "Key": f["Key"], "VersionId": f["VersionId"]}
            s3.copy_object(Bucket=bucket, CopySource=copy_source, Key=f["Key"])
            restored += 1

        from app.utils.audit_log import log_event_bg
        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="restore_site_version",
            resource_type="site",
            resource_id=str(site_id),
            details={"deployment_time": deployment_time, "files_restored": restored, "site_name": site.name},
        )

        return {
            "success": True,
            "message": f"Restored {restored} files from {deployment_time}",
            "files_restored": restored,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to restore site %s: %s", site_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to restore: {e}") from e
