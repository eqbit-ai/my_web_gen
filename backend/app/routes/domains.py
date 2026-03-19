"""
User-facing domain routes — search, purchase, and auto-configure DNS.

Full flow:
  1. User searches for a domain name → availability + pricing
  2. User purchases the domain → registered via OpenProvider
  3. Backend auto-creates Route53 hosted zone
  4. Backend auto-updates nameservers at OpenProvider → Route53
  5. If linked to a site: auto-requests ACM cert + CloudFront
  6. Domain goes live at https://domain.com automatically
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

# Store references to background tasks to prevent premature garbage collection
_background_tasks: set = set()

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select, update

from app.database import async_session
from app.utils import sanitize_log
from app.models.domain import Domain
from app.models.site import Site
from app.utils.audit_log import log_event_bg
from app.utils.auth import decode_access_token
from app.utils.cloudfront_acm import (
    check_certificate_status,
    create_distribution,
    get_dns_records,
    request_certificate,
)
from app.utils.openprovider import (
    OpenProviderError,
    check_domain_availability,
    register_domain,
    update_nameservers,
)
from app.utils.openprovider import (
    get_contact as op_get_contact,
)
from app.utils.openprovider import (
    reassign_domain_contact as op_reassign_contact,
)
from app.utils.openprovider import (
    renew_domain as op_renew_domain,
)
from app.utils.openprovider import (
    set_auto_renew as op_set_auto_renew,
)
from app.utils.openprovider import (
    set_whois_privacy as op_set_whois_privacy,
)
from app.utils.openprovider import (
    sync_domain_status as op_sync_domain_status,
)
from app.utils.openprovider import (
    transfer_lock as op_transfer_lock,
)
from app.utils.openprovider import (
    update_contact as op_update_contact,
)
from app.utils.openprovider import (
    verify_credentials as op_verify,
)
from app.utils.route53 import (
    create_acm_validation_records,
    create_alias_record,
    create_hosted_zone,
    get_nameservers,
)
from app.utils.route53 import (
    delete_record as r53_delete_record,
)
from app.utils.route53 import (
    list_records as r53_list_records,
)
from app.utils.route53 import (
    upsert_record as r53_upsert_record,
)

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


# ── Schemas ───────────────────────────────────────────────────────────


class DomainSearchRequest(BaseModel):
    query: str  # e.g. "mybusiness"
    extensions: list[str] | None = None  # e.g. ["com", "ae", "net"]


class DomainPurchaseRequest(BaseModel):
    domain_name: str  # SLD, e.g. "mybusiness"
    tld: str  # e.g. "com"
    period: int = 1  # years
    site_id: str | None = None  # auto-connect to an existing site
    auto_renew: bool = True


class DomainConnectRequest(BaseModel):
    site_id: str


class UpdateNameserversRequest(BaseModel):
    nameservers: list[str]


class DNSRecordRequest(BaseModel):
    name: str
    type: str  # A, AAAA, CNAME, MX, TXT, SRV
    value: str
    ttl: int = 300


class DeleteDNSRecordRequest(BaseModel):
    name: str
    type: str
    value: str
    ttl: int = 300


class UpdateContactRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None


class RenewDomainRequest(BaseModel):
    period: int = 1


class TransferRequestModel(BaseModel):
    reason: str | None = None  # Optional reason for the transfer


# ── Search ────────────────────────────────────────────────────────────


@router.get("/search")
async def search_domains(
    q: str = Query(..., min_length=1, max_length=63, description="Domain name to search"),
    extensions: str = Query(default=None, description="Comma-separated TLDs, e.g. com,ae,net"),
    user: dict = Depends(require_auth),
):
    """Search for available domains. Returns availability + pricing for each TLD."""
    # Sanitize: strip TLD if user typed "mybusiness.com"
    query = q.strip().lower()
    if "." in query:
        parts = query.rsplit(".", 1)
        query = parts[0]
        # If user typed full domain, search that specific TLD + common ones
        if extensions is None:
            extensions = parts[1]

    ext_list = None
    if extensions:
        ext_list = [e.strip().lower().lstrip(".") for e in extensions.split(",") if e.strip()]

    try:
        results = await check_domain_availability(query, ext_list)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Domain search failed: {e}") from e
    except Exception as e:
        logger.error("Domain search error: %s", e)
        raise HTTPException(status_code=502, detail="Domain search service unavailable") from e

    return {"query": query, "results": results}


# ── Purchase ──────────────────────────────────────────────────────────


@router.post("/purchase")
async def purchase_domain(req: DomainPurchaseRequest, user: dict = Depends(require_auth)):
    """Purchase and register a domain, then auto-configure DNS.

    Flow:
      1. Register domain via OpenProvider
      2. Create Route53 hosted zone
      3. Update nameservers at OpenProvider → Route53
      4. Save domain record in DB
      5. If site_id provided: auto-start SSL + CDN setup (background)
    """
    sld = req.domain_name.strip().lower()
    tld = req.tld.strip().lower().lstrip(".")
    full_domain = f"{sld}.{tld}"

    # Validate
    if not sld or not tld:
        raise HTTPException(status_code=400, detail="Domain name and TLD are required")

    # Check not already registered in our system
    async with async_session() as db:
        existing = await db.execute(
            select(Domain).where(Domain.domain_name == full_domain)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"{full_domain} is already registered in our system")

    # Step 1: Register domain via OpenProvider
    logger.info("[DOMAIN] Registering %s via OpenProvider...", sanitize_log(full_domain))
    try:
        reg_result = await register_domain(
            domain_name=sld,
            tld=tld,
            period=req.period,
            auto_renew=req.auto_renew,
        )
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Domain registration failed: {e}") from e

    # Step 2: Create Route53 hosted zone
    logger.info("[DOMAIN] Creating Route53 hosted zone for %s...", sanitize_log(full_domain))
    try:
        zone_result = await create_hosted_zone(full_domain)
    except Exception as e:
        logger.error("Route53 zone creation failed for %s: %s", sanitize_log(full_domain), e)
        raise HTTPException(status_code=502, detail=f"DNS zone creation failed: {e}") from e

    zone_id = zone_result["zone_id"]
    nameservers = zone_result["nameservers"]

    # Step 3: Update nameservers at OpenProvider → Route53
    logger.info("[DOMAIN] Updating nameservers for %s → %s", sanitize_log(full_domain), nameservers)
    try:
        await update_nameservers(sld, tld, nameservers)
    except Exception as e:
        logger.warning("[DOMAIN] Failed to auto-update nameservers for %s: %s", sanitize_log(full_domain), e)
        # Non-fatal: user can update manually if needed

    # Step 4: Save domain record
    async with async_session() as db:
        domain = Domain(
            user_id=user["user_id"],
            domain_name=full_domain,
            tld=tld,
            registrar="openprovider",
            status="active",
            dns_status="healthy",
            auto_renew=req.auto_renew,
            registered_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=365 * req.period),
            licence_number=user.get("license_number"),
            route53_zone_id=zone_id,
            openprovider_domain_id=reg_result.get("id"),
            contact_handle=reg_result.get("owner_handle"),
            nameservers=nameservers,
            transfer_locked=True,
            verification_status="verified",
        )
        db.add(domain)
        await db.commit()
        await db.refresh(domain)
        domain_id = str(domain.id)

    log_event_bg(
        user_id=str(user["user_id"]),
        action="domain_purchase",
        resource_type="domain",
        resource_id=domain_id,
        details={"domain": full_domain, "tld": tld, "period": req.period},
    )

    logger.info("[DOMAIN] ✅ %s registered and DNS configured (zone=%s)", sanitize_log(full_domain), zone_id)

    # Step 5: If a site_id was provided, auto-connect the domain
    site_connection = None
    if req.site_id:
        try:
            site_connection = await _auto_connect_domain_to_site(
                domain_id=domain_id,
                domain_name=full_domain,
                zone_id=zone_id,
                site_id=req.site_id,
                user=user,
            )
        except Exception as e:
            logger.warning("[DOMAIN] Auto-connect to site failed: %s", e)
            site_connection = {"status": "failed", "error": str(e)}

    return {
        "success": True,
        "domain_id": domain_id,
        "domain": full_domain,
        "nameservers": nameservers,
        "zone_id": zone_id,
        "registration": reg_result,
        "site_connection": site_connection,
    }


async def _auto_connect_domain_to_site(
    domain_id: str, domain_name: str, zone_id: str, site_id: str, user: dict
) -> dict:
    """Auto-connect a purchased domain to an existing site.

    Creates ACM cert, validation records, and kicks off CloudFront setup.
    The domain-status polling endpoint in deploy.py handles the rest.
    """
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            return {"status": "error", "error": "Site not found"}

        if site.status != "published":
            return {"status": "error", "error": "Site must be deployed first"}

        # Request ACM certificate
        cert_result = await request_certificate(domain_name)

        # Auto-create ACM validation records in Route53
        if cert_result.get("validation_records"):
            try:
                await create_acm_validation_records(zone_id, cert_result["validation_records"])
            except Exception as e:
                logger.warning("Failed to create ACM validation records: %s", e)

        # Update site with domain info
        dns_records = get_dns_records(
            domain=domain_name,
            cloudfront_domain="(pending SSL validation)",
            validation_records=cert_result.get("validation_records", []),
        )

        site.domain = domain_name
        site.route53_zone_id = zone_id
        site.acm_certificate_arn = cert_result["arn"]
        site.domain_status = "pending_validation"
        site.dns_records = dns_records

        # Link domain record to site
        await db.execute(
            update(Domain).where(Domain.id == domain_id).values(site_id=site.id)
        )
        await db.commit()

    # Background: poll for cert validation and auto-create CloudFront
    task = asyncio.create_task(_poll_cert_and_create_cdn(site_id, user))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {
        "status": "pending_validation",
        "message": f"Domain {domain_name} connected to site. SSL certificate is being validated — CDN will be created automatically.",
        "acm_arn": cert_result["arn"],
    }


async def _poll_cert_and_create_cdn(site_id: str, user: dict):
    """Background task: wait for ACM cert to become ISSUED, then create CloudFront."""
    MAX_WAIT = 1800  # 30 minutes — DNS propagation can be slow
    POLL_INTERVAL = 30

    for _ in range(MAX_WAIT // POLL_INTERVAL):
        await asyncio.sleep(POLL_INTERVAL)
        try:
            async with async_session() as db:
                result = await db.execute(select(Site).where(Site.id == site_id))
                site = result.scalar_one_or_none()
                if not site or not site.acm_certificate_arn:
                    return

                # Already has CloudFront or is active
                if site.cloudfront_distribution_id or site.domain_status == "active":
                    return

                cert_status = await check_certificate_status(site.acm_certificate_arn)
                if cert_status.get("status") == "FAILED":
                    site.domain_status = "failed"
                    await db.commit()
                    logger.error("[DOMAIN] ACM cert FAILED for site %s", site_id)
                    return

                if cert_status.get("status") != "ISSUED":
                    continue

                # Cert is ISSUED — create CloudFront
                s3_prefix = site.cloudflare_project_name
                if not s3_prefix:
                    return

                dist_result = await create_distribution(
                    domain=site.domain,
                    s3_project_name=s3_prefix,
                    acm_cert_arn=site.acm_certificate_arn,
                )
                site.cloudfront_distribution_id = dist_result["distribution_id"]
                site.cloudfront_domain = dist_result["domain_name"]

                # Auto-create ALIAS records
                if site.route53_zone_id:
                    try:
                        await create_alias_record(
                            zone_id=site.route53_zone_id,
                            name=site.domain,
                            target_domain=dist_result["domain_name"],
                        )
                        if not site.domain.startswith("www."):
                            await create_alias_record(
                                zone_id=site.route53_zone_id,
                                name=f"www.{site.domain}",
                                target_domain=dist_result["domain_name"],
                            )
                    except Exception as e:
                        logger.warning("Failed to create ALIAS records: %s", e)

                site.dns_records = get_dns_records(
                    domain=site.domain,
                    cloudfront_domain=dist_result["domain_name"],
                    validation_records=[],
                )
                site.domain_status = "active"
                site.deployed_url = f"https://{site.domain}"

                # Sync ssl_status on the Domain record
                dom_result = await db.execute(
                    select(Domain).where(Domain.site_id == site.id)
                )
                dom = dom_result.scalar_one_or_none()
                if dom:
                    dom.ssl_status = "active"
                    dom.dns_status = "healthy"

                await db.commit()

                logger.info("[DOMAIN] ✅ %s is live at https://%s", site.domain, site.domain)
                return

        except Exception as e:
            logger.warning("[DOMAIN] Background cert poll error for site %s: %s", sanitize_log(site_id), e)

    logger.warning("[DOMAIN] Cert validation timed out for site %s after %ds", sanitize_log(site_id), MAX_WAIT)


# ── Retry Domain Activation ────────────────────────────────────────────


@router.post("/{domain_id}/retry-activation")
async def retry_domain_activation(domain_id: str, user: dict = Depends(require_auth)):
    """Re-trigger the cert validation → CloudFront creation pipeline.

    Useful when the initial background task timed out (e.g. slow DNS propagation).
    """
    async with async_session() as db:
        result = await db.execute(
            select(Domain).where(Domain.id == domain_id, Domain.user_id == user["user_id"])
        )
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        if not domain.site_id:
            raise HTTPException(status_code=400, detail="Domain is not connected to any site")

        # Check site status
        site_result = await db.execute(select(Site).where(Site.id == domain.site_id))
        site = site_result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Connected site not found")

        if site.domain_status == "active":
            return {"status": "already_active", "message": "Domain is already active"}

        if not site.acm_certificate_arn:
            raise HTTPException(status_code=400, detail="No ACM certificate found — reconnect the domain")

        # Check cert status right now
        try:
            cert_status = await check_certificate_status(site.acm_certificate_arn)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to check certificate: {e}") from e

        status = cert_status.get("status", "UNKNOWN")

        if status == "ISSUED" and not site.cloudfront_distribution_id:
            # Cert is ready — kick off CloudFront creation immediately
            task = asyncio.create_task(_poll_cert_and_create_cdn(str(site.id), user))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
            return {"status": "creating_cdn", "message": "Certificate is valid — creating CloudFront distribution now"}

        if status == "PENDING_VALIDATION":
            # Re-start the polling background task
            task = asyncio.create_task(_poll_cert_and_create_cdn(str(site.id), user))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
            return {"status": "polling", "message": "Certificate still pending validation — re-started background polling (up to 30 min)"}

        if status == "FAILED":
            return {"status": "failed", "message": "Certificate validation failed. Try disconnecting and reconnecting the domain."}

        return {"status": status, "message": f"Certificate status: {status}"}


# ── List User's Domains ──────────────────────────────────────────────


@router.get("")
async def list_user_domains(user: dict = Depends(require_auth)):
    """List all domains owned by the current user."""
    async with async_session() as db:
        result = await db.execute(
            select(Domain)
            .where(Domain.user_id == user["user_id"])
            .order_by(Domain.created_at.desc())
        )
        domains = result.scalars().all()

    return {
        "domains": [
            {
                "id": str(d.id),
                "domain_name": d.domain_name,
                "tld": d.tld,
                "status": d.status,
                "dns_status": d.dns_status,
                "ssl_status": d.ssl_status,
                "auto_renew": d.auto_renew,
                "registered_at": d.registered_at.isoformat() if d.registered_at else None,
                "expires_at": d.expires_at.isoformat() if d.expires_at else None,
                "site_id": str(d.site_id) if d.site_id else None,
            }
            for d in domains
        ]
    }


# ── Domain Detail ────────────────────────────────────────────────────


@router.get("/{domain_id}")
async def get_domain_detail(domain_id: str, user: dict = Depends(require_auth)):
    """Get details of a specific domain."""
    async with async_session() as db:
        result = await db.execute(
            select(Domain).where(Domain.id == domain_id, Domain.user_id == user["user_id"])
        )
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        # Get linked site info
        site_info = None
        if domain.site_id:
            site_result = await db.execute(
                select(Site).where(Site.id == domain.site_id)
            )
            site = site_result.scalar_one_or_none()
            if site:
                site_info = {
                    "id": str(site.id),
                    "name": site.name,
                    "deployed_url": site.deployed_url,
                    "domain_status": site.domain_status,
                    "cloudfront_domain": site.cloudfront_domain,
                }

    return {
        "id": str(domain.id),
        "domain_name": domain.domain_name,
        "tld": domain.tld,
        "registrar": domain.registrar,
        "status": domain.status,
        "dns_status": domain.dns_status,
        "ssl_status": domain.ssl_status,
        "ssl_expires_at": domain.ssl_expires_at.isoformat() if domain.ssl_expires_at else None,
        "auto_renew": domain.auto_renew,
        "registered_at": domain.registered_at.isoformat() if domain.registered_at else None,
        "expires_at": domain.expires_at.isoformat() if domain.expires_at else None,
        "verification_status": domain.verification_status,
        "route53_zone_id": domain.route53_zone_id,
        "nameservers": domain.nameservers,
        "transfer_locked": domain.transfer_locked,
        "whois_privacy": domain.whois_privacy,
        "contact_handle": domain.contact_handle,
        "transfer_requested_at": domain.transfer_requested_at.isoformat() if domain.transfer_requested_at else None,
        "transfer_reason": domain.transfer_reason,
        "site": site_info,
    }


# ── Connect Domain to Site ───────────────────────────────────────────


@router.post("/{domain_id}/connect")
async def connect_domain_to_site(
    domain_id: str, req: DomainConnectRequest, user: dict = Depends(require_auth)
):
    """Connect a purchased domain to a deployed site. Auto-configures SSL + CDN."""
    async with async_session() as db:
        # Verify domain ownership
        result = await db.execute(
            select(Domain).where(Domain.id == domain_id, Domain.user_id == user["user_id"])
        )
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        if domain.site_id:
            raise HTTPException(status_code=400, detail="Domain is already connected to a site. Disconnect it first.")

    # Get the Route53 zone (should exist from purchase)
    # Re-create if somehow missing
    try:
        zone_result = await create_hosted_zone(domain.domain_name)
        zone_id = zone_result["zone_id"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"DNS zone creation failed: {e}") from e

    result = await _auto_connect_domain_to_site(
        domain_id=domain_id,
        domain_name=domain.domain_name,
        zone_id=zone_id,
        site_id=req.site_id,
        user=user,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return {"success": True, **result}


# ── Disconnect Domain from Site ──────────────────────────────────────


@router.post("/{domain_id}/disconnect")
async def disconnect_domain_from_site(domain_id: str, user: dict = Depends(require_auth)):
    """Disconnect a domain from its linked site. Site stays deployed on S3 URL."""
    async with async_session() as db:
        result = await db.execute(
            select(Domain).where(Domain.id == domain_id, Domain.user_id == user["user_id"])
        )
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        if not domain.site_id:
            raise HTTPException(status_code=400, detail="Domain is not connected to any site")

        # Clear site's domain fields
        site_result = await db.execute(select(Site).where(Site.id == domain.site_id))
        site = site_result.scalar_one_or_none()
        if site:
            site.domain = None
            site.route53_zone_id = None
            site.cloudfront_distribution_id = None
            site.cloudfront_domain = None
            site.acm_certificate_arn = None
            site.domain_status = None
            site.dns_records = None

        # Clear domain's site link
        domain.site_id = None
        await db.commit()

    return {"success": True, "message": f"{domain.domain_name} disconnected from site"}


# ── Helper ───────────────────────────────────────────────────────────


async def _get_user_domain(domain_id: str, user_id: int) -> Domain:
    """Load a domain record, verifying ownership."""
    async with async_session() as db:
        result = await db.execute(
            select(Domain).where(Domain.id == domain_id, Domain.user_id == user_id)
        )
        domain = result.scalar_one_or_none()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return domain


def _split_domain(domain_name: str) -> tuple[str, str]:
    """Split 'mybusiness.com' into ('mybusiness', 'com')."""
    parts = domain_name.rsplit(".", 1)
    return parts[0], parts[1]


# ── Nameservers ──────────────────────────────────────────────────────


@router.put("/{domain_id}/nameservers")
async def update_nameservers_endpoint(
    domain_id: str, req: UpdateNameserversRequest, user: dict = Depends(require_auth)
):
    """Update nameservers for a domain at the registrar."""
    if len(req.nameservers) < 2 or len(req.nameservers) > 13:
        raise HTTPException(status_code=400, detail="Must provide 2-13 nameservers")

    domain = await _get_user_domain(domain_id, user["user_id"])
    sld, tld = _split_domain(domain.domain_name)

    try:
        await update_nameservers(sld, tld, req.nameservers)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Failed to update nameservers: {e}") from e

    async with async_session() as db:
        await db.execute(
            update(Domain).where(Domain.id == domain_id).values(nameservers=req.nameservers)
        )
        await db.commit()

    log_event_bg(user_id=str(user["user_id"]), action="domain_update_ns", resource_type="domain",
                 resource_id=domain_id, details={"nameservers": req.nameservers})

    return {"success": True, "nameservers": req.nameservers}


# ── DNS Records ──────────────────────────────────────────────────────


@router.get("/{domain_id}/dns")
async def list_dns_records(domain_id: str, user: dict = Depends(require_auth)):
    """List all DNS records for a domain's Route53 zone."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    if not domain.route53_zone_id:
        raise HTTPException(status_code=400, detail="No DNS zone configured for this domain")

    try:
        records = await r53_list_records(domain.route53_zone_id)
        ns = await get_nameservers(domain.route53_zone_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch DNS records: {e}") from e

    return {"records": records, "nameservers": ns, "zone_id": domain.route53_zone_id}


@router.post("/{domain_id}/dns")
async def upsert_dns_record(domain_id: str, req: DNSRecordRequest, user: dict = Depends(require_auth)):
    """Create or update a DNS record."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    if not domain.route53_zone_id:
        raise HTTPException(status_code=400, detail="No DNS zone configured for this domain")

    if req.type.upper() in ("NS", "SOA"):
        raise HTTPException(status_code=400, detail="Cannot modify NS or SOA records")

    # Handle @ → domain apex
    name = req.name.strip()
    if name == "@":
        name = domain.domain_name
    elif not name.endswith(domain.domain_name):
        name = f"{name}.{domain.domain_name}"

    try:
        record = await r53_upsert_record(domain.route53_zone_id, name, req.type.upper(), req.value, req.ttl)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to create DNS record: {e}") from e

    log_event_bg(user_id=str(user["user_id"]), action="dns_upsert", resource_type="domain",
                 resource_id=domain_id, details={"name": name, "type": req.type, "value": req.value})

    return {"success": True, "record": record}


@router.delete("/{domain_id}/dns")
async def delete_dns_record_endpoint(domain_id: str, req: DeleteDNSRecordRequest, user: dict = Depends(require_auth)):
    """Delete a DNS record."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    if not domain.route53_zone_id:
        raise HTTPException(status_code=400, detail="No DNS zone configured for this domain")

    if req.type.upper() in ("NS", "SOA"):
        raise HTTPException(status_code=400, detail="Cannot delete NS or SOA records")

    name = req.name.strip()
    if name == "@":
        name = domain.domain_name

    try:
        await r53_delete_record(domain.route53_zone_id, name, req.type.upper(), req.value, req.ttl)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to delete DNS record: {e}") from e

    log_event_bg(user_id=str(user["user_id"]), action="dns_delete", resource_type="domain",
                 resource_id=domain_id, details={"name": name, "type": req.type})

    return {"success": True}


# ── Renew ────────────────────────────────────────────────────────────


@router.post("/{domain_id}/renew")
async def renew_domain_endpoint(domain_id: str, req: RenewDomainRequest, user: dict = Depends(require_auth)):
    """Renew a domain for additional years."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    sld, tld = _split_domain(domain.domain_name)

    try:
        await op_renew_domain(sld, tld, req.period)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Domain renewal failed: {e}") from e


    async with async_session() as db:
        d = await db.get(Domain, domain.id)
        if d.expires_at:
            d.expires_at = d.expires_at + timedelta(days=365 * req.period)
        await db.commit()

    log_event_bg(user_id=str(user["user_id"]), action="domain_renew", resource_type="domain",
                 resource_id=domain_id, details={"period": req.period})

    return {"success": True, "message": f"Domain renewed for {req.period} year(s)"}


# ── Auto-Renew Toggle ───────────────────────────────────────────────


@router.put("/{domain_id}/auto-renew")
async def toggle_auto_renew(domain_id: str, enabled: bool = Query(...), user: dict = Depends(require_auth)):
    """Toggle auto-renew on/off."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    sld, tld = _split_domain(domain.domain_name)

    try:
        await op_set_auto_renew(sld, tld, enabled)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Failed to update auto-renew: {e}") from e

    async with async_session() as db:
        await db.execute(update(Domain).where(Domain.id == domain.id).values(auto_renew=enabled))
        await db.commit()

    log_event_bg(user_id=str(user["user_id"]), action="domain_auto_renew", resource_type="domain",
                 resource_id=domain_id, details={"enabled": enabled})

    return {"success": True, "auto_renew": enabled}


# ── Contact / WHOIS ─────────────────────────────────────────────────


@router.put("/{domain_id}/contact")
async def update_contact_endpoint(domain_id: str, req: UpdateContactRequest, user: dict = Depends(require_auth)):
    """Update WHOIS contact details for the domain."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    if not domain.contact_handle:
        raise HTTPException(status_code=400, detail="No contact handle associated with this domain")

    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    has_name_change = "first_name" in fields or "last_name" in fields
    new_handle = None

    try:
        if has_name_change:
            # OpenProvider blocks name edits on contacts linked to active domains.
            # Create a new contact handle with the updated info and reassign the domain.
            sld, tld = _split_domain(domain.domain_name)
            result = await op_reassign_contact(sld, tld, domain.contact_handle, **fields)
            new_handle = result["new_handle"]
        else:
            # Non-name fields can be updated in-place
            await op_update_contact(domain.contact_handle, **fields)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Failed to update contact: {e}") from e

    # If we created a new handle, update the domain record in our DB
    if new_handle:
        async with async_session() as db:
            await db.execute(
                update(Domain).where(Domain.id == domain.id).values(contact_handle=new_handle)
            )
            await db.commit()

    log_event_bg(user_id=str(user["user_id"]), action="domain_update_contact", resource_type="domain",
                 resource_id=domain_id, details={"fields": list(fields.keys()), "new_handle": new_handle})

    return {"success": True, "updated_fields": list(fields.keys())}


# ── Transfer Lock ────────────────────────────────────────────────────


@router.put("/{domain_id}/transfer-lock")
async def toggle_transfer_lock(domain_id: str, locked: bool = Query(...), user: dict = Depends(require_auth)):
    """Enable or disable transfer lock."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    sld, tld = _split_domain(domain.domain_name)

    try:
        await op_transfer_lock(sld, tld, locked)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Failed to update transfer lock: {e}") from e

    async with async_session() as db:
        await db.execute(update(Domain).where(Domain.id == domain.id).values(transfer_locked=locked))
        await db.commit()

    log_event_bg(user_id=str(user["user_id"]), action="domain_transfer_lock", resource_type="domain",
                 resource_id=domain_id, details={"locked": locked})

    return {"success": True, "transfer_locked": locked}


# ── WHOIS Privacy ────────────────────────────────────────────────────


@router.put("/{domain_id}/whois-privacy")
async def toggle_whois_privacy(domain_id: str, enabled: bool = Query(...), user: dict = Depends(require_auth)):
    """Enable or disable WHOIS privacy."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    sld, tld = _split_domain(domain.domain_name)

    try:
        await op_set_whois_privacy(sld, tld, enabled)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Failed to update WHOIS privacy: {e}") from e

    async with async_session() as db:
        await db.execute(update(Domain).where(Domain.id == domain.id).values(whois_privacy=enabled))
        await db.commit()

    log_event_bg(user_id=str(user["user_id"]), action="domain_whois_privacy", resource_type="domain",
                 resource_id=domain_id, details={"enabled": enabled})

    return {"success": True, "whois_privacy": enabled}


# ── Contact Info ───────────────────────────────────────────────────


@router.get("/{domain_id}/contact")
async def get_contact_info(domain_id: str, user: dict = Depends(require_auth)):
    """Get WHOIS contact details for the domain from OpenProvider."""
    domain = await _get_user_domain(domain_id, user["user_id"])

    if not domain.contact_handle:
        return {"contact": None, "message": "No contact handle associated with this domain"}

    try:
        contact = await op_get_contact(domain.contact_handle)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch contact: {e}") from e

    # Normalize response
    name_data = contact.get("name", {})
    phone_data = contact.get("phone", {})
    address_data = contact.get("address", {})

    return {
        "contact": {
            "handle": domain.contact_handle,
            "first_name": name_data.get("first_name", ""),
            "last_name": name_data.get("last_name", ""),
            "company_name": contact.get("company_name", ""),
            "email": contact.get("email", ""),
            "phone": f"{phone_data.get('country_code', '')} {phone_data.get('area_code', '')}{phone_data.get('subscriber_number', '')}".strip(),
            "address": {
                "street": address_data.get("street", ""),
                "number": address_data.get("number", ""),
                "city": address_data.get("city", ""),
                "state": address_data.get("state", ""),
                "zipcode": address_data.get("zipcode", ""),
                "country": address_data.get("country", ""),
            },
        }
    }


# ── Transfer Request ──────────────────────────────────────────────


@router.post("/{domain_id}/request-transfer")
async def request_transfer(domain_id: str, req: TransferRequestModel, user: dict = Depends(require_auth)):
    """Request admin to transfer a domain out of the platform."""
    domain = await _get_user_domain(domain_id, user["user_id"])

    if domain.transfer_requested_at:
        return {
            "status": "already_requested",
            "message": "Transfer already requested",
            "requested_at": domain.transfer_requested_at.isoformat(),
        }

    async with async_session() as db:
        await db.execute(
            update(Domain).where(Domain.id == domain.id).values(
                transfer_requested_at=datetime.now(UTC),
                transfer_reason=req.reason,
            )
        )
        await db.commit()

    log_event_bg(
        user_id=str(user["user_id"]),
        action="domain_transfer_request",
        resource_type="domain",
        resource_id=domain_id,
        details={"domain": domain.domain_name, "reason": req.reason},
    )

    return {
        "status": "requested",
        "message": f"Transfer request submitted for {domain.domain_name}. Our team will contact you within 24-48 hours.",
    }


@router.delete("/{domain_id}/cancel-transfer")
async def cancel_transfer_request(domain_id: str, user: dict = Depends(require_auth)):
    """Cancel a pending transfer request."""
    domain = await _get_user_domain(domain_id, user["user_id"])

    if not domain.transfer_requested_at:
        raise HTTPException(status_code=400, detail="No transfer request to cancel")

    async with async_session() as db:
        await db.execute(
            update(Domain).where(Domain.id == domain.id).values(
                transfer_requested_at=None,
                transfer_reason=None,
            )
        )
        await db.commit()

    log_event_bg(
        user_id=str(user["user_id"]),
        action="domain_transfer_cancel",
        resource_type="domain",
        resource_id=domain_id,
        details={"domain": domain.domain_name},
    )

    return {"status": "cancelled", "message": "Transfer request cancelled"}


# ── Sync from Registrar ─────────────────────────────────────────────


@router.post("/{domain_id}/sync")
async def sync_domain(domain_id: str, user: dict = Depends(require_auth)):
    """Pull latest domain status from OpenProvider and update local DB."""
    domain = await _get_user_domain(domain_id, user["user_id"])
    sld, tld = _split_domain(domain.domain_name)

    try:
        live = await op_sync_domain_status(sld, tld)
    except OpenProviderError as e:
        raise HTTPException(status_code=502, detail=f"Failed to sync domain: {e}") from e

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

    async with async_session() as db:
        await db.execute(update(Domain).where(Domain.id == domain.id).values(**updates))
        await db.commit()

    return {"success": True, "live_status": live, "updated_fields": list(updates.keys())}


# ── Health Check ─────────────────────────────────────────────────────


@router.get("/provider/status")
async def provider_status(user: dict = Depends(require_auth)):
    """Check OpenProvider API connectivity."""
    try:
        ok = await op_verify()
        return {"connected": ok, "provider": "openprovider"}
    except Exception as e:
        return {"connected": False, "provider": "openprovider", "error": str(e)}
