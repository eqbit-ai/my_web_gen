"""
Deployment routes — deploy generated websites to AWS S3 as static sites.

Flow:
  1. User clicks "Deploy" in generator → POST /api/deploy
  2. Backend extracts HTML/CSS/JS from Redis session
  3. Uploads files to S3 bucket under site-specific prefix
  4. Returns live URL
  5. Stores deployment in sites table for dashboard tracking
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.sql import func

from app.database import async_session
from app.models.site import Site
from app.utils.auth import decode_access_token
from app.utils.cloudfront_acm import (
    request_certificate,
    check_certificate_status,
    create_distribution,
    get_distribution_status,
    disable_distribution,
    delete_distribution,
    delete_certificate,
    get_dns_records,
)
from app.utils.route53 import (
    create_hosted_zone,
    delete_hosted_zone,
    create_alias_record,
    create_acm_validation_records,
    get_nameservers,
)
from app.utils.s3_deploy import deploy_site, delete_site, verify_credentials
from app.utils.session_store import get_session

logger = logging.getLogger(__name__)

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

    # 3. Determine site name
    site_name = req.site_name.strip() if req.site_name else ""
    if not site_name:
        plan = session.get("plan", {})
        if isinstance(plan, dict):
            site_name = plan.get("company_name") or plan.get("business_name") or ""
        if not site_name:
            site_name = f"site-{req.session_id[:8]}"

    # 4. Deploy to S3
    try:
        result = await deploy_site(
            site_name=site_name,
            html=html,
            css=css,
            js=js,
            pages=pages,
            is_multipage=is_multipage,
        )
    except Exception as e:
        logger.error("Deployment failed: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Deployment failed: {str(e)}")

    # 5. Store in database
    page_count = len(pages) if pages else 1
    async with async_session() as db:
        existing = await db.execute(
            select(Site).where(
                Site.user_id == user["user_id"],
                Site.session_id == req.session_id,
            )
        )
        site = existing.scalar_one_or_none()

        if site:
            site.name = site_name
            site.status = "published"
            site.deployed_url = result["url"]
            site.cloudflare_project_name = result["project_name"]  # reuse column for S3 prefix
            site.is_multipage = is_multipage
            site.page_count = page_count
            site.deploy_error = None
            site.last_deployed_at = func.now()
        else:
            site = Site(
                user_id=user["user_id"],
                name=site_name,
                status="published",
                deployed_url=result["url"],
                cloudflare_project_name=result["project_name"],  # reuse column for S3 prefix
                session_id=req.session_id,
                is_multipage=is_multipage,
                page_count=page_count,
                last_deployed_at=func.now(),
            )
            db.add(site)

        await db.commit()
        await db.refresh(site)
        site_id = str(site.id)

    logger.info("Site deployed to S3: %s → %s", site_name, result["url"])

    return {
        "success": True,
        "site_id": site_id,
        "url": result["url"],
        "deployment_url": result["url"],
        "project_name": result["project_name"],
        "is_multipage": is_multipage,
        "page_count": page_count,
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

        try:
            deploy_result = await deploy_site(
                site_name=site.name,
                html=html,
                css=css,
                js=js,
                pages=pages,
                is_multipage=is_multipage,
            )
        except Exception as e:
            site.deploy_error = str(e)
            await db.commit()
            raise HTTPException(status_code=502, detail=f"Redeployment failed: {str(e)}")

        site.deployed_url = deploy_result["url"]
        site.status = "published"
        site.deploy_error = None
        site.is_multipage = is_multipage
        site.page_count = len(pages) if pages else 1
        site.last_deployed_at = func.now()
        if req.session_id:
            site.session_id = req.session_id
        await db.commit()

    return {
        "success": True,
        "url": deploy_result["url"],
        "deployment_url": deploy_result["url"],
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

    return {
        "site_id": str(site.id),
        "name": site.name,
        "status": site.status,
        "url": site.deployed_url,
        "domain": site.domain,
        "domain_status": site.domain_status,
        "cloudfront_domain": site.cloudfront_domain,
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
    async with async_session() as db:
        result = await db.execute(
            select(Site)
            .where(Site.user_id == user["user_id"])
            .order_by(Site.updated_at.desc())
        )
        sites = result.scalars().all()

    return {
        "sites": [
            {
                "id": str(s.id),
                "name": s.name,
                "status": s.status,
                "url": s.deployed_url,
                "domain": s.domain,
                "domain_status": s.domain_status,
                "cloudfront_domain": s.cloudfront_domain,
                "is_multipage": s.is_multipage,
                "page_count": s.page_count,
                "last_deployed_at": s.last_deployed_at.isoformat() if s.last_deployed_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sites
        ]
    }


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

    Phase 1 (immediate):
      1. Creates a Route53 hosted zone → returns nameservers
      2. Requests an ACM certificate (DNS validation)
      3. Auto-creates ACM validation CNAME records in Route53

    Phase 2 (background — after user changes nameservers & cert validates):
      4. Creates CloudFront distribution (needs ISSUED cert)
      5. Auto-creates ALIAS records in Route53

    The domain-status endpoint triggers Phase 2 when it detects the cert is ISSUED.
    """
    domain = req.domain_name.strip().lower().rstrip(".")
    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="Valid domain name is required (e.g. mybusiness.ae)")

    async with async_session() as db:
        result = await db.execute(
            select(Site).where(Site.id == site_id, Site.user_id == user["user_id"])
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        if site.status != "published":
            raise HTTPException(status_code=400, detail="Site must be deployed before connecting a domain")

        s3_prefix = site.cloudflare_project_name  # S3 project name / prefix
        if not s3_prefix:
            raise HTTPException(status_code=400, detail="Site has no S3 deployment. Deploy first.")

        # Check if domain is already in use by another site
        existing_domain = await db.execute(
            select(Site).where(Site.domain == domain, Site.id != site_id)
        )
        if existing_domain.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Domain is already connected to another site")

        # Step 1: Create Route53 hosted zone
        try:
            zone_result = await create_hosted_zone(domain)
        except Exception as e:
            logger.error("Route53 hosted zone creation failed for %s: %s", domain, e)
            raise HTTPException(status_code=502, detail=f"DNS zone creation failed: {e}")

        zone_id = zone_result["zone_id"]
        nameservers = zone_result["nameservers"]

        # Step 2: Request ACM certificate
        try:
            cert_result = await request_certificate(domain)
        except Exception as e:
            logger.error("ACM certificate request failed for %s: %s", domain, e)
            try:
                await delete_hosted_zone(zone_id)
            except Exception:
                pass
            raise HTTPException(status_code=502, detail=f"SSL certificate request failed: {e}")

        # Step 3: Auto-create ACM validation records in Route53
        if cert_result.get("validation_records"):
            try:
                await create_acm_validation_records(zone_id, cert_result["validation_records"])
                logger.info("ACM validation records auto-created in Route53 for %s", domain)
            except Exception as e:
                logger.warning("Failed to auto-create ACM validation records: %s", e)

        # CloudFront is NOT created yet — it requires an ISSUED certificate.
        # The domain-status endpoint will create it once the cert is validated.

        # Build user-facing DNS info (without CloudFront domain for now)
        dns_records = get_dns_records(
            domain=domain,
            cloudfront_domain="(pending SSL validation)",
            validation_records=cert_result["validation_records"],
        )

        # Update site in database
        site.domain = domain
        site.route53_zone_id = zone_id
        site.acm_certificate_arn = cert_result["arn"]
        site.domain_status = "pending_validation"
        site.dns_records = dns_records
        await db.commit()

    logger.info("Domain %s connected to site %s (pending SSL validation)", domain, site_id)

    return {
        "success": True,
        "domain": domain,
        "domain_status": "pending_validation",
        "nameservers": nameservers,
        "dns_records": dns_records,
        "instructions": (
            "Step 1: Update your domain's nameservers at your registrar to the nameservers listed below. "
            "Step 2: Wait for SSL certificate validation (automatic once nameservers propagate). "
            "Step 3: CloudFront CDN will be set up automatically after SSL is validated. "
            "Your site will be live at https://" + domain + " once complete."
        ),
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

    Disables and deletes the CloudFront distribution, then removes the ACM certificate.
    The S3-hosted site remains accessible via its original URL.
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

        # Step 1: Disable CloudFront distribution (if it exists)
        dist_id = site.cloudfront_distribution_id
        cert_arn = site.acm_certificate_arn

        if dist_id:
            try:
                await disable_distribution(dist_id)
                logger.info("Distribution %s disabled for domain disconnect", dist_id)
            except Exception as e:
                logger.error("Failed to disable distribution %s: %s", dist_id, e)
                # Continue with cleanup even if disable fails

        # Note: CloudFront takes ~15 min to fully disable before it can be deleted.
        # We mark the domain as disconnected immediately and schedule cleanup.
        # The distribution deletion can be handled by a background task later.

        # Step 2: Clear domain fields
        s3_prefix = site.cloudflare_project_name
        zone_id = site.route53_zone_id
        site.domain = None
        site.route53_zone_id = None
        site.cloudfront_distribution_id = None
        site.cloudfront_domain = None
        site.acm_certificate_arn = None
        site.domain_status = None
        site.dns_records = None
        # Restore original S3 URL
        if s3_prefix:
            bucket = os.getenv("AWS_S3_DEPLOY_BUCKET", "")
            region = os.getenv("AWS_REGION", "me-central-1")
            site.deployed_url = f"http://{bucket}.s3-website.{region}.amazonaws.com/{s3_prefix}/"
        await db.commit()

    # Background cleanup: delete distribution + cert + hosted zone (best-effort)
    import asyncio

    async def _cleanup():
        """Wait for distribution to deploy in disabled state, then delete it + cert + zone."""
        try:
            # CloudFront needs to be in "Deployed" state before deletion
            for _ in range(60):  # up to 30 minutes
                await asyncio.sleep(30)
                status = await get_distribution_status(dist_id)
                if status.get("status") == "Deployed":
                    break
            await delete_distribution(dist_id)
            if cert_arn:
                await delete_certificate(cert_arn)
            if zone_id:
                await delete_hosted_zone(zone_id)
            logger.info("Cleanup complete: distribution %s, cert, and zone deleted", dist_id)
        except Exception as e:
            logger.warning("Background cleanup failed for distribution %s: %s", dist_id, e)

    asyncio.create_task(_cleanup())

    return {"success": True, "message": "Domain disconnected. CloudFront cleanup in progress."}


# ── Delete Deployed Site ──────────────────────────────────────────────────


@router.delete("/{site_id}")
async def delete_deployed_site(site_id: str, user: dict = Depends(require_auth)):
    """Permanently delete a deployed site — removes S3 files, domain resources, and DB record."""
    import asyncio

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
        asyncio.create_task(_cleanup())

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
