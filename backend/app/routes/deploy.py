"""
Deployment routes — deploy generated websites to AWS S3 as static sites.

Flow:
  1. User clicks "Deploy" in generator → POST /api/deploy
  2. Backend extracts HTML/CSS/JS from Redis session
  3. Uploads files to S3 bucket under site-specific prefix
  4. Returns live URL
  5. Stores deployment in sites table for dashboard tracking
"""

import asyncio
import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.sql import func

from app.database import async_session
from app.utils import sanitize_log
from app.models.site import Site
from app.utils.auth import decode_access_token
from app.utils.cloudfront_acm import (
    check_certificate_status,
    create_distribution,
    delete_certificate,
    delete_distribution,
    disable_distribution,
    get_distribution_status,
    get_dns_records,
    invalidate_cache,
    request_certificate,
)
from app.utils.route53 import (
    create_acm_validation_records,
    create_alias_record,
    create_hosted_zone,
    delete_alias_record,
    delete_hosted_zone,
    get_nameservers,
)
from app.utils.s3_deploy import delete_site, deploy_site, verify_credentials
from app.utils.session_store import get_session

logger = logging.getLogger(__name__)

# Set to prevent premature garbage collection of fire-and-forget tasks
_background_tasks: set = set()

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


# ── Schemas ──────────────────────────────────────────────────────────────


class DeployRequest(BaseModel):
    session_id: str
    site_name: str = ""
    site_id: str | None = None  # Pass existing site_id to overwrite same S3 folder


class RedeployRequest(BaseModel):
    session_id: str | None = None


class ConnectDomainRequest(BaseModel):
    domain_name: str


# ── Deploy ───────────────────────────────────────────────────────────────


