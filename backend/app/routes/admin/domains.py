"""
Admin domain management endpoints.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.domain import Domain
from app.models.user import User
from app.utils.audit_log import log_event_bg

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Domains"])


# ── Schemas ──────────────────────────────────────────────────────────


class DomainUpdateRequest(BaseModel):
    status: str | None = None
    auto_renew: bool | None = None
    verification_notes: str | None = None


class VerificationOverrideRequest(BaseModel):
    verification_status: str  # verified, rejected, pending


# ── Endpoints ────────────────────────────────────────────────────────


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
    """List all domains with pagination and optional filters."""
    try:
        query = select(Domain)

        if status:
            query = query.where(Domain.status == status)
        if user_id:
            query = query.where(Domain.user_id == user_id)
        if tld:
            query = query.where(Domain.tld == tld)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(Domain.created_at.desc()).limit(limit).offset(offset)
        )
        domains = result.scalars().all()

        # Fetch user emails
        user_ids = list({d.user_id for d in domains})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        return {
            "domains": [
                {
                    "id": str(d.id),
                    "user_id": d.user_id,
                    "user_email": user_map.get(d.user_id, ""),
                    "domain_name": d.domain_name,
                    "tld": d.tld,
                    "registrar": d.registrar,
                    "status": d.status,
                    "dns_status": d.dns_status,
                    "ssl_status": d.ssl_status,
                    "ssl_expires_at": _serialize_datetime(d.ssl_expires_at),
                    "verification_status": d.verification_status,
                    "auto_renew": d.auto_renew,
                    "expires_at": _serialize_datetime(d.expires_at),
                    "created_at": _serialize_datetime(d.created_at),
                }
                for d in domains
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list domains: %s", e)
        return {"domains": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.get("/domains/expiring")
async def expiring_domains(
    days: int = Query(default=30, ge=1, le=365),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List domains expiring within N days."""
    try:
        cutoff = datetime.now(UTC) + timedelta(days=days)

        result = await db.execute(
            select(Domain)
            .where(
                Domain.expires_at.isnot(None),
                Domain.expires_at <= cutoff,
                Domain.status != "expired",
            )
            .order_by(Domain.expires_at.asc())
        )
        domains = result.scalars().all()

        return {
            "expiring_within_days": days,
            "count": len(domains),
            "domains": [
                {
                    "id": str(d.id),
                    "domain_name": d.domain_name,
                    "user_id": d.user_id,
                    "status": d.status,
                    "auto_renew": d.auto_renew,
                    "expires_at": _serialize_datetime(d.expires_at),
                    "days_remaining": (d.expires_at - datetime.now(UTC)).days if d.expires_at else None,
                }
                for d in domains
            ],
        }
    except Exception as e:
        logger.warning("Failed to fetch expiring domains: %s", e)
        return {"expiring_within_days": days, "count": 0, "domains": [], "error": str(e)}


