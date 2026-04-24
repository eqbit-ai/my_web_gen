"""
Admin domain management endpoints.

External domains: user-owned domains pointed via nameservers (stored on Site model).
Internal domains: domains purchased through the platform (stored in Domain model/table).
Admin-only: full control, cross-user visibility, bulk ops, health checks.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.domain import Domain
from app.models.site import Site
from app.models.user import User
from app.utils.audit_log import log_event_bg
from app.utils.openprovider import (
    OpenProviderError,
)
from app.utils.openprovider import (
    renew_domain as op_renew_domain,
)
from app.utils.openprovider import (
    sync_domain_status as op_sync_domain_status,
)
from app.utils.openprovider import (
    update_contact as op_update_contact,
)
from app.utils.openprovider import (
    update_nameservers as op_update_nameservers,
)
from app.utils.route53 import get_nameservers as r53_get_nameservers

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Domains"])


# ── Schemas ──────────────────────────────────────────────────────────


class AdminDomainStatusUpdate(BaseModel):
    status: str  # active, suspended, pending, expired


class AdminTransferOwnership(BaseModel):
    new_user_id: int


class AdminOverrideNameservers(BaseModel):
    nameservers: list[str]


class AdminOverrideContact(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None


class AdminForceRenew(BaseModel):
    period: int = 1


class AdminBulkAction(BaseModel):
    domain_ids: list[str]
    action: str  # suspend, reactivate, force_renew, sync


# ── Helper ───────────────────────────────────────────────────────────


def _split_domain(domain_name: str) -> tuple[str, str]:
    parts = domain_name.rsplit(".", 1)
    return parts[0], parts[1]


def _serialize_domain(d: Domain, user_email: str = "") -> dict:
    return {
        "id": str(d.id),
        "user_id": d.user_id,
        "user_email": user_email,
        "domain_name": d.domain_name,
        "tld": d.tld,
        "registrar": d.registrar,
        "status": d.status,
        "dns_status": d.dns_status,
        "ssl_status": d.ssl_status,
        "ssl_expires_at": _serialize_datetime(d.ssl_expires_at),
        "verification_status": d.verification_status,
        "auto_renew": d.auto_renew,
        "transfer_locked": d.transfer_locked,
        "whois_privacy": d.whois_privacy,
        "nameservers": d.nameservers,
        "route53_zone_id": d.route53_zone_id,
        "contact_handle": d.contact_handle,
        "transfer_requested_at": _serialize_datetime(d.transfer_requested_at),
        "transfer_reason": d.transfer_reason,
        "site_id": str(d.site_id) if d.site_id else None,
        "registered_at": _serialize_datetime(d.registered_at),
        "expires_at": _serialize_datetime(d.expires_at),
        "created_at": _serialize_datetime(d.created_at),
        "updated_at": _serialize_datetime(d.updated_at),
    }


# ═════════════════════════════════════════════════════════════════════
# External Domains (user-owned, pointed via nameservers — Site model)
# ═════════════════════════════════════════════════════════════════════


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
    """List all sites with external (user-pointed) domains.

    Excludes domains that are also registered internally (shown in Internal Domains instead).
    """
    try:
        # Get internally registered domain names to exclude
        internal_result = await db.execute(select(Domain.domain_name))
        internal_names = {r[0] for r in internal_result.fetchall()}

        query = select(Site).where(
            Site.domain.isnot(None),
            Site.domain != "",
            Site.domain.notin_(internal_names) if internal_names else True,
        )

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
    """Aggregate health stats for external domains (excludes internally registered)."""
    try:
        # Exclude internally registered domains
        internal_result = await db.execute(select(Domain.domain_name))
        internal_names = {r[0] for r in internal_result.fetchall()}

        ext_filter = [Site.domain.isnot(None), Site.domain != ""]
        if internal_names:
            ext_filter.append(Site.domain.notin_(internal_names))

        base = select(Site).where(*ext_filter)
        total_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = total_result.scalar() or 0

        status_result = await db.execute(
            select(Site.domain_status, func.count(Site.id))
            .where(*ext_filter)
            .group_by(Site.domain_status)
        )
        status_stats = {(r[0] or "unknown"): r[1] for r in status_result.fetchall()}

        with_ssl = await db.execute(
            select(func.count())
            .select_from(Site)
            .where(*ext_filter, Site.acm_certificate_arn.isnot(None))
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


# ═════════════════════════════════════════════════════════════════════
# Internal Domains (purchased through platform — Domain model)
# ═════════════════════════════════════════════════════════════════════


@router.get("/domains/internal")
async def list_internal_domains(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, description="Search domain name"),
    status: str | None = Query(default=None),
    verification: str | None = Query(default=None),
    tld: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all domains registered through the platform with search and filters."""
    try:
        query = select(Domain)

        if q:
            query = query.where(Domain.domain_name.ilike(f"%{q}%"))
        if status:
            query = query.where(Domain.status == status)
        if verification:
            query = query.where(Domain.verification_status == verification)
        if tld:
            query = query.where(Domain.tld == tld)
        if user_id:
            query = query.where(Domain.user_id == user_id)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(Domain.created_at.desc()).limit(limit).offset(offset)
        )
        domains = result.scalars().all()

        user_ids = list({d.user_id for d in domains})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        return {
            "domains": [_serialize_domain(d, user_map.get(d.user_id, "")) for d in domains],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list internal domains: %s", e)
        return {"domains": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.get("/domains/internal/health")
async def internal_domains_health(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate stats for internally registered domains."""
    try:
        total_result = await db.execute(select(func.count()).select_from(Domain))
        total = total_result.scalar() or 0

        status_result = await db.execute(
            select(Domain.status, func.count(Domain.id)).group_by(Domain.status)
        )
        status_stats = {(r[0] or "unknown"): r[1] for r in status_result.fetchall()}

        verification_result = await db.execute(
            select(Domain.verification_status, func.count(Domain.id))
            .group_by(Domain.verification_status)
        )
        verification_stats = {(r[0] or "unknown"): r[1] for r in verification_result.fetchall()}

        ssl_result = await db.execute(
            select(Domain.ssl_status, func.count(Domain.id)).group_by(Domain.ssl_status)
        )
        ssl_stats = {(r[0] or "unknown"): r[1] for r in ssl_result.fetchall()}

        # Auto-renew stats
        renew_result = await db.execute(
            select(Domain.auto_renew, func.count(Domain.id)).group_by(Domain.auto_renew)
        )
        renew_stats = {("enabled" if r[0] else "disabled"): r[1] for r in renew_result.fetchall()}

        return {
            "total_domains": total,
            "domain_status": status_stats,
            "verification_status": verification_stats,
            "ssl_status": ssl_stats,
            "auto_renew": renew_stats,
        }
    except Exception as e:
        logger.warning("Failed to fetch internal domain health: %s", e)
        return {"error": str(e)}


# ── Expiring Domains Report ──────────────────────────────────────────


@router.get("/domains/internal/expiring")
async def expiring_domains(
    days: int = Query(default=30, ge=1, le=365),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Report domains expiring within N days, grouped by urgency."""
    try:
        now = datetime.now(UTC)
        cutoff = now + timedelta(days=days)

        result = await db.execute(
            select(Domain)
            .where(Domain.expires_at.isnot(None), Domain.expires_at <= cutoff)
            .order_by(Domain.expires_at.asc())
        )
        domains = result.scalars().all()

        user_ids = list({d.user_id for d in domains})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        expired = []
        critical = []  # < 7 days
        warning = []   # < 30 days
        upcoming = []  # < N days

        for d in domains:
            entry = _serialize_domain(d, user_map.get(d.user_id, ""))
            days_left = (d.expires_at - now).days if d.expires_at else 0
            entry["days_until_expiry"] = days_left

            if days_left < 0:
                expired.append(entry)
            elif days_left < 7:
                critical.append(entry)
            elif days_left < 30:
                warning.append(entry)
            else:
                upcoming.append(entry)

        return {
            "total": len(domains),
            "expired": {"count": len(expired), "domains": expired},
            "critical": {"count": len(critical), "domains": critical},
            "warning": {"count": len(warning), "domains": warning},
            "upcoming": {"count": len(upcoming), "domains": upcoming},
        }
    except Exception as e:
        logger.warning("Failed to fetch expiring domains: %s", e)
        return {"error": str(e)}


# ── Transfer Requests ────────────────────────────────────────────────


@router.get("/domains/internal/transfer-requests")
async def list_transfer_requests(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all domains with pending transfer requests."""
    try:
        result = await db.execute(
            select(Domain)
            .where(Domain.transfer_requested_at.isnot(None))
            .order_by(Domain.transfer_requested_at.desc())
        )
        domains = result.scalars().all()

        user_ids = list({d.user_id for d in domains})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        return {
            "total": len(domains),
            "requests": [
                {
                    **_serialize_domain(d, user_map.get(d.user_id, "")),
                    "transfer_reason": d.transfer_reason,
                    "transfer_requested_at": _serialize_datetime(d.transfer_requested_at),
                }
                for d in domains
            ],
        }
    except Exception as e:
        logger.warning("Failed to fetch transfer requests: %s", e)
        return {"error": str(e)}


@router.delete("/domains/internal/{domain_id}/transfer-request")
async def admin_clear_transfer_request(
    domain_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: clear/resolve a transfer request after processing."""
    try:
        result = await db.execute(select(Domain).where(Domain.id == domain_id))
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        await db.execute(
            update(Domain).where(Domain.id == domain.id).values(
                transfer_requested_at=None,
                transfer_reason=None,
            )
        )
        await db.commit()

        log_event_bg(
            user_id="admin",
            action="admin_clear_transfer_request",
            resource_type="domain",
            resource_id=domain_id,
            details={"domain": domain.domain_name},
        )

        return {"success": True, "message": f"Transfer request cleared for {domain.domain_name}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to clear transfer request domain_id=%s", domain_id)
        raise HTTPException(status_code=500, detail="Failed to clear transfer request") from e


# ── DNS Health Check ─────────────────────────────────────────────────


@router.get("/domains/internal/dns-health")
async def dns_health_check(
    limit: int = Query(default=50, ge=1, le=200),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Check DNS health: compare registered NS at OpenProvider vs expected Route53 NS."""
    try:
        result = await db.execute(
            select(Domain)
            .where(Domain.route53_zone_id.isnot(None), Domain.status == "active")
            .limit(limit)
        )
        domains = result.scalars().all()

        healthy = 0
        mismatched = 0
        errors = 0
        details = []

        for d in domains:
            try:
                expected_ns = await r53_get_nameservers(d.route53_zone_id)
                registered_ns = d.nameservers or []

                expected_set = set(n.rstrip(".").lower() for n in expected_ns)
                registered_set = set(n.rstrip(".").lower() for n in registered_ns)

                if expected_set == registered_set:
                    healthy += 1
                    status = "healthy"
                else:
                    mismatched += 1
                    status = "mismatched"

                details.append({
                    "domain": d.domain_name,
                    "status": status,
                    "expected_ns": list(expected_set),
                    "registered_ns": list(registered_set),
                })
            except Exception as e:
                errors += 1
                details.append({
                    "domain": d.domain_name,
                    "status": "error",
                    "error": str(e),
                })

        no_zone_count = await db.execute(
            select(func.count()).select_from(
                select(Domain).where(Domain.route53_zone_id.is_(None), Domain.status == "active").subquery()
            )
        )

        return {
            "healthy": healthy,
            "mismatched": mismatched,
            "errors": errors,
            "no_zone": no_zone_count.scalar() or 0,
            "details": details,
        }
    except Exception as e:
        logger.warning("Failed DNS health check: %s", e)
        return {"error": str(e)}


# ── Domain Detail (with full info) ───────────────────────────────────


@router.get("/domains/internal/{domain_id}")
async def get_internal_domain_detail(
    domain_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get full details for a specific domain."""
    try:
        result = await db.execute(select(Domain).where(Domain.id == domain_id))
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        user_result = await db.execute(
            select(User.email, User.full_name, User.company_name)
            .where(User.id == domain.user_id)
        )
        user_info = user_result.first()

        site_info = None
        if domain.site_id:
            site_result = await db.execute(
                select(Site.name, Site.deployed_url, Site.status)
                .where(Site.id == domain.site_id)
            )
            site_row = site_result.first()
            if site_row:
                site_info = {
                    "id": str(domain.site_id),
                    "name": site_row[0],
                    "deployed_url": site_row[1],
                    "status": site_row[2],
                }

        return {
            **_serialize_domain(domain),
            "owner": {
                "email": user_info[0] if user_info else "",
                "full_name": user_info[1] if user_info else "",
                "company_name": user_info[2] if user_info else "",
            } if user_info else None,
            "site": site_info,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch domain domain_id=%s", domain_id)
        raise HTTPException(status_code=500, detail="Failed to fetch domain") from e


# ── Live Sync from Registrar ─────────────────────────────────────────


@router.post("/domains/internal/{domain_id}/sync")
async def admin_sync_domain(
    domain_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pull live status from OpenProvider and update DB. Returns comparison."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    sld, tld = _split_domain(domain.domain_name)

    try:
        live = await op_sync_domain_status(sld, tld)
    except OpenProviderError as e:
        logger.exception("OpenProvider sync failed domain_id=%s", domain_id)
        raise HTTPException(status_code=502, detail="Sync with registrar failed") from e

    updates = {
        "auto_renew": live.get("autorenew", domain.auto_renew),
        "transfer_locked": live.get("is_locked", domain.transfer_locked),
        "whois_privacy": live.get("whois_privacy", domain.whois_privacy),
        "nameservers": live.get("nameservers"),
        "contact_handle": live.get("owner_handle") or domain.contact_handle,
    }
    if live.get("expiration_date"):
        try:
            updates["expires_at"] = datetime.fromisoformat(live["expiration_date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    op_status = live.get("status", "").lower()
    if op_status in ("act", "active"):
        updates["status"] = "active"
    elif op_status in ("exp", "expired"):
        updates["status"] = "expired"

    await db.execute(update(Domain).where(Domain.id == domain.id).values(**updates))
    await db.commit()

    log_event_bg(user_id="admin", action="admin_domain_sync", resource_type="domain",
                 resource_id=domain_id, details={"live": live})

    return {"success": True, "live_status": live, "updated_fields": list(updates.keys())}


# ── Force Renew ──────────────────────────────────────────────────────


@router.post("/domains/internal/{domain_id}/force-renew")
async def admin_force_renew(
    domain_id: str,
    req: AdminForceRenew,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin force-renew a domain."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    sld, tld = _split_domain(domain.domain_name)

    try:
        await op_renew_domain(sld, tld, req.period)
    except OpenProviderError as e:
        logger.exception("OpenProvider renewal failed domain_id=%s", domain_id)
        raise HTTPException(status_code=502, detail="Renewal with registrar failed") from e

    if domain.expires_at:
        new_expiry = domain.expires_at + timedelta(days=365 * req.period)
    else:
        new_expiry = datetime.now(UTC) + timedelta(days=365 * req.period)

    await db.execute(
        update(Domain).where(Domain.id == domain.id).values(expires_at=new_expiry, status="active")
    )
    await db.commit()

    log_event_bg(user_id="admin", action="admin_domain_force_renew", resource_type="domain",
                 resource_id=domain_id, details={"period": req.period, "new_expiry": new_expiry.isoformat()})

    return {"success": True, "new_expires_at": new_expiry.isoformat()}


# ── Update Status (suspend / reactivate) ─────────────────────────────


@router.put("/domains/internal/{domain_id}/status")
async def admin_update_status(
    domain_id: str,
    req: AdminDomainStatusUpdate,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin update domain status (suspend, reactivate, etc.)."""
    valid = {"active", "suspended", "pending", "expired"}
    if req.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    old_status = domain.status
    await db.execute(update(Domain).where(Domain.id == domain.id).values(status=req.status))
    await db.commit()

    log_event_bg(user_id="admin", action="admin_domain_status", resource_type="domain",
                 resource_id=domain_id, details={"old": old_status, "new": req.status})

    return {"success": True, "old_status": old_status, "new_status": req.status}


# ── Transfer Ownership ───────────────────────────────────────────────


@router.post("/domains/internal/{domain_id}/transfer-ownership")
async def admin_transfer_ownership(
    domain_id: str,
    req: AdminTransferOwnership,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Transfer domain ownership to a different user."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Verify target user exists
    user_result = await db.execute(select(User.id).where(User.id == req.new_user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target user not found")

    old_user = domain.user_id
    await db.execute(
        update(Domain).where(Domain.id == domain.id).values(user_id=req.new_user_id)
    )
    await db.commit()

    log_event_bg(user_id="admin", action="admin_domain_transfer", resource_type="domain",
                 resource_id=domain_id, details={"from_user": old_user, "to_user": req.new_user_id})

    return {"success": True, "old_user_id": old_user, "new_user_id": req.new_user_id}


# ── Override Nameservers ─────────────────────────────────────────────


@router.put("/domains/internal/{domain_id}/nameservers")
async def admin_override_nameservers(
    domain_id: str,
    req: AdminOverrideNameservers,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin override: force-update nameservers at OpenProvider."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    sld, tld = _split_domain(domain.domain_name)

    try:
        await op_update_nameservers(sld, tld, req.nameservers)
    except OpenProviderError as e:
        logger.exception("OpenProvider nameserver override failed domain_id=%s", domain_id)
        raise HTTPException(status_code=502, detail="Failed to update nameservers at registrar") from e

    await db.execute(
        update(Domain).where(Domain.id == domain.id).values(nameservers=req.nameservers)
    )
    await db.commit()

    log_event_bg(user_id="admin", action="admin_domain_ns_override", resource_type="domain",
                 resource_id=domain_id, details={"nameservers": req.nameservers})

    return {"success": True, "nameservers": req.nameservers}


# ── Override Contact ─────────────────────────────────────────────────


@router.put("/domains/internal/{domain_id}/contact")
async def admin_override_contact(
    domain_id: str,
    req: AdminOverrideContact,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin override: update contact/WHOIS details."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if not domain.contact_handle:
        raise HTTPException(status_code=400, detail="No contact handle for this domain")

    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        await op_update_contact(domain.contact_handle, **fields)
    except OpenProviderError as e:
        logger.exception("OpenProvider contact override failed domain_id=%s", domain_id)
        raise HTTPException(status_code=502, detail="Failed to update contact at registrar") from e

    log_event_bg(user_id="admin", action="admin_domain_contact_override", resource_type="domain",
                 resource_id=domain_id, details={"fields": list(fields.keys())})

    return {"success": True, "updated_fields": list(fields.keys())}


# ── Bulk Operations ──────────────────────────────────────────────────


@router.post("/domains/internal/bulk")
async def admin_bulk_action(
    req: AdminBulkAction,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Bulk operations: suspend, reactivate, force_renew, sync."""
    valid_actions = {"suspend", "reactivate", "force_renew", "sync"}
    if req.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

    success = []
    failed = []

    for did in req.domain_ids:
        try:
            result = await db.execute(select(Domain).where(Domain.id == did))
            domain = result.scalar_one_or_none()
            if not domain:
                failed.append({"id": did, "error": "Not found"})
                continue

            sld, tld = _split_domain(domain.domain_name)

            if req.action == "suspend":
                await db.execute(update(Domain).where(Domain.id == domain.id).values(status="suspended"))
                success.append(did)

            elif req.action == "reactivate":
                await db.execute(update(Domain).where(Domain.id == domain.id).values(status="active"))
                success.append(did)

            elif req.action == "force_renew":
                await op_renew_domain(sld, tld, 1)
                new_expiry = (domain.expires_at or datetime.now(UTC)) + timedelta(days=365)
                await db.execute(
                    update(Domain).where(Domain.id == domain.id).values(expires_at=new_expiry, status="active")
                )
                success.append(did)

            elif req.action == "sync":
                live = await op_sync_domain_status(sld, tld)
                updates = {
                    "auto_renew": live.get("autorenew", domain.auto_renew),
                    "transfer_locked": live.get("is_locked", domain.transfer_locked),
                    "whois_privacy": live.get("whois_privacy", domain.whois_privacy),
                    "nameservers": live.get("nameservers"),
                }
                await db.execute(update(Domain).where(Domain.id == domain.id).values(**updates))
                success.append(did)

        except Exception as e:
            failed.append({"id": did, "error": str(e)})

    await db.commit()

    log_event_bg(user_id="admin", action=f"admin_domain_bulk_{req.action}", resource_type="domain",
                 resource_id="bulk", details={"success": len(success), "failed": len(failed)})

    return {
        "action": req.action,
        "success": success,
        "failed": failed,
        "total_processed": len(success) + len(failed),
    }


# ── Backfill Route53 Zone IDs ────────────────────────────────────────


@router.post("/domains/internal/backfill-zones")
async def admin_backfill_zones(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """One-time utility: backfill route53_zone_id for domains missing it."""
    result = await db.execute(
        select(Domain).where(Domain.route53_zone_id.is_(None), Domain.status == "active")
    )
    domains = result.scalars().all()

    fixed = []
    failed = []

    for d in domains:
        # Try to get from linked site first
        if d.site_id:
            site_result = await db.execute(select(Site.route53_zone_id).where(Site.id == d.site_id))
            site_zone = site_result.scalar_one_or_none()
            if site_zone:
                await db.execute(
                    update(Domain).where(Domain.id == d.id).values(route53_zone_id=site_zone)
                )
                fixed.append({"domain": d.domain_name, "zone_id": site_zone, "source": "site"})
                continue

        # Create a new zone
        try:
            from app.utils.route53 import create_hosted_zone
            zone_result = await create_hosted_zone(d.domain_name)
            await db.execute(
                update(Domain).where(Domain.id == d.id).values(
                    route53_zone_id=zone_result["zone_id"],
                    nameservers=zone_result["nameservers"],
                )
            )
            fixed.append({"domain": d.domain_name, "zone_id": zone_result["zone_id"], "source": "created"})
        except Exception as e:
            failed.append({"domain": d.domain_name, "error": str(e)})

    await db.commit()

    return {"fixed": len(fixed), "failed": len(failed), "details": fixed, "errors": failed}


# ── Detail routes (parameterized — must come AFTER all fixed paths) ──────


@router.get("/domains/{site_id}")
async def get_domain_detail(
    site_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get external domain details for a specific site."""
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
        logger.exception("Failed to fetch domain details domain_id=%s", domain_id)
        raise HTTPException(status_code=500, detail="Failed to fetch domain") from e
