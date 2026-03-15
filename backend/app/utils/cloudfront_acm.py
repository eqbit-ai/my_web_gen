"""
CloudFront + ACM utility — manages custom domain connections for S3-hosted static websites.

Creates CloudFront distributions with ACM SSL certificates so tenants can use
their own domains (e.g. mybusiness.ae) pointing to their S3-deployed site.

ACM certificates are always provisioned in us-east-1 (CloudFront requirement).
CloudFront origins use the S3 *website* endpoint (custom origin, HTTP-only)
so that S3 index-document and error-document redirects work correctly.
"""

import asyncio
import logging
import os
import uuid
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _bucket() -> str:
    return os.getenv("AWS_S3_DEPLOY_BUCKET", "")


def _region() -> str:
    return os.getenv("AWS_REGION", "me-central-1")


def _aws_creds() -> dict:
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    }


def _acm_client():
    """ACM client pinned to us-east-1 (required for CloudFront certificates)."""
    return boto3.client("acm", region_name="us-east-1", **_aws_creds())


def _cf_client():
    """CloudFront is a global service — region is irrelevant."""
    return boto3.client("cloudfront", **_aws_creds())


def _s3_website_endpoint() -> str:
    """S3 website endpoint for the deploy bucket (custom origin domain)."""
    return f"{_bucket()}.s3-website.{_region()}.amazonaws.com"


def _is_www(domain: str) -> bool:
    return domain.lower().startswith("www.")


def _root_domain(domain: str) -> str:
    """Strip leading 'www.' if present."""
    return domain[4:] if _is_www(domain) else domain


# ---------------------------------------------------------------------------
# 1. Request ACM certificate
# ---------------------------------------------------------------------------