@router.get("/domains/ae-queue")
async def ae_verification_queue(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List .ae domains pending verification (TDRA queue)."""
    try:
        result = await db.execute(
            select(Domain)
            .where(
                Domain.tld == "ae",
                Domain.verification_status == "pending",
            )
            .order_by(Domain.created_at.asc())
        )
        domains = result.scalars().all()

        # Fetch user info
        user_ids = list({d.user_id for d in domains})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email, User.license_number).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: {"email": r[1], "license_number": r[2]} for r in user_result.fetchall()}

        return {
            "queue_size": len(domains),
            "domains": [
                {
                    "id": str(d.id),
                    "domain_name": d.domain_name,
                    "user_id": d.user_id,
                    "user_email": user_map.get(d.user_id, {}).get("email", ""),
                    "licence_number": d.licence_number or user_map.get(d.user_id, {}).get("license_number", ""),
                    "verification_notes": d.verification_notes,
                    "created_at": _serialize_datetime(d.created_at),
                }
                for d in domains
            ],
        }
    except Exception as e:
        logger.warning("Failed to fetch .ae verification queue: %s", e)
        return {"queue_size": 0, "domains": [], "error": str(e)}


@router.get("/domains/health")
async def domains_health(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate DNS and SSL health stats across all domains."""
    try:
        # DNS status breakdown
        dns_result = await db.execute(
            select(Domain.dns_status, func.count(Domain.id)).group_by(Domain.dns_status)
        )
        dns_stats = {r[0]: r[1] for r in dns_result.fetchall()}

        # SSL status breakdown
        ssl_result = await db.execute(
            select(Domain.ssl_status, func.count(Domain.id)).group_by(Domain.ssl_status)
        )
        ssl_stats = {r[0]: r[1] for r in ssl_result.fetchall()}

        # Domain status breakdown
        status_result = await db.execute(
            select(Domain.status, func.count(Domain.id)).group_by(Domain.status)
        )
        status_stats = {r[0]: r[1] for r in status_result.fetchall()}

        # Total domains
        total_result = await db.execute(select(func.count(Domain.id)))
        total = total_result.scalar() or 0

        return {
            "total_domains": total,
            "domain_status": status_stats,
            "dns_status": dns_stats,
            "ssl_status": ssl_stats,
        }
    except Exception as e:
        logger.warning("Failed to fetch domain health: %s", e)
        return {"error": str(e)}


@router.get("/domains/{domain_id}")
async def get_domain_detail(
    domain_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info for a specific domain."""
    try:
        result = await db.execute(select(Domain).where(Domain.id == domain_id))
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        # Get owner info
        user_result = await db.execute(
            select(User.email, User.full_name, User.company_name, User.license_number)
            .where(User.id == domain.user_id)
        )
        user_info = user_result.first()

        return {
            "id": str(domain.id),
            "site_id": str(domain.site_id) if domain.site_id else None,
            "user_id": domain.user_id,
            "owner": {
                "email": user_info[0] if user_info else "",
                "full_name": user_info[1] if user_info else "",
                "company_name": user_info[2] if user_info else "",
                "license_number": user_info[3] if user_info else "",
            } if user_info else None,
            "domain_name": domain.domain_name,
            "tld": domain.tld,
            "registrar": domain.registrar,
            "status": domain.status,
            "dns_status": domain.dns_status,
            "ssl_status": domain.ssl_status,
            "ssl_expires_at": _serialize_datetime(domain.ssl_expires_at),
            "registered_at": _serialize_datetime(domain.registered_at),
            "expires_at": _serialize_datetime(domain.expires_at),
            "auto_renew": domain.auto_renew,
            "verification_status": domain.verification_status,
            "licence_number": domain.licence_number,
            "verification_notes": domain.verification_notes,
            "created_at": _serialize_datetime(domain.created_at),
            "updated_at": _serialize_datetime(domain.updated_at),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch domain: {e}") from e


@router.patch("/domains/{domain_id}")
async def update_domain(
    domain_id: str,
    req: DomainUpdateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update domain status, auto_renew, or notes."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    updates = {}
    if req.status is not None:
        valid_statuses = {"pending", "active", "expired", "suspended"}
        if req.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        updates["status"] = req.status
    if req.auto_renew is not None:
        updates["auto_renew"] = req.auto_renew
    if req.verification_notes is not None:
        updates["verification_notes"] = req.verification_notes

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    await db.execute(update(Domain).where(Domain.id == domain_id).values(**updates))
    await db.commit()

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="update_domain",
        resource_type="domain",
        resource_id=str(domain_id),
        details={"domain_name": domain.domain_name, "updates": updates},
    )

    return {"message": f"Domain {domain.domain_name} updated", "updates": updates}


@router.post("/domains/{domain_id}/verify")
async def override_verification(
    domain_id: str,
    req: VerificationOverrideRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Override verification status for a domain."""
    valid_statuses = {"pending", "verified", "rejected"}
    if req.verification_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid verification_status. Must be one of: {valid_statuses}",
        )

    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    await db.execute(
        update(Domain)
        .where(Domain.id == domain_id)
        .values(verification_status=req.verification_status)
    )
    await db.commit()

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="override_domain_verification",
        resource_type="domain",
        resource_id=str(domain_id),
        details={
            "domain_name": domain.domain_name,
            "new_status": req.verification_status,
        },
    )

    return {
        "message": f"Verification status for {domain.domain_name} set to {req.verification_status}",
    }


@router.post("/domains/{domain_id}/ssl/reprovision")
async def reprovision_ssl(
    domain_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger SSL reprovisioning for a domain (placeholder)."""
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="reprovision_ssl",
        resource_type="domain",
        resource_id=str(domain_id),
        details={"domain_name": domain.domain_name},
    )

    return {
        "message": f"SSL reprovisioning queued for {domain.domain_name}",
        "domain_id": str(domain.id),
        "status": "queued",
    }
