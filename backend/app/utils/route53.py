"""
Route53 DNS utility — manages hosted zones and DNS records for custom domains.

Each tenant's custom domain gets its own Route53 public hosted zone.
Provides full CRUD on DNS records (A, AAAA, CNAME, MX, TXT, SRV, CAA)
so users can manage DNS from the dashboard.

System-managed records (ACM validation CNAMEs, CloudFront ALIAS) are
auto-created and marked with a "meydan-managed" comment.
"""

import asyncio
import hashlib
import logging
import os
import uuid

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# CloudFront hosted zone ID — AWS constant for all CloudFront distributions
CLOUDFRONT_HOSTED_ZONE_ID = "Z2FDTNDATAQYW2"

SUPPORTED_RECORD_TYPES = {"A", "AAAA", "CNAME", "MX", "TXT", "SRV", "CAA"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_route53_client():
    """Create a Route53 client using env credentials."""
    return boto3.client(
        "route53",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def _normalize_name(name: str) -> str:
    """Ensure a DNS name ends with a trailing dot (Route53 requirement)."""
    if not name.endswith("."):
        name += "."
    return name


def _clean_zone_id(zone_id: str) -> str:
    """Strip the /hostedzone/ prefix if present."""
    return zone_id.replace("/hostedzone/", "")


def _record_id(name: str, record_type: str) -> str:
    """Generate a deterministic ID for a record by hashing name+type."""
    raw = f"{name}|{record_type}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _wrap_txt_value(value: str) -> str:
    """Auto-wrap TXT record value in quotes if not already wrapped."""
    value = value.strip()
    if not (value.startswith('"') and value.endswith('"')):
        value = f'"{value}"'
    return value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def create_hosted_zone(domain: str) -> dict:
    """
    Create a Route53 public hosted zone for the given domain.

    Returns {"zone_id": "Z1234...", "nameservers": ["ns-123.awsdns-45.com", ...]}
    """
    client = _get_route53_client()
    caller_ref = str(uuid.uuid4())

    try:
        resp = await asyncio.to_thread(
            client.create_hosted_zone,
            Name=domain,
            CallerReference=caller_ref,
            HostedZoneConfig={
                "Comment": f"Meydan Free Zone — {domain}",
                "PrivateZone": False,
            },
        )

        zone_id = _clean_zone_id(resp["HostedZone"]["Id"])
        nameservers = resp["DelegationSet"]["NameServers"]

        logger.info("Created hosted zone %s for %s (NS: %s)", zone_id, domain, nameservers)
        return {"zone_id": zone_id, "nameservers": nameservers}

    except ClientError as exc:
        logger.error("Failed to create hosted zone for %s: %s", domain, exc)
        raise


async def delete_hosted_zone(zone_id: str) -> bool:
    """
    Delete a Route53 hosted zone after removing all non-NS/SOA records.

    Returns True on success.
    """
    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)

    try:
        # First, list and delete all non-NS/SOA records
        paginator = client.get_paginator("list_resource_record_sets")
        changes = []

        for page in await asyncio.to_thread(
            lambda: list(paginator.paginate(HostedZoneId=zone_id))
        ):
            for rr in page["ResourceRecordSets"]:
                if rr["Type"] in ("NS", "SOA"):
                    continue
                change = {"Action": "DELETE", "ResourceRecordSet": rr}
                changes.append(change)

        # Batch-delete records (Route53 max 1000 per batch)
        for i in range(0, len(changes), 1000):
            batch = changes[i : i + 1000]
            await asyncio.to_thread(
                client.change_resource_record_sets,
                HostedZoneId=zone_id,
                ChangeBatch={"Changes": batch},
            )
            logger.info("Deleted %d records from zone %s", len(batch), zone_id)

        # Now delete the zone itself
        await asyncio.to_thread(client.delete_hosted_zone, Id=zone_id)
        logger.info("Deleted hosted zone %s", zone_id)
        return True

    except ClientError as exc:
        logger.error("Failed to delete hosted zone %s: %s", zone_id, exc)
        raise


async def list_records(zone_id: str) -> list:
    """
    List all DNS records in a hosted zone.

    Returns list of dicts with id, name, type, value, ttl, is_alias, managed, etc.
    """
    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)

    try:
        paginator = client.get_paginator("list_resource_record_sets")
        records = []

        for page in await asyncio.to_thread(
            lambda: list(paginator.paginate(HostedZoneId=zone_id))
        ):
            for rr in page["ResourceRecordSets"]:
                name = rr["Name"]
                rtype = rr["Type"]
                is_alias = "AliasTarget" in rr

                # Determine if managed (NS/SOA or meydan-managed comment)
                managed = rtype in ("NS", "SOA")

                # Build the record entry
                entry = {
                    "id": _record_id(name, rtype),
                    "name": name,
                    "type": rtype,
                    "is_alias": is_alias,
                    "managed": managed,
                }

                if is_alias:
                    alias = rr["AliasTarget"]
                    entry["value"] = alias["DNSName"]
                    entry["alias_target"] = alias["DNSName"]
                    entry["ttl"] = None
                else:
                    values = [r["Value"] for r in rr.get("ResourceRecords", [])]
                    entry["value"] = values[0] if len(values) == 1 else "\n".join(values)
                    entry["ttl"] = rr.get("TTL", 300)

                records.append(entry)

        # Second pass: check for meydan-managed comment via test_dns_answer
        # (Route53 doesn't return comments in list_resource_record_sets,
        # so we rely on the alias/system heuristic instead)
        # Mark ALIAS records pointing to cloudfront as managed
        for rec in records:
            if rec["is_alias"] and rec.get("alias_target", "").endswith(".cloudfront.net."):
                rec["managed"] = True

        return records

    except ClientError as exc:
        logger.error("Failed to list records for zone %s: %s", zone_id, exc)
        raise