async def request_certificate(domain: str) -> dict:
    """
    Request a public ACM certificate (DNS-validated) in us-east-1.

    If *domain* does not start with ``www.``, the cert also covers ``www.<domain>``
    via SubjectAlternativeNames.

    Returns::

        {
            "arn": "arn:aws:acm:us-east-1:...",
            "validation_records": [
                {"name": "_abc.example.com.", "type": "CNAME", "value": "_def.acm-validations.aws."}
            ]
        }
    """

    def _request():
        client = _acm_client()
        sans = [domain]
        if not _is_www(domain):
            sans.append(f"www.{domain}")

        resp = client.request_certificate(
            DomainName=domain,
            SubjectAlternativeNames=sans,
            ValidationMethod="DNS",
            IdempotencyToken=uuid.uuid4().hex[:32],
        )
        arn = resp["CertificateArn"]
        logger.info("ACM certificate requested: %s for %s", arn, domain)

        # ACM needs a moment before DomainValidationOptions are populated
        waiter = client.get_waiter("certificate_validated")
        # We won't actually *wait* for full validation here — just poll once
        # to grab the CNAME records the user needs to create.
        import time
        validation_records = []
        for _ in range(10):
            desc = client.describe_certificate(CertificateArn=arn)
            options = desc["Certificate"].get("DomainValidationOptions", [])
            if options and "ResourceRecord" in options[0]:
                for opt in options:
                    rr = opt.get("ResourceRecord", {})
                    if rr:
                        validation_records.append({
                            "name": rr["Name"],
                            "type": rr["Type"],
                            "value": rr["Value"],
                        })
                break
            time.sleep(2)

        return {"arn": arn, "validation_records": validation_records}

    try:
        return await asyncio.to_thread(_request)
    except ClientError as exc:
        logger.error("ACM request_certificate failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# 2. Check certificate status
# ---------------------------------------------------------------------------

async def check_certificate_status(arn: str) -> dict:
    """
    Describe an ACM certificate and return its current status.

    Returns::

        {"status": "PENDING_VALIDATION" | "ISSUED" | "FAILED", "domain": "example.com"}
    """

    def _check():
        client = _acm_client()
        desc = client.describe_certificate(CertificateArn=arn)
        cert = desc["Certificate"]
        return {
            "status": cert["Status"],
            "domain": cert["DomainName"],
        }

    try:
        return await asyncio.to_thread(_check)
    except ClientError as exc:
        logger.error("ACM describe_certificate failed for %s: %s", arn, exc)
        raise


# ---------------------------------------------------------------------------
# 3. Create CloudFront distribution
# ---------------------------------------------------------------------------

async def create_distribution(
    domain: str,
    s3_project_name: str,
    acm_cert_arn: str,
) -> dict:
    """
    Create a CloudFront distribution that serves ``s3://<bucket>/<s3_project_name>/``
    behind a custom domain with HTTPS (ACM certificate).

    Returns::

        {
            "distribution_id": "E1234...",
            "domain_name": "d1234.cloudfront.net",
            "status": "InProgress"
        }
    """

    def _create():
        client = _cf_client()
        origin_domain = _s3_website_endpoint()
        caller_ref = str(uuid.uuid4())

        # Build aliases list
        aliases = [domain]
        if not _is_www(domain):
            aliases.append(f"www.{domain}")

        config = {
            "CallerReference": caller_ref,
            "Comment": f"Meydan site: {domain} -> {s3_project_name}",
            "Enabled": True,
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": f"S3Website-{s3_project_name}",
                        "DomainName": origin_domain,
                        "OriginPath": f"/{s3_project_name}",
                        "CustomOriginConfig": {
                            "HTTPPort": 80,
                            "HTTPSPort": 443,
                            "OriginProtocolPolicy": "http-only",
                            "OriginSslProtocols": {
                                "Quantity": 1,
                                "Items": ["TLSv1.2"],
                            },
                        },
                        "CustomHeaders": {
                            "Quantity": 0,
                        },
                    }
                ],
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": f"S3Website-{s3_project_name}",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"],
                    "CachedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"],
                    },
                },
                "Compress": True,
                "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",  # CachingOptimized
                "ForwardedValues": None,  # Not needed when CachePolicyId is set
            },
            "Aliases": {
                "Quantity": len(aliases),
                "Items": aliases,
            },
            "DefaultRootObject": "index.html",
            "CustomErrorResponses": {
                "Quantity": 1,
                "Items": [
                    {
                        "ErrorCode": 404,
                        "ResponsePagePath": "/index.html",
                        "ResponseCode": "200",
                        "ErrorCachingMinTTL": 10,
                    }
                ],
            },
            "PriceClass": "PriceClass_200",
            "ViewerCertificate": {
                "ACMCertificateArn": acm_cert_arn,
                "SSLSupportMethod": "sni-only",
                "MinimumProtocolVersion": "TLSv1.2_2021",
                "CloudFrontDefaultCertificate": False,
            },
            "HttpVersion": "http2and3",
            "IsIPV6Enabled": True,
        }

        # CachePolicyId and ForwardedValues are mutually exclusive —
        # remove ForwardedValues when using a managed cache policy.
        del config["DefaultCacheBehavior"]["ForwardedValues"]

        resp = client.create_distribution(DistributionConfig=config)
        dist = resp["Distribution"]
        logger.info(
            "CloudFront distribution created: %s (%s) for %s",
            dist["Id"],
            dist["DomainName"],
            domain,
        )
        return {
            "distribution_id": dist["Id"],
            "domain_name": dist["DomainName"],
            "status": dist["Status"],
        }

    try:
        return await asyncio.to_thread(_create)
    except ClientError as exc:
        logger.error("CloudFront create_distribution failed for %s: %s", domain, exc)
        raise


# ---------------------------------------------------------------------------
# 4. Get distribution status
# ---------------------------------------------------------------------------

async def get_distribution_status(distribution_id: str) -> dict:
    """
    Poll a CloudFront distribution's deploy status.

    Returns::

        {"status": "InProgress" | "Deployed", "domain_name": "d1234.cloudfront.net"}
    """

    def _status():
        client = _cf_client()
        resp = client.get_distribution(Id=distribution_id)
        dist = resp["Distribution"]
        return {
            "status": dist["Status"],
            "domain_name": dist["DomainName"],
        }

    try:
        return await asyncio.to_thread(_status)
    except ClientError as exc:
        logger.error("CloudFront get_distribution failed for %s: %s", distribution_id, exc)
        raise