@router.post("")
async def deploy_website(req: DeployRequest, user: dict = Depends(require_auth)):
    """Deploy a generated website to AWS S3.

    Extracts HTML/CSS/JS from the Redis session and pushes to S3.
    Creates or updates a Site record in the database.
    """
    # 1. Get session data
    session = await get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired. Please regenerate.")

    # 2. Extract content
    is_multipage = session.get("multipage", False)
    pages = session.get("pages")
    html = session.get("html", "")
    css = session.get("css", "")
    js = session.get("js", "")

    if not html and not pages:
        raise HTTPException(status_code=400, detail="No website content found in session.")

    # Ensure multipage pages dict contains the index page
    if is_multipage and pages and "index" not in pages and html:
        pages["index"] = {"html": html, "css": css}

    # 3. Determine site name — reuse S3 prefix for the SAME website
    site_name = req.site_name.strip() if req.site_name else ""
    existing_site = None
    async with async_session() as db:
        # First try: match by explicit site_id (redesign/redeploy of same site)
        if req.site_id:
            result_q = await db.execute(
                select(Site).where(
                    Site.id == req.site_id,
                    Site.user_id == user["user_id"],
                )
            )
            existing_site = result_q.scalar_one_or_none()

        # Second try: match by session_id (same generation = same site)
        if not existing_site:
            result_q = await db.execute(
                select(Site).where(
                    Site.user_id == user["user_id"],
                    Site.session_id == req.session_id,
                )
            )
            existing_site = result_q.scalar_one_or_none()

    # Reuse the existing S3 prefix only for the SAME website
    if existing_site and existing_site.cloudflare_project_name:
        site_name = site_name or existing_site.name or existing_site.cloudflare_project_name
    elif not site_name:
        plan = session.get("plan", {})
        if isinstance(plan, dict):
            site_name = plan.get("company_name") or plan.get("business_name") or ""
        if not site_name:
            site_name = f"site-{req.session_id[:8]}"

    # 4. Create or get site record BEFORE deploy (so we have site_id for form injection)
    s3_project_name = existing_site.cloudflare_project_name if existing_site and existing_site.cloudflare_project_name else None
    page_count = len(pages) if pages else 1
    async with async_session() as db:
        if existing_site:
            refetch = await db.execute(select(Site).where(Site.id == existing_site.id))
            site = refetch.scalar_one_or_none()
        else:
            site = None

        if not site:
            # Create draft record to get the site_id for form action injection
            site = Site(
                user_id=user["user_id"],
                name=site_name,
                status="draft",
                session_id=req.session_id,
                is_multipage=is_multipage,
                page_count=page_count,
            )
            db.add(site)
            await db.commit()
            await db.refresh(site)

    deploy_site_id = str(site.id)
    custom_head = getattr(site, "custom_head_code", "") or ""
    custom_body = getattr(site, "custom_body_code", "") or ""

    # 5. Deploy to S3
    try:
        result = await deploy_site(
            site_name=site_name,
            html=html,
            css=css,
            js=js,
            pages=pages,
            is_multipage=is_multipage,
            s3_prefix_override=s3_project_name,
            site_id=deploy_site_id,
            custom_head_code=custom_head,
            custom_body_code=custom_body,
        )
    except Exception as e:
        logger.error("Deployment failed: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Deployment failed: {str(e)}") from e

    # 6. Update site record with deploy result
    site_id = deploy_site_id
    async with async_session() as db:
        refetch = await db.execute(select(Site).where(Site.id == deploy_site_id))
        site = refetch.scalar_one_or_none()

        if site:
            site.name = site_name
            site.status = "published"
            site.deployed_url = result["url"]
            site.cloudflare_project_name = result["project_name"]
            site.session_id = req.session_id
            site.is_multipage = is_multipage
            site.page_count = page_count
            site.deploy_error = None
            site.last_deployed_at = func.now()
            await db.commit()
            await db.refresh(site)
            site_id = str(site.id)
        else:
            await db.commit()

    # Invalidate CloudFront cache if site has a distribution (overwrote existing files)
    cache_invalidated = False
    async with async_session() as db:
        refetch = await db.execute(select(Site).where(Site.id == site_id))
        site_obj = refetch.scalar_one_or_none()
        cf_dist_id = getattr(site_obj, "cloudfront_distribution_id", None) if site_obj else None
    if cf_dist_id:
        try:
            inv_result = await invalidate_cache(cf_dist_id)
            cache_invalidated = inv_result.get("status") != "failed"
        except Exception as e:
            logger.warning("Cache invalidation failed for site %s: %s", site_id, e)

    # Build CNAME target from S3 hostname
    bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "")
    region = os.getenv("AWS_REGION", "me-central-1")
    s3_hostname = f"{bucket}.s3-website.{region}.amazonaws.com" if bucket else None

    logger.info("Site deployed to S3: %s → %s", sanitize_log(site_name), result["url"])

    return {
        "success": True,
        "site_id": site_id,
        "url": result["url"],
        "deployment_url": result["url"],
        "project_name": result["project_name"],
        "cname_target": s3_hostname,
        "s3_hostname": s3_hostname,
        "is_multipage": is_multipage,
        "page_count": page_count,
        "cache_invalidated": cache_invalidated,
    }


# ── Redeploy ─────────────────────────────────────────────────────────────


@router.post("/{site_id}/redeploy")
async def redeploy_website(site_id: str, req: RedeployRequest, user: dict = Depends(require_auth)):
    """Redeploy an existing site (after edits)."""
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        session_id = req.session_id or site.session_id
        if not session_id:
            raise HTTPException(status_code=400, detail="No session ID available for redeployment")

        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session expired. Please regenerate the site first.")

        is_multipage = session.get("multipage", False)
        pages = session.get("pages")
        html = session.get("html", "")
        css = session.get("css", "")
        js = session.get("js", "")

        # Ensure multipage pages dict contains the index page
        if is_multipage and pages and "index" not in pages and html:
            pages["index"] = {"html": html, "css": css}

        try:
            deploy_result = await deploy_site(
                site_name=site.name,
                html=html,
                css=css,
                js=js,
                pages=pages,
                is_multipage=is_multipage,
                site_id=site_id,
            )
        except Exception as e:
            site.deploy_error = str(e)
            await db.commit()
            raise HTTPException(status_code=502, detail=f"Redeployment failed: {str(e)}") from e

        site.deployed_url = deploy_result["url"]
        site.status = "published"
        site.deploy_error = None
        site.is_multipage = is_multipage
        site.page_count = len(pages) if pages else 1
        site.last_deployed_at = func.now()
        if req.session_id:
            site.session_id = req.session_id
        await db.commit()

        # Invalidate CloudFront cache so the new content is served immediately
        cf_distribution_id = getattr(site, "cloudfront_distribution_id", None)
        cache_invalidated = False
        if cf_distribution_id:
            try:
                inv_result = await invalidate_cache(cf_distribution_id)
                cache_invalidated = inv_result.get("status") != "failed"
            except Exception as e:
                logger.warning("Cache invalidation failed for site %s: %s", site_id, e)

    return {
        "success": True,
        "url": deploy_result["url"],
        "deployment_url": deploy_result["url"],
        "cache_invalidated": cache_invalidated,
    }