async def upsert_record(
    zone_id: str,
    name: str,
    record_type: str,
    value: str,
    ttl: int = 300,
) -> dict:
    """
    Create or update a DNS record using UPSERT.

    Handles MX priority syntax (e.g. "10 mail.example.com") and
    auto-wraps TXT values in quotes.
    """
    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)
    name = _normalize_name(name)

    if record_type not in SUPPORTED_RECORD_TYPES:
        raise ValueError(f"Unsupported record type: {record_type}")

    # Build resource records
    if record_type == "TXT":
        # Support multiple TXT values separated by newlines
        lines = [line.strip() for line in value.split("\n") if line.strip()]
        resource_records = [{"Value": _wrap_txt_value(line)} for line in lines]
    elif record_type == "MX":
        # MX requires "priority hostname" format — auto-add priority 10 if missing
        parts = value.strip().split()
        if len(parts) == 1 or not parts[0].isdigit():
            value = f"10 {value.strip()}"
        resource_records = [{"Value": value}]
    else:
        resource_records = [{"Value": value}]

    try:
        await asyncio.to_thread(
            client.change_resource_record_sets,
            HostedZoneId=zone_id,
            ChangeBatch={
                "Comment": "User DNS record",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": name,
                            "Type": record_type,
                            "TTL": ttl,
                            "ResourceRecords": resource_records,
                        },
                    }
                ],
            },
        )

        logger.info("Upserted %s record %s in zone %s", record_type, name, zone_id)

        return {
            "id": _record_id(name, record_type),
            "name": name,
            "type": record_type,
            "value": value,
            "ttl": ttl,
            "is_alias": False,
            "managed": False,
        }

    except ClientError as exc:
        logger.error("Failed to upsert %s %s in zone %s: %s", record_type, name, zone_id, exc)
        raise


async def delete_record(
    zone_id: str,
    name: str,
    record_type: str,
    value: str,
    ttl: int = 300,
) -> bool:
    """
    Delete a specific DNS record. Cannot delete NS or SOA records.

    Returns True on success.
    """
    if record_type in ("NS", "SOA"):
        raise ValueError(f"Cannot delete {record_type} records — they are managed by Route53")

    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)
    name = _normalize_name(name)

    # Build resource records matching the existing record
    if record_type == "TXT":
        lines = [line.strip() for line in value.split("\n") if line.strip()]
        resource_records = [{"Value": _wrap_txt_value(line)} for line in lines]
    else:
        resource_records = [{"Value": value}]

    try:
        await asyncio.to_thread(
            client.change_resource_record_sets,
            HostedZoneId=zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "DELETE",
                        "ResourceRecordSet": {
                            "Name": name,
                            "Type": record_type,
                            "TTL": ttl,
                            "ResourceRecords": resource_records,
                        },
                    }
                ],
            },
        )

        logger.info("Deleted %s record %s from zone %s", record_type, name, zone_id)
        return True

    except ClientError as exc:
        logger.error("Failed to delete %s %s from zone %s: %s", record_type, name, zone_id, exc)
        raise


