"""
Admin domain management endpoints.

Connected domains are stored on the Site model (Site.domain, Site.domain_status, etc.).
This module queries sites that have a domain connected.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.site import Site
from app.models.user import User

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Domains"])


@router.get("/domains")
async def list_domains(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    tld: str | None = Query(default=None),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all sites with connected domains."""
    try:
        query = select(Site).where(Site.domain.isnot(None), Site.domain != "")

        if status:
            query = query.where(Site.domain_status == status)
        if user_id:
            query = query.where(Site.user_id == user_id)
        if tld:
            query = query.where(Site.domain.endswith(tld))

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(Site.created_at.desc()).limit(limit).offset(offset)
        )
        sites = result.scalars().all()

        user_ids = list({s.user_id for s in sites})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        return {
            "domains": [
                {
                    "id": str(s.id),
                    "user_id": s.user_id,
                    "user_email": user_map.get(s.user_id, ""),
                    "domain": s.domain,
                    "site_name": s.name,
                    "status": s.domain_status or s.status,
                    "ssl_status": "active" if s.acm_certificate_arn else "none",
                    "cloudfront_domain": s.cloudfront_domain,
                    "route53_zone_id": s.route53_zone_id,
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
        logger.warning("Failed to list domains: %s", e)
        return {"domains": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.get("/domains/health")
async def domains_health(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate domain health stats from sites with connected domains."""
    try:
        base = select(Site).where(Site.domain.isnot(None), Site.domain != "")
        total_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = total_result.scalar() or 0

        status_result = await db.execute(
            select(Site.domain_status, func.count(Site.id))
            .where(Site.domain.isnot(None), Site.domain != "")
            .group_by(Site.domain_status)
        )
        status_stats = {(r[0] or "unknown"): r[1] for r in status_result.fetchall()}

        with_ssl = await db.execute(
            select(func.count())
            .select_from(Site)
            .where(Site.domain.isnot(None), Site.domain != "", Site.acm_certificate_arn.isnot(None))
        )
        ssl_count = with_ssl.scalar() or 0

        return {
            "total_domains": total,
            "domain_status": status_stats,
            "ssl_active": ssl_count,
            "ssl_none": total - ssl_count,
        }
    except Exception as e:
        logger.warning("Failed to fetch domain health: %s", e)
        return {"error": str(e)}


@router.get("/domains/{site_id}")
async def get_domain_detail(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get domain details for a specific site."""
    try:
        result = await db.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        user_result = await db.execute(
            select(User.email, User.full_name, User.company_name)
            .where(User.id == site.user_id)
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
            "domain": site.domain,
            "site_name": site.name,
            "status": site.domain_status or site.status,
            "ssl_status": "active" if site.acm_certificate_arn else "none",
            "cloudfront_domain": site.cloudfront_domain,
            "cloudfront_distribution_id": site.cloudfront_distribution_id,
            "acm_certificate_arn": site.acm_certificate_arn,
            "route53_zone_id": site.route53_zone_id,
            "dns_records": site.dns_records,
            "deployed_url": site.deployed_url,
            "created_at": _serialize_datetime(site.created_at),
            "updated_at": _serialize_datetime(site.updated_at),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch domain: {e}") from e