# ── Status ───────────────────────────────────────────────────────────────


@router.get("/{site_id}/status")
async def get_deploy_status(site_id: str, user: dict = Depends(require_auth)):
    """Get deployment status for a site."""
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

    bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "")
    region = os.getenv("AWS_REGION", "me-central-1")
    s3_hostname = f"{bucket}.s3-website.{region}.amazonaws.com" if bucket else None
    cname_target = site.cloudfront_domain or s3_hostname

    return {
        "site_id": str(site.id),
        "name": site.name,
        "status": site.status,
        "url": site.deployed_url,
        "domain": site.domain,
        "domain_status": site.domain_status,
        "cloudfront_domain": site.cloudfront_domain,
        "cname_target": cname_target,
        "s3_hostname": s3_hostname,
        "dns_records": site.dns_records,
        "is_multipage": site.is_multipage,
        "page_count": site.page_count,
        "last_deployed_at": site.last_deployed_at.isoformat() if site.last_deployed_at else None,
        "error": site.deploy_error,
    }


# ── List User's Sites ───────────────────────────────────────────────────


@router.get("")
async def list_deployed_sites(user: dict = Depends(require_auth)):
    """List all deployed sites for the current user."""
    from app.models.domain import Domain as DomainModel
    async with async_session() as db:
        result = await db.execute(
            select(Site)
            .where(Site.user_id == user["user_id"])
            .order_by(Site.updated_at.desc())
        )
        sites = result.scalars().all()

        # Map site_id → domain record for sites with domains
        site_ids = [s.id for s in sites if s.domain]
        domain_map = {}
        if site_ids:
            dom_result = await db.execute(
                select(DomainModel).where(DomainModel.site_id.in_(site_ids))
            )
            for d in dom_result.scalars().all():
                domain_map[str(d.site_id)] = d

    site_list = []
    for s in sites:
        # Build CNAME target: CloudFront domain if available, else S3 website hostname
        bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "")
        region = os.getenv("AWS_REGION", "me-central-1")
        s3_hostname = f"{bucket}.s3-website.{region}.amazonaws.com" if bucket else None
        cname_target = s.cloudfront_domain or s3_hostname

        entry = {
            "id": str(s.id),
            "name": s.name,
            "status": s.status,
            "url": s.deployed_url,
            "domain": s.domain,
            "domain_status": s.domain_status,
            "cloudfront_domain": s.cloudfront_domain,
            "route53_zone_id": s.route53_zone_id,
            "dns_records": s.dns_records or [],
            "cname_target": cname_target,
            "s3_hostname": s3_hostname,
            "is_multipage": s.is_multipage,
            "page_count": s.page_count,
            "last_deployed_at": s.last_deployed_at.isoformat() if s.last_deployed_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        dom = domain_map.get(str(s.id))
        if dom:
            entry["domain_record_id"] = str(dom.id)
            entry["contact_handle"] = dom.contact_handle
            entry["transfer_requested_at"] = dom.transfer_requested_at.isoformat() if dom.transfer_requested_at else None
            entry["whois_privacy"] = dom.whois_privacy
            entry["transfer_locked"] = dom.transfer_locked
            entry["expires_at"] = dom.expires_at.isoformat() if dom.expires_at else None
        site_list.append(entry)

    return {"sites": site_list}


# ── Take Offline ─────────────────────────────────────────────────────────


@router.post("/{site_id}/offline")
async def take_site_offline(site_id: str, user: dict = Depends(require_auth)):
    """Mark a site as offline and remove files from S3."""
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        # Delete files from S3
        if site.cloudflare_project_name:
            try:
                await delete_site(site.cloudflare_project_name)
            except Exception as e:
                logger.warning("Failed to delete S3 files for %s: %s", site.cloudflare_project_name, e)

        site.status = "offline"
        await db.commit()

    return {"success": True, "status": "offline"}


# ── Connect Custom Domain ─────────────────────────────────────────────


@router.post("/{site_id}/connect-domain")
async def connect_domain(site_id: str, req: ConnectDomainRequest, user: dict = Depends(require_auth)):
    """Connect a custom domain to a deployed site.

    For platform-purchased domains with existing Route53 zone + ACM cert:
      - Reuses existing infrastructure (no NS change, no SSL wait)
      - Creates CloudFront distribution immediately if cert is ISSUED
      - Domain goes live in ~5 minutes (CloudFront deploy time only)

    For external domains (first-time setup):
      Phase 1: Creates Route53 zone + ACM cert + validation records
      Phase 2: domain-status endpoint creates CloudFront once cert is ISSUED
    """
    domain = req.domain_name.strip().lower().rstrip(".")
    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="Valid domain name is required (e.g. mybusiness.ae)")

    # Split into SLD and TLD
    parts = domain.rsplit(".", 1)
    check_sld, check_tld = parts[0], parts[1]

    # Check if domain is purchased through our platform
    from app.models.domain import Domain as DomainModel
    async with async_session() as db:
        internal = await db.execute(
            select(DomainModel).where(DomainModel.domain_name == domain)
        )
        internal_domain = internal.scalar_one_or_none()

    if not internal_domain:
        # External domain — check if it's registered anywhere
        try:
            from app.utils.openprovider import check_domain_availability
            results = await check_domain_availability(check_sld, [check_tld])
            if results and results[0].get("status") == "free":
                raise HTTPException(
                    status_code=400,
                    detail=f"Domain {domain} is not registered. You need to register it first before connecting. Purchase it from the Domains section."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("[DOMAIN] Availability check failed for %s: %s — proceeding anyway", sanitize_log(domain), e)

    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        if site.status != "published":
            raise HTTPException(status_code=400, detail="Site must be deployed before connecting a domain")

        s3_prefix = site.cloudflare_project_name
        if not s3_prefix:
            raise HTTPException(status_code=400, detail="Site has no S3 deployment. Deploy first.")

        # Check if domain is already in use by another site
        existing_domain = await db.execute(
            select(Site).where(Site.domain == domain, Site.id != site_id)
        )
        if existing_domain.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Domain is already connected to another site")

        # ── Reuse existing infrastructure from Domain record if available ──
        has_existing_zone = internal_domain and internal_domain.route53_zone_id
        has_existing_cert = internal_domain and internal_domain.acm_certificate_arn

        # --- Route53 Zone ---
        if has_existing_zone:
            zone_id = internal_domain.route53_zone_id
            nameservers = internal_domain.nameservers or []
            if not nameservers:
                try:
                    nameservers = await get_nameservers(zone_id)
                except Exception:
                    nameservers = []
            logger.info("Reusing existing Route53 zone %s for %s", zone_id, domain)
        else:
            try:
                zone_result = await create_hosted_zone(domain)
            except Exception as e:
                logger.error("Route53 hosted zone creation failed for %s: %s", domain, e)
                raise HTTPException(status_code=502, detail=f"DNS zone creation failed: {e}") from e
            zone_id = zone_result["zone_id"]
            nameservers = zone_result["nameservers"]
            # Persist on Domain record for future reconnects
            if internal_domain:
                refetch = await db.execute(select(DomainModel).where(DomainModel.id == internal_domain.id))
                dom = refetch.scalar_one_or_none()
                if dom:
                    dom.route53_zone_id = zone_id
                    dom.nameservers = nameservers

        # --- ACM Certificate ---
        cert_arn = None
        cert_issued = False
        validation_records = []

        if has_existing_cert:
            cert_arn = internal_domain.acm_certificate_arn
            # Check if it's still valid
            try:
                cert_status = await check_certificate_status(cert_arn)
                cert_issued = cert_status.get("status") == "ISSUED"
                logger.info("Reusing existing ACM cert %s (status=%s) for %s", cert_arn, cert_status.get("status"), domain)
            except Exception:
                # Cert might be deleted — request a new one
                cert_arn = None

        if not cert_arn:
            try:
                cert_result = await request_certificate(domain)
            except Exception as e:
                logger.error("ACM certificate request failed for %s: %s", domain, e)
                if not has_existing_zone:
                    try:
                        await delete_hosted_zone(zone_id)
                    except Exception:
                        pass
                raise HTTPException(status_code=502, detail=f"SSL certificate request failed: {e}") from e
            cert_arn = cert_result["arn"]
            validation_records = cert_result.get("validation_records", [])
            # Persist on Domain record
            if internal_domain:
                refetch = await db.execute(select(DomainModel).where(DomainModel.id == internal_domain.id))
                dom = refetch.scalar_one_or_none()
                if dom:
                    dom.acm_certificate_arn = cert_arn

            # Auto-create ACM validation records in Route53
            if validation_records:
                try:
                    await create_acm_validation_records(zone_id, validation_records)
                    logger.info("ACM validation records auto-created in Route53 for %s", domain)
                except Exception as e:
                    logger.warning("Failed to auto-create ACM validation records: %s", e)

        # --- If cert is already ISSUED, create CloudFront immediately ---
        cf_dist_id = None
        cf_domain = None
        if cert_issued:
            try:
                dist_result = await create_distribution(
                    domain=domain,
                    s3_project_name=s3_prefix,
                    acm_cert_arn=cert_arn,
                )
                cf_dist_id = dist_result["distribution_id"]
                cf_domain = dist_result["domain_name"]
                logger.info("CloudFront distribution created immediately for %s: %s", domain, cf_dist_id)

                # Auto-create ALIAS records in Route53
                try:
                    await create_alias_record(zone_id=zone_id, name=domain, target_domain=cf_domain)
                    if not domain.startswith("www."):
                        await create_alias_record(zone_id=zone_id, name=f"www.{domain}", target_domain=cf_domain)
                    logger.info("ALIAS records auto-created for %s", domain)
                except Exception as e:
                    logger.warning("Failed to auto-create ALIAS records: %s", e)
            except Exception as e:
                logger.error("Immediate CloudFront creation failed for %s: %s", domain, e)
                # Fall through — domain-status endpoint will retry

        # Determine initial status
        if cf_dist_id:
            domain_status_val = "pending_deployment"  # CloudFront deploying (~5 min)
            cf_domain_display = cf_domain
        else:
            domain_status_val = "pending_validation"
            cf_domain_display = "(pending SSL validation)"

        dns_records = get_dns_records(
            domain=domain,
            cloudfront_domain=cf_domain_display or "(pending SSL validation)",
            validation_records=validation_records,
        )

        # Update site
        site.domain = domain
        site.route53_zone_id = zone_id
        site.acm_certificate_arn = cert_arn
        site.cloudfront_distribution_id = cf_dist_id
        site.cloudfront_domain = cf_domain
        site.domain_status = domain_status_val
        site.dns_records = dns_records

        # Link Domain record to this site
        if internal_domain:
            refetch = await db.execute(select(DomainModel).where(DomainModel.id == internal_domain.id))
            dom = refetch.scalar_one_or_none()
            if dom:
                dom.site_id = site.id
                dom.ssl_status = "issued" if cert_issued else "pending_validation"

        await db.commit()

    cf_domain_for_cname = site.cloudfront_domain or "(will be available after SSL validation)"

    if cert_issued:
        instructions = (
            "Your domain already has a valid SSL certificate. "
            "CloudFront CDN is being deployed now (~5 minutes). "
            "Your site will be live at https://" + domain + " shortly."
        )
    else:
        instructions = (
            "Choose one of these options to connect your domain:\n\n"
            "Option A (Recommended): Add a CNAME record at your DNS provider:\n"
            f"  www.{domain} → {cf_domain_for_cname}\n\n"
            "Option B (Full control): Change your nameservers to the ones listed below. "
            "This gives us full DNS control including SSL auto-setup.\n\n"
            "SSL certificate will be validated automatically once DNS propagates."
        )

    logger.info("Domain %s connected to site %s (status=%s, reused_infra=%s)", sanitize_log(domain), sanitize_log(str(site_id)), sanitize_log(domain_status_val), bool(has_existing_zone))

    return {
        "success": True,
        "domain": domain,
        "domain_status": domain_status_val,
        "nameservers": nameservers,
        "cloudfront_domain": cf_domain_for_cname,
        "cname_target": cf_domain_for_cname,
        "cname_record": f"www.{domain} → {cf_domain_for_cname}",
        "dns_records": dns_records,
        "reused_infrastructure": bool(has_existing_zone or has_existing_cert),
        "instructions": instructions,
    }


# ── Domain Status ────────────────────────────────────────────────────────


@router.get("/{site_id}/domain-status")
async def domain_status(site_id: str, user: dict = Depends(require_auth)):
    """Check the current status of a custom domain connection.

    Polls ACM certificate validation and CloudFront deployment status.
    """
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        if not site.acm_certificate_arn:
            # Fetch nameservers if zone exists
            ns = []
            if site.route53_zone_id:
                try:
                    ns = await get_nameservers(site.route53_zone_id)
                except Exception:
                    pass
            return {
                "domain": site.domain,
                "domain_status": site.domain_status or "none",
                "dns_records": site.dns_records or [],
                "nameservers": ns,
            }

        # Check certificate status
        try:
            cert_status = await check_certificate_status(site.acm_certificate_arn)
        except Exception as e:
            logger.warning("Failed to check cert status for %s: %s", site_id, e)
            cert_status = {"status": "UNKNOWN"}

        cert_issued = cert_status.get("status") == "ISSUED"

        # Phase 2: If cert just became ISSUED and no CloudFront yet, create it now
        if cert_issued and not site.cloudfront_distribution_id:
            s3_prefix = site.cloudflare_project_name
            if s3_prefix:
                try:
                    dist_result = await create_distribution(
                        domain=site.domain,
                        s3_project_name=s3_prefix,
                        acm_cert_arn=site.acm_certificate_arn,
                    )
                    site.cloudfront_distribution_id = dist_result["distribution_id"]
                    site.cloudfront_domain = dist_result["domain_name"]
                    logger.info("CloudFront distribution auto-created for %s: %s", site.domain, dist_result["distribution_id"])

                    # Auto-create ALIAS records in Route53
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
                            logger.info("ALIAS records auto-created for %s", site.domain)
                        except Exception as e:
                            logger.warning("Failed to auto-create ALIAS records: %s", e)

                    # Update DNS records with real CloudFront domain
                    site.dns_records = get_dns_records(
                        domain=site.domain,
                        cloudfront_domain=dist_result["domain_name"],
                        validation_records=[],
                    )
                    await db.commit()
                except Exception as e:
                    logger.error("Auto CloudFront creation failed for %s: %s", site.domain, e)

        # Check CloudFront status
        cf_status = None
        if site.cloudfront_distribution_id:
            try:
                cf_status = await get_distribution_status(site.cloudfront_distribution_id)
            except Exception as e:
                logger.warning("Failed to check CF status for %s: %s", site_id, e)

        # Determine overall domain status
        cf_deployed = cf_status and cf_status.get("status") == "Deployed"

        if cert_issued and cf_deployed:
            new_status = "active"
            deployed_url = f"https://{site.domain}"
        elif cert_status.get("status") == "FAILED":
            new_status = "failed"
            deployed_url = site.deployed_url
        elif cert_issued and site.cloudfront_distribution_id:
            new_status = "pending_deployment"
            deployed_url = site.deployed_url
        elif cert_issued:
            new_status = "creating_cdn"
            deployed_url = site.deployed_url
        else:
            new_status = "pending_validation"
            deployed_url = site.deployed_url

        # Update if status changed
        if new_status != site.domain_status:
            site.domain_status = new_status
            if new_status == "active":
                site.deployed_url = deployed_url
                # Sync ssl_status on the Domain record
                from app.models.domain import Domain as DomainModel
                dom_result = await db.execute(
                    select(DomainModel).where(DomainModel.site_id == site.id)
                )
                dom = dom_result.scalar_one_or_none()
                if dom:
                    dom.ssl_status = "active"
                    dom.dns_status = "healthy"
            await db.commit()

        # Fetch nameservers
        ns = []
        if site.route53_zone_id:
            try:
                ns = await get_nameservers(site.route53_zone_id)
            except Exception:
                pass

    return {
        "domain": site.domain,
        "domain_status": new_status,
        "ssl_status": cert_status.get("status", "UNKNOWN"),
        "cloudfront_status": cf_status.get("status") if cf_status else None,
        "cloudfront_domain": site.cloudfront_domain,
        "deployed_url": deployed_url,
        "dns_records": site.dns_records or [],
        "nameservers": ns,
    }


# ── Disconnect Domain ────────────────────────────────────────────────────


@router.delete("/{site_id}/disconnect-domain")
async def disconnect_domain(site_id: str, user: dict = Depends(require_auth)):
    """Disconnect a custom domain from a site.

    For platform-purchased domains:
      - Deletes CloudFront distribution only
      - KEEPS Route53 zone + ACM cert on the Domain record for instant reconnect
      - No nameserver change needed when reconnecting to a new site

    For external domains:
      - Deletes CloudFront + ACM cert + Route53 zone (full cleanup)
    """
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        if not site.domain:
            raise HTTPException(status_code=400, detail="No custom domain is connected")

        domain_name = site.domain
        dist_id = site.cloudfront_distribution_id
        site_cf_domain = site.cloudfront_domain  # needed for ALIAS record cleanup
        cert_arn = site.acm_certificate_arn
        zone_id = site.route53_zone_id
        s3_prefix = site.cloudflare_project_name

        # Check if this is a platform-purchased domain
        from app.models.domain import Domain as DomainModel
        dom_result = await db.execute(
            select(DomainModel).where(DomainModel.domain_name == domain_name)
        )
        internal_domain = dom_result.scalar_one_or_none()
        is_platform_domain = internal_domain is not None

        # Step 1: Disable CloudFront distribution (always)
        if dist_id:
            try:
                await disable_distribution(dist_id)
                logger.info("Distribution %s disabled for domain disconnect", dist_id)
            except Exception as e:
                logger.error("Failed to disable distribution %s: %s", dist_id, e)

        # Step 2: Clear domain fields on the Site record
        site.domain = None
        site.cloudfront_distribution_id = None
        site.cloudfront_domain = None
        site.domain_status = None
        site.dns_records = None

        if is_platform_domain:
            # Platform domain: keep zone + cert on Domain record, clear from Site only
            site.route53_zone_id = None
            site.acm_certificate_arn = None
            # Ensure Domain record has the infra fields preserved
            if internal_domain:
                if not internal_domain.route53_zone_id and zone_id:
                    internal_domain.route53_zone_id = zone_id
                if not internal_domain.acm_certificate_arn and cert_arn:
                    internal_domain.acm_certificate_arn = cert_arn
                internal_domain.site_id = None  # Unlink from site
                internal_domain.ssl_status = "issued" if cert_arn else "none"
            logger.info("Platform domain %s disconnected — keeping Route53 zone + ACM cert for reconnect", domain_name)
        else:
            # External domain: clear everything from Site
            site.route53_zone_id = None
            site.acm_certificate_arn = None

        # Restore original S3 URL
        if s3_prefix:
            bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "")
            region = os.getenv("AWS_REGION", "me-central-1")
            # S3 static website hosting only supports HTTP — HTTPS requires CloudFront (added when domain connected)
            site.deployed_url = f"http://{bucket}.s3-website.{region}.amazonaws.com/{s3_prefix}/"  # noqa: S105

        await db.commit()

    # Background cleanup: delete CloudFront distribution (always)
    # For external domains, also delete cert + zone
    async def _cleanup():
        try:
            if dist_id:
                for _ in range(60):  # up to 30 minutes
                    await asyncio.sleep(30)
                    status = await get_distribution_status(dist_id)
                    if status.get("status") == "Deployed":
                        break
                await delete_distribution(dist_id)
                logger.info("CloudFront distribution %s deleted", dist_id)

            if not is_platform_domain:
                # External domain: full cleanup
                if cert_arn:
                    await delete_certificate(cert_arn)
                if zone_id:
                    await delete_hosted_zone(zone_id)
                logger.info("Full cleanup complete for external domain %s", domain_name)
            else:
                # Platform domain: remove old ALIAS records from Route53 (they point to deleted CloudFront)
                if zone_id and site_cf_domain:
                    try:
                        await delete_alias_record(zone_id, domain_name, site_cf_domain)
                        if not domain_name.startswith("www."):
                            await delete_alias_record(zone_id, f"www.{domain_name}", site_cf_domain)
                    except Exception as e:
                        logger.warning("Failed to clean up ALIAS records for %s: %s", domain_name, e)
                logger.info("CloudFront cleanup complete for platform domain %s (zone + cert preserved)", domain_name)
        except Exception as e:
            logger.warning("Background cleanup failed for %s: %s", domain_name, e)

    task = asyncio.create_task(_cleanup())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    msg = "Domain disconnected."
    if is_platform_domain:
        msg += " DNS and SSL infrastructure preserved — you can reconnect this domain instantly to any site."
    else:
        msg += " CloudFront cleanup in progress."

    return {"success": True, "message": msg, "platform_domain": is_platform_domain}