async def create_alias_record(
    zone_id: str,
    name: str,
    target_domain: str,
    target_zone_id: str = CLOUDFRONT_HOSTED_ZONE_ID,
) -> dict:
    """
    Create an ALIAS record (Route53-specific, supports apex domains).

    Default target_zone_id is CloudFront's hosted zone ID.
    Marks the record as meydan-managed.
    """
    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)
    name = _normalize_name(name)
    target_domain = _normalize_name(target_domain)

    try:
        await asyncio.to_thread(
            client.change_resource_record_sets,
            HostedZoneId=zone_id,
            ChangeBatch={
                "Comment": "meydan-managed",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": name,
                            "Type": "A",
                            "AliasTarget": {
                                "HostedZoneId": target_zone_id,
                                "DNSName": target_domain,
                                "EvaluateTargetHealth": False,
                            },
                        },
                    }
                ],
            },
        )

        logger.info(
            "Created ALIAS record %s -> %s in zone %s (meydan-managed)",
            name, target_domain, zone_id,
        )

        return {
            "id": _record_id(name, "A"),
            "name": name,
            "type": "A",
            "value": target_domain,
            "alias_target": target_domain,
            "ttl": None,
            "is_alias": True,
            "managed": True,
        }

    except ClientError as exc:
        logger.error(
            "Failed to create ALIAS %s -> %s in zone %s: %s",
            name, target_domain, zone_id, exc,
        )
        raise


async def delete_alias_record(
    zone_id: str,
    name: str,
    target_domain: str,
    target_zone_id: str = CLOUDFRONT_HOSTED_ZONE_ID,
) -> bool:
    """Delete an ALIAS A record from Route53."""
    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)
    name = _normalize_name(name)
    target_domain = _normalize_name(target_domain)

    try:
        await asyncio.to_thread(
            client.change_resource_record_sets,
            HostedZoneId=zone_id,
            ChangeBatch={
                "Comment": "meydan-managed cleanup",
                "Changes": [
                    {
                        "Action": "DELETE",
                        "ResourceRecordSet": {
                            "Name": name,
                            "Type": "A",
                            "AliasTarget": {
                                "HostedZoneId": target_zone_id,
                                "DNSName": target_domain,
                                "EvaluateTargetHealth": False,
                            },
                        },
                    }
                ],
            },
        )
        logger.info("Deleted ALIAS record %s -> %s in zone %s", name, target_domain, zone_id)
        return True
    except ClientError as exc:
        logger.warning("Failed to delete ALIAS %s in zone %s: %s", name, zone_id, exc)
        return False


async def create_acm_validation_records(
    zone_id: str,
    validation_records: list,
) -> bool:
    """
    Batch-create all ACM CNAME validation records.

    Each record in validation_records: {"name": "...", "type": "CNAME", "value": "..."}
    Marks all as meydan-managed.

    Returns True on success.
    """
    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)

    changes = []
    for rec in validation_records:
        name = _normalize_name(rec["name"])
        value = _normalize_name(rec["value"])

        changes.append({
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": name,
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [{"Value": value}],
            },
        })

    if not changes:
        logger.warning("No ACM validation records to create for zone %s", zone_id)
        return True

    try:
        await asyncio.to_thread(
            client.change_resource_record_sets,
            HostedZoneId=zone_id,
            ChangeBatch={
                "Comment": "meydan-managed",
                "Changes": changes,
            },
        )

        logger.info(
            "Created %d ACM validation records in zone %s (meydan-managed)",
            len(changes), zone_id,
        )
        return True

    except ClientError as exc:
        logger.error(
            "Failed to create ACM validation records in zone %s: %s",
            zone_id, exc,
        )
        raise


async def get_nameservers(zone_id: str) -> list:
    """
    Get the NS records for a hosted zone.

    Returns list of nameserver strings (e.g. ["ns-123.awsdns-45.com", ...]).
    """
    client = _get_route53_client()
    zone_id = _clean_zone_id(zone_id)

    try:
        resp = await asyncio.to_thread(
            client.get_hosted_zone,
            Id=zone_id,
        )

        nameservers = resp["DelegationSet"]["NameServers"]
        logger.info("Nameservers for zone %s: %s", zone_id, nameservers)
        return nameservers

    except ClientError as exc:
        logger.error("Failed to get nameservers for zone %s: %s", zone_id, exc)
        raise
