"""
DNS management routes — manage DNS records for sites with connected custom domains.

Endpoints:
  GET  /{site_id}/records      — List all DNS records for the site's hosted zone
  POST /{site_id}/records      — Add or update a DNS record
  DELETE /{site_id}/records    — Delete a DNS record
  GET  /{site_id}/nameservers  — Get nameservers and setup instructions
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select

from app.database import async_session
from app.models.site import Site
from app.utils.auth import decode_access_token
from app.utils.route53 import delete_record, list_records, upsert_record

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

ALLOWED_RECORD_TYPES = {"A", "AAAA", "CNAME", "MX", "TXT", "SRV", "CAA"}
MANAGED_RECORD_TYPES = {"NS", "SOA"}


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


# ── Schemas ──────────────────────────────────────────────────────────────


class DNSRecordRequest(BaseModel):
    name: str
    type: str
    value: str
    ttl: int = 300


class DeleteDNSRecordRequest(BaseModel):
    name: str
    type: str
    value: str


# ── Helpers ──────────────────────────────────────────────────────────────


async def _get_user_site(site_id: str, user_id: int) -> Site:
    """Fetch a site and verify ownership + Route53 zone exists."""
    async with async_session() as session:
        result = await session.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()

    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    if site.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this site")
    if not site.route53_zone_id:
        raise HTTPException(status_code=400, detail="Site does not have a hosted zone configured")

    return site


def _is_managed_record(record_type: str, name: str, domain: str) -> bool:
    """Check if a record is managed by the system and should not be modified by users."""
    if record_type in MANAGED_RECORD_TYPES:
        return True
    # Protect meydan-managed validation records (e.g. _acme-challenge, CloudFront alias)
    if name == domain or name == f"{domain}.":
        if record_type == "A":
            return True
    return False


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/{site_id}/records")
async def get_dns_records(site_id: str, token_data: dict = Depends(require_auth)):
    """List all DNS records for a site's hosted zone."""
    user_id = token_data["user_id"]
    site = await _get_user_site(site_id, user_id)

    try:
        records = await list_records(site.route53_zone_id)
    except Exception as e:
        logger.error(f"Failed to list DNS records for zone {site.route53_zone_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch DNS records from provider") from e

    # Extract nameservers from the NS records
    ns_records = [r for r in records if r["type"] == "NS"]
    nameservers = []
    for r in ns_records:
        nameservers.extend(r["value"].split("\n"))

    return {
        "records": records,
        "nameservers": nameservers,
        "domain": site.domain,
    }


@router.post("/{site_id}/records")
async def create_or_update_dns_record(
    site_id: str,
    body: DNSRecordRequest,
    token_data: dict = Depends(require_auth),
):
    """Add or update a DNS record in the site's hosted zone."""
    user_id = token_data["user_id"]
    site = await _get_user_site(site_id, user_id)

    record_type = body.type.upper()
    if record_type not in ALLOWED_RECORD_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Record type '{body.type}' is not allowed. Must be one of: {', '.join(sorted(ALLOWED_RECORD_TYPES))}",
        )

    # Convert "@" to the actual domain name (Route53 doesn't understand "@")
    record_name = body.name.strip()
    if record_name == "@":
        record_name = site.domain
    elif not record_name.endswith(f".{site.domain}") and not record_name.endswith(f".{site.domain}.") and record_name != site.domain:
        # Subdomain shorthand: "mail" → "mail.dekorsouq.com"
        record_name = f"{record_name}.{site.domain}"

    if _is_managed_record(record_type, record_name, site.domain):
        raise HTTPException(status_code=400, detail="Cannot modify managed DNS records")

    try:
        record = await upsert_record(
            zone_id=site.route53_zone_id,
            name=record_name,
            record_type=record_type,
            value=body.value,
            ttl=body.ttl,
        )
    except Exception as e:
        logger.error(f"Failed to upsert DNS record in zone {site.route53_zone_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to create/update DNS record") from e

    return {"record": record}


@router.delete("/{site_id}/records")
async def remove_dns_record(
    site_id: str,
    body: DeleteDNSRecordRequest,
    token_data: dict = Depends(require_auth),
):
    """Delete a DNS record from the site's hosted zone."""
    user_id = token_data["user_id"]
    site = await _get_user_site(site_id, user_id)

    record_type = body.type.upper()
    if _is_managed_record(record_type, body.name, site.domain):
        raise HTTPException(status_code=400, detail="Cannot delete managed DNS records")

    try:
        await delete_record(
            zone_id=site.route53_zone_id,
            name=body.name,
            record_type=record_type,
            value=body.value,
        )
    except Exception as e:
        logger.error(f"Failed to delete DNS record in zone {site.route53_zone_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to delete DNS record") from e

    return {"success": True}


@router.get("/{site_id}/nameservers")
async def get_nameservers(site_id: str, token_data: dict = Depends(require_auth)):
    """Get nameservers for the site's domain with setup instructions."""
    user_id = token_data["user_id"]
    site = await _get_user_site(site_id, user_id)

    try:
        records = await list_records(site.route53_zone_id)
    except Exception as e:
        logger.error(f"Failed to fetch nameservers for zone {site.route53_zone_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch nameservers from provider") from e

    ns_records = [r for r in records if r["type"] == "NS"]
    nameservers = []
    for r in ns_records:
        nameservers.extend(r["value"].split("\n"))

    return {
        "nameservers": nameservers,
        "domain": site.domain,
        "instructions": (
            f"To connect your domain '{site.domain}', update the nameservers at your domain registrar "
            f"to the following values: {', '.join(nameservers)}. "
            "DNS propagation typically takes 24-48 hours."
        ),
    }