# ── Available Domains for Connection ─────────────────────────────────────


@router.get("/{site_id}/available-domains")
async def get_available_domains(site_id: str, user: dict = Depends(require_auth)):
    """Get user's purchased domains that are available to connect to this site.

    Returns domains that are:
    - Owned by this user
    - Not currently connected to any site (site_id is null)
    - Status is active
    """
    from app.models.domain import Domain as DomainModel
    async with async_session() as db:
        # Verify site exists and belongs to user
        site_result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = site_result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        # Get all user's domains that are not connected to any site
        result = await db.execute(
            select(DomainModel).where(
                DomainModel.user_id == user["user_id"],
                DomainModel.site_id.is_(None),
                DomainModel.status == "active",
            ).order_by(DomainModel.domain_name)
        )
        available = result.scalars().all()

        # Also get the domain currently connected to this site (if any)
        current_domain = None
        if site.domain:
            dom_result = await db.execute(
                select(DomainModel).where(DomainModel.domain_name == site.domain)
            )
            current_dom = dom_result.scalar_one_or_none()
            if current_dom:
                current_domain = {
                    "id": str(current_dom.id),
                    "domain_name": current_dom.domain_name,
                    "status": current_dom.status,
                    "ssl_status": current_dom.ssl_status,
                }

    return {
        "available_domains": [
            {
                "id": str(d.id),
                "domain_name": d.domain_name,
                "tld": d.tld,
                "has_ssl": d.acm_certificate_arn is not None,
                "has_dns": d.route53_zone_id is not None,
                "instant_connect": d.acm_certificate_arn is not None and d.route53_zone_id is not None,
                "registered_at": d.registered_at.isoformat() if d.registered_at else None,
                "expires_at": d.expires_at.isoformat() if d.expires_at else None,
            }
            for d in available
        ],
        "current_domain": current_domain,
        "site_status": site.status,
    }