# ---------------------------------------------------------------------------
# 5. Disable distribution
# ---------------------------------------------------------------------------

async def disable_distribution(distribution_id: str) -> bool:
    """
    Disable a CloudFront distribution (must be done before deletion).

    Returns True on success.
    """

    def _disable():
        client = _cf_client()
        # Fetch current config + ETag
        resp = client.get_distribution_config(Id=distribution_id)
        config = resp["DistributionConfig"]
        etag = resp["ETag"]

        if not config["Enabled"]:
            logger.info("Distribution %s is already disabled", distribution_id)
            return True

        config["Enabled"] = False
        client.update_distribution(
            Id=distribution_id,
            DistributionConfig=config,
            IfMatch=etag,
        )
        logger.info("Distribution %s disabled", distribution_id)
        return True

    try:
        return await asyncio.to_thread(_disable)
    except ClientError as exc:
        logger.error("CloudFront disable_distribution failed for %s: %s", distribution_id, exc)
        raise


# ---------------------------------------------------------------------------
# 6. Delete distribution
# ---------------------------------------------------------------------------

async def delete_distribution(distribution_id: str) -> bool:
    """
    Delete a CloudFront distribution. The distribution must already be disabled
    and in ``Deployed`` status.

    Returns True on success.
    """

    def _delete():
        client = _cf_client()
        # Need current ETag for deletion
        resp = client.get_distribution_config(Id=distribution_id)
        etag = resp["ETag"]
        config = resp["DistributionConfig"]

        if config["Enabled"]:
            raise RuntimeError(
                f"Distribution {distribution_id} is still enabled. "
                "Disable it first with disable_distribution()."
            )

        client.delete_distribution(Id=distribution_id, IfMatch=etag)
        logger.info("Distribution %s deleted", distribution_id)
        return True

    try:
        return await asyncio.to_thread(_delete)
    except ClientError as exc:
        logger.error("CloudFront delete_distribution failed for %s: %s", distribution_id, exc)
        raise


# ---------------------------------------------------------------------------
# 7. Delete ACM certificate
# ---------------------------------------------------------------------------

async def delete_certificate(arn: str) -> bool:
    """
    Delete an ACM certificate. The cert must not be in use by any distribution.

    Returns True on success.
    """

    def _delete():
        client = _acm_client()
        client.delete_certificate(CertificateArn=arn)
        logger.info("ACM certificate deleted: %s", arn)
        return True

    try:
        return await asyncio.to_thread(_delete)
    except ClientError as exc:
        logger.error("ACM delete_certificate failed for %s: %s", arn, exc)
        raise


# ---------------------------------------------------------------------------
# 8. Get DNS records the user must create
# ---------------------------------------------------------------------------

def get_dns_records(
    domain: str,
    cloudfront_domain: str,
    validation_records: list,
) -> list:
    """
    Build the full list of DNS records the tenant must add at their registrar.

    Returns a list of dicts::

        [
            {"type": "CNAME", "name": "_acme.example.com.", "value": "_xyz.acm.aws.", "purpose": "SSL Validation"},
            {"type": "CNAME", "name": "example.com",        "value": "d1234.cloudfront.net", "purpose": "Website"},
            {"type": "CNAME", "name": "www.example.com",    "value": "d1234.cloudfront.net", "purpose": "Website"},
        ]
    """
    records: list[dict] = []

    # ACM validation CNAMEs
    for vr in validation_records:
        records.append({
            "type": vr.get("type", "CNAME"),
            "name": vr["name"],
            "value": vr["value"],
            "purpose": "SSL Validation",
        })

    # Website CNAME: domain → CloudFront
    records.append({
        "type": "CNAME",
        "name": domain,
        "value": cloudfront_domain,
        "purpose": "Website",
    })

    # www variant (only if the primary domain is NOT already www)
    if not _is_www(domain):
        records.append({
            "type": "CNAME",
            "name": f"www.{domain}",
            "value": cloudfront_domain,
            "purpose": "Website",
        })

    return records
