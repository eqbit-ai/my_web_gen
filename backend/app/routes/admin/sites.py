"""
Admin site management endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_tenant_db
from app.models.project import Project
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
        query = select(Site).where(Site.deleted_at.is_(None))

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
        logger.exception("Failed to fetch site site_id=%s", site_id)
        raise HTTPException(status_code=500, detail="Failed to fetch site") from e


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

        # 3) Fallback: fetch index.html from S3
        if not html and site.cloudflare_project_name:
            try:
                import os

                import boto3

                bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "meydan-dev-deployed-sites")
                s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))
                s3_key = f"{site.cloudflare_project_name}/index.html"
                s3_kwargs = {"Bucket": bucket, "Key": s3_key}
                expected_owner = os.getenv("AWS_ACCOUNT_ID", "")
                if expected_owner:
                    s3_kwargs["ExpectedBucketOwner"] = expected_owner
                obj = s3.get_object(**s3_kwargs)
                html = obj["Body"].read().decode("utf-8")
            except Exception as s3_err:
                logger.warning("S3 preview fallback failed for %s: %s", site_id, s3_err)

        return {
            "site_id": str(site.id),
            "name": site.name,
            "html": html,
            "found_in_cache": html is not None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to preview site site_id=%s", site_id)
        raise HTTPException(status_code=500, detail="Failed to preview site") from e


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
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))

    try:
        expected_owner = os.getenv("AWS_ACCOUNT_ID", "")
        s3_kwargs = {"Bucket": bucket, "Prefix": f"{s3_prefix}/"}
        if expected_owner:
            s3_kwargs["ExpectedBucketOwner"] = expected_owner
        response = s3.list_object_versions(**s3_kwargs)
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
        logger.exception("Failed to list versions for site %s", site_id)
        raise HTTPException(status_code=500, detail="Failed to list versions") from e


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
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))

    try:
        expected_owner = os.getenv("AWS_ACCOUNT_ID", "")
        list_kwargs = {"Bucket": bucket, "Prefix": f"{s3_prefix}/"}
        if expected_owner:
            list_kwargs["ExpectedBucketOwner"] = expected_owner
        response = s3.list_object_versions(**list_kwargs)
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
            copy_kwargs = {"Bucket": bucket, "CopySource": copy_source, "Key": f["Key"]}
            if expected_owner:
                copy_kwargs["ExpectedBucketOwner"] = expected_owner
            s3.copy_object(**copy_kwargs)
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
        logger.exception("Failed to restore site %s", site_id)
        raise HTTPException(status_code=500, detail="Failed to restore site") from e


# ── Deleted Items (Trash) ─────────────────────────────────────────────────


@router.get("/deleted")
async def list_deleted_items(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all soft-deleted sites and projects across all tenants."""
    # Deleted sites
    site_result = await db.execute(
        select(Site).where(Site.deleted_at.isnot(None)).order_by(Site.deleted_at.desc())
    )
    deleted_sites = site_result.scalars().all()

    user_ids = list({s.user_id for s in deleted_sites})
    user_map = {}
    if user_ids:
        user_result = await db.execute(
            select(User.id, User.email, User.full_name, User.company_name, User.db_schema)
            .where(User.id.in_(user_ids))
        )
        user_map = {r[0]: {"email": r[1], "full_name": r[2], "company_name": r[3], "db_schema": r[4]} for r in user_result.fetchall()}

    sites_list = [
        {
            "type": "site",
            "id": str(s.id),
            "name": s.name,
            "user_id": s.user_id,
            "user_email": user_map.get(s.user_id, {}).get("email", ""),
            "user_name": user_map.get(s.user_id, {}).get("full_name", ""),
            "deployed_url": s.deployed_url,
            "deleted_at": _serialize_datetime(s.deleted_at),
            "created_at": _serialize_datetime(s.created_at),
        }
        for s in deleted_sites
    ]

    # Deleted projects — scan all tenant schemas
    all_users = await db.execute(select(User.id, User.email, User.full_name, User.db_schema))
    all_users_list = all_users.fetchall()

    projects_list = []
    for uid, email, full_name, db_schema in all_users_list:
        if not db_schema:
            continue
        try:
            async for tenant_db in get_tenant_db(db_schema):
                result = await tenant_db.execute(
                    select(Project).where(Project.deleted_at.isnot(None)).order_by(Project.deleted_at.desc())
                )
                for p in result.scalars().all():
                    projects_list.append({
                        "type": "project",
                        "id": p.id,
                        "name": p.name,
                        "user_id": uid,
                        "user_email": email,
                        "user_name": full_name,
                        "has_content": bool(p.current_html),
                        "deleted_at": _serialize_datetime(p.deleted_at),
                        "created_at": _serialize_datetime(p.created_at),
                        "db_schema": db_schema,
                    })
        except Exception as e:
            logger.warning("Failed to scan tenant %s for deleted projects: %s", db_schema, e)

    # Merge and sort by deleted_at
    all_items = sites_list + projects_list
    all_items.sort(key=lambda x: x.get("deleted_at") or "", reverse=True)

    return {"items": all_items, "total": len(all_items)}


@router.post("/deleted/restore/site/{site_id}")
async def restore_deleted_site(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted site."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if not site.deleted_at:
        raise HTTPException(status_code=400, detail="Site is not deleted")

    site.deleted_at = None
    site.status = "published"
    await db.commit()

    from app.utils.audit_log import log_event_bg
    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="restore_deleted_site",
        resource_type="site",
        resource_id=str(site_id),
        details={"site_name": site.name},
    )

    return {"success": True, "message": f"Site '{site.name}' restored"}


@router.post("/deleted/restore/project/{project_id}")
async def restore_deleted_project(
    project_id: str,
    db_schema: str = Query(...),
    admin=Depends(require_admin),
):
    """Restore a soft-deleted project."""
    async for tenant_db in get_tenant_db(db_schema):
        result = await tenant_db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if not project.deleted_at:
            raise HTTPException(status_code=400, detail="Project is not deleted")

        project.deleted_at = None
        await tenant_db.commit()

        from app.utils.audit_log import log_event_bg
        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="restore_deleted_project",
            resource_type="project",
            resource_id=project_id,
            details={"project_name": project.name, "db_schema": db_schema},
        )

        return {"success": True, "message": f"Project '{project.name}' restored"}


@router.delete("/deleted/purge/site/{site_id}")
async def purge_deleted_site(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a soft-deleted site and its S3 files."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if not site.deleted_at:
        raise HTTPException(status_code=400, detail="Site is not in trash — soft-delete it first")

    # Delete S3 files
    if site.cloudflare_project_name:
        try:
            from app.utils.s3_deploy import delete_site
            await delete_site(site.cloudflare_project_name)
        except Exception as e:
            logger.warning("Failed to delete S3 files for %s: %s", site.cloudflare_project_name, e)

    await db.delete(site)
    await db.commit()

    from app.utils.audit_log import log_event_bg
    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="purge_deleted_site",
        resource_type="site",
        resource_id=str(site_id),
        details={"site_name": site.name},
    )

    return {"success": True, "message": f"Site '{site.name}' permanently deleted"}