# ── Delete Deployed Site ──────────────────────────────────────────────────


@router.delete("/{site_id}")
async def delete_deployed_site(site_id: str, user: dict = Depends(require_auth)):
    """Permanently delete a deployed site — removes S3 files, domain resources, and DB record."""
    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        s3_prefix = site.cloudflare_project_name
        dist_id = site.cloudfront_distribution_id
        cert_arn = site.acm_certificate_arn
        zone_id = site.route53_zone_id

        # Delete S3 files
        if s3_prefix:
            try:
                await delete_site(s3_prefix)
            except Exception as e:
                logger.warning("Failed to delete S3 files for %s: %s", s3_prefix, e)

        # Delete DB record
        await db.delete(site)
        await db.commit()

    # Background cleanup: CloudFront + ACM + Route53 (best-effort)
    async def _cleanup():
        try:
            if dist_id:
                try:
                    await disable_distribution(dist_id)
                except Exception:
                    pass
                for _ in range(60):
                    await asyncio.sleep(30)
                    status = await get_distribution_status(dist_id)
                    if status.get("status") == "Deployed":
                        break
                await delete_distribution(dist_id)
            if cert_arn:
                await delete_certificate(cert_arn)
            if zone_id:
                await delete_hosted_zone(zone_id)
            logger.info("Cleanup complete for deleted site %s", site_id)
        except Exception as e:
            logger.warning("Background cleanup failed for site %s: %s", site_id, e)

    if dist_id or cert_arn or zone_id:
        task = asyncio.create_task(_cleanup())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    return {"success": True, "message": "Site deleted"}


# ── Health Check ─────────────────────────────────────────────────────────


@router.get("/aws/status")
async def aws_status(user: dict = Depends(require_auth)):
    """Check if AWS S3 credentials and bucket are valid."""
    try:
        valid = await verify_credentials()
        return {"connected": valid, "provider": "aws-s3"}
    except Exception as e:
        return {"connected": False, "provider": "aws-s3", "error": str(e)}
