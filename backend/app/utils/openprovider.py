"""
OpenProvider API client — domain search, registration, and management.

Docs: https://docs.openprovider.com/doc/all
Auth: Bearer token via /auth/login endpoint
"""

import logging
import os
import time

import httpx

from app.utils import sanitize_log

logger = logging.getLogger(__name__)

_token: str | None = None
_token_expires: float = 0


def _config():
    return {
        "api_url": os.getenv("OPENPROVIDER_API_URL", "https://api.openprovider.eu/v1beta"),
        "username": os.getenv("OPENPROVIDER_USERNAME", ""),
        "password": os.getenv("OPENPROVIDER_PASSWORD", ""),
    }


async def _get_token() -> str:
    """Authenticate and cache bearer token (valid ~48h)."""
    global _token, _token_expires
    if _token and time.time() < _token_expires:
        return _token

    cfg = _config()
    last_err = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{cfg['api_url']}/auth/login",
                    json={"username": cfg["username"], "password": cfg["password"], "ip": "0.0.0.0"},
                )
                resp.raise_for_status()
                data = resp.json()

            _token = data["data"]["token"]
            _token_expires = time.time() + 47 * 3600
            logger.info("[OpenProvider] Authenticated successfully")
            return _token
        except Exception as e:
            last_err = e
            logger.warning("[OpenProvider] Auth attempt %d failed: %s", attempt + 1, e)
            if attempt < 2:
                import asyncio
                await asyncio.sleep(1 * (attempt + 1))

    raise last_err


async def _request(method: str, path: str, **kwargs) -> dict:
    """Make an authenticated API request."""
    token = await _get_token()
    cfg = _config()
    url = f"{cfg['api_url']}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.request(method, url, headers=headers, **kwargs)
        body = resp.json()

        if resp.status_code >= 400:
            code = body.get("code", resp.status_code)
            desc = body.get("desc", body.get("message", "Unknown error"))
            logger.error("[OpenProvider] %s %s → %s: %s", method, path, code, desc)
            raise OpenProviderError(code, desc)

    return body.get("data", body)


class OpenProviderError(Exception):
    def __init__(self, code, message=""):
        self.code = code
        super().__init__(f"OpenProvider error {code}: {message}")


# Cache: "sld.tld" → numeric domain ID
_domain_id_cache: dict[str, int] = {}


async def _resolve_domain_id(domain_name: str, tld: str) -> int:
    """Resolve sld + tld to OpenProvider numeric domain ID.

    Checks cache first, then queries the list endpoint with a filter.
    """
    key = f"{domain_name}.{tld}"
    if key in _domain_id_cache:
        return _domain_id_cache[key]

    data = await _request(
        "GET", "/domains",
        params={"domain_name_pattern": domain_name, "extension": tld, "limit": 1},
    )
    results = data.get("results", [])
    if not results:
        raise OpenProviderError(0, f"Domain {key} not found in OpenProvider account")

    domain_id = results[0]["id"]
    _domain_id_cache[key] = domain_id
    logger.info("[OpenProvider] Resolved %s → ID %d", sanitize_log(key), domain_id)
    return domain_id


def cache_domain_id(domain_name: str, tld: str, domain_id: int):
    """Pre-cache a domain ID (called after registration)."""
    _domain_id_cache[f"{domain_name}.{tld}"] = domain_id


# ═══════════════════════════════════════════════════════════════
# Domain Search / Availability
# ═══════════════════════════════════════════════════════════════


async def check_domain_availability(domain_name: str, extensions: list[str] | None = None) -> list[dict]:
    """Check if a domain is available for registration.

    Args:
        domain_name: The SLD (second-level domain) without TLD, e.g. "mybusiness"
        extensions: List of TLDs to check, e.g. ["com", "ae", "net"]. Defaults to common ones.

    Returns:
        List of {domain, tld, status, price} dicts.
        status: "free" (available), "active" (taken), or "error"
    """
    if extensions is None:
        # 15 popular TLDs across business / regional / modern categories so the
        # search popup feels rich (was 6 before).
        extensions = [
            "com", "ae", "net", "org", "io",
            "co", "app", "shop", "online", "store",
            "site", "tech", "dev", "me", "xyz",
        ]

    # Build domains array for batch check
    domains = [{"name": domain_name, "extension": ext} for ext in extensions]

    data = await _request("POST", "/domains/check", json={"domains": domains, "with_price": True})

    results = []
    for item in data.get("results", []):
        # API returns "domain": "meydantest.com" (full string)
        domain_str = item.get("domain", "")
        status = item.get("status", "error")

        # Split domain into SLD and TLD
        if "." in domain_str:
            sld, tld = domain_str.split(".", 1)
        else:
            sld, tld = domain_str, ""

        # Extract pricing — API returns {price: {product: {price, currency}, reseller: {price, currency}}}
        price = None
        if status == "free" and "price" in item:
            reseller_price = item["price"].get("reseller", item["price"].get("product", {}))
            price = {
                "currency": reseller_price.get("currency", "USD"),
                "amount": reseller_price.get("price", 0),
                "period": 1,
            }

        results.append({
            "domain": domain_str,
            "sld": sld,
            "tld": tld,
            "status": status,  # "free" or "active"
            "price": price,
        })

    return results


async def get_domain_price(tld: str) -> dict | None:
    """Get registration price for a TLD."""
    try:
        data = await _request("GET", f"/prices/domains/{tld}")
        product = data.get("product", data)
        prices = product.get("prices", {})
        create_price = prices.get("create", [{}])
        if isinstance(create_price, list) and create_price:
            return {
                "currency": create_price[0].get("currency", "USD"),
                "amount": create_price[0].get("price", 0),
                "period": create_price[0].get("period", 1),
            }
        return None
    except Exception:
        return None


async def suggest_domains(keyword: str, limit: int = 10) -> list[dict]:
    """Get domain name suggestions based on a keyword."""
    try:
        data = await _request("POST", "/dns/nameservers/suggest", json={
            "keyword": keyword,
            "limit": limit,
        })
        return data.get("results", [])
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# Default Contact Handle (cached)
# ═══════════════════════════════════════════════════════════════

_default_contact_handle: str | None = None


async def _get_or_create_default_contact() -> str:
    """Get or create a default Meydan Free Zone contact handle for domain registration."""
    global _default_contact_handle
    if _default_contact_handle:
        return _default_contact_handle

    # Try to find existing contacts first
    try:
        data = await _request("GET", "/customers", params={"limit": 1, "company_name": "Meydan Free Zone"})
        results = data.get("results", [])
        if results:
            handle = results[0].get("handle", results[0].get("id", ""))
            if handle:
                _default_contact_handle = str(handle)
                logger.info("[OpenProvider] Using existing contact handle: %s", _default_contact_handle)
                return _default_contact_handle
    except Exception as e:
        logger.warning("[OpenProvider] Could not search contacts: %s", e)

    # Create a new default contact
    try:
        result = await create_contact(
            first_name=os.getenv("OPENPROVIDER_CONTACT_FIRST_NAME", "Meydan"),
            last_name=os.getenv("OPENPROVIDER_CONTACT_LAST_NAME", "Free Zone"),
            company_name=os.getenv("OPENPROVIDER_CONTACT_COMPANY", "Meydan Free Zone"),
            email=os.getenv("OPENPROVIDER_CONTACT_EMAIL", "domains@meydanfz.ae"),
            phone=os.getenv("OPENPROVIDER_CONTACT_PHONE", "45550000"),
            address={
                "street": os.getenv("OPENPROVIDER_CONTACT_STREET", "Meydan Hotel"),
                "number": os.getenv("OPENPROVIDER_CONTACT_NUMBER", "1"),
                "zipcode": os.getenv("OPENPROVIDER_CONTACT_ZIP", "00000"),
                "city": "Dubai",
                "state": "Dubai",
                "country": "AE",
            },
        )
        _default_contact_handle = str(result["handle"])
        logger.info("[OpenProvider] Created default contact handle: %s", _default_contact_handle)
        return _default_contact_handle
    except Exception as e:
        raise OpenProviderError(f"Failed to create contact handle: {e}") from e


# ═══════════════════════════════════════════════════════════════
# Domain Registration
# ═══════════════════════════════════════════════════════════════


async def register_domain(
    domain_name: str,
    tld: str,
    period: int = 1,
    owner_contact: dict | None = None,
    nameservers: list[str] | None = None,
    auto_renew: bool = True,
) -> dict:
    """Register a new domain.

    Args:
        domain_name: SLD (e.g. "mybusiness")
        tld: Extension (e.g. "com", "ae")
        period: Registration period in years (default 1)
        owner_contact: Contact details dict (name, email, phone, address, etc.)
        nameservers: Custom nameservers. If None, uses OpenProvider defaults.
        auto_renew: Whether to auto-renew.

    Returns:
        Dict with domain ID, status, and registration details.
    """
    payload = {
        "domain": {"name": domain_name, "extension": tld},
        "period": period,
        "autorenew": "on" if auto_renew else "off",
    }

    # Owner contact (required for registration)
    if owner_contact and owner_contact.get("handle"):
        handle = owner_contact["handle"]
    else:
        # Auto-create a default contact handle for Meydan Free Zone
        handle = await _get_or_create_default_contact()

    payload["owner_handle"] = handle
    payload["admin_handle"] = handle
    payload["tech_handle"] = handle
    payload["billing_handle"] = handle

    # Custom nameservers (for pointing to Route53)
    if nameservers:
        payload["name_servers"] = [{"name": ns} for ns in nameservers]

    data = await _request("POST", "/domains", json=payload)

    domain_id = data.get("id")
    if domain_id:
        cache_domain_id(domain_name, tld, domain_id)

    return {
        "id": domain_id,
        "domain": f"{domain_name}.{tld}",
        "status": data.get("status", "ACT"),
        "registered": True,
        "owner_handle": handle,
    }


# ═══════════════════════════════════════════════════════════════
# Domain Management
# ═══════════════════════════════════════════════════════════════


async def get_domain(domain_name: str, tld: str) -> dict:
    """Get details of a registered domain."""
    domain_id = await _resolve_domain_id(domain_name, tld)
    data = await _request("GET", f"/domains/{domain_id}")
    return data


async def update_nameservers(domain_name: str, tld: str, nameservers: list[str]) -> dict:
    """Update the nameservers for a registered domain.

    This is the key step: after registering through OpenProvider,
    we point nameservers to our Route53 hosted zone.
    """
    domain_id = await _resolve_domain_id(domain_name, tld)
    payload = {
        "name_servers": [{"name": ns} for ns in nameservers],
    }
    data = await _request("PUT", f"/domains/{domain_id}", json=payload)
    logger.info("[OpenProvider] Nameservers updated for %s.%s → %s", sanitize_log(domain_name), sanitize_log(tld), sanitize_log(str(nameservers)))
    return data


async def list_domains(limit: int = 100, offset: int = 0) -> dict:
    """List all domains in the reseller account."""
    data = await _request("GET", "/domains", params={"limit": limit, "offset": offset})
    return data


async def renew_domain(domain_name: str, tld: str, period: int = 1) -> dict:
    """Renew a domain for additional years."""
    domain_id = await _resolve_domain_id(domain_name, tld)
    data = await _request("POST", f"/domains/{domain_id}/renew", json={"period": period})
    return data


async def transfer_lock(domain_name: str, tld: str, locked: bool = True) -> dict:
    """Enable or disable transfer lock."""
    domain_id = await _resolve_domain_id(domain_name, tld)
    data = await _request("PUT", f"/domains/{domain_id}", json={
        "is_locked": locked,
    })
    return data


# ═══════════════════════════════════════════════════════════════
# Contact Management (for .ae TDRA compliance)
# ═══════════════════════════════════════════════════════════════


async def create_contact(
    first_name: str,
    last_name: str,
    company_name: str,
    email: str,
    phone: str,
    address: dict,
) -> dict:
    """Create a contact handle for domain registration.

    Args:
        address: {"street": "...", "city": "...", "state": "...", "zipcode": "...", "country": "AE"}

    Returns:
        {"handle": "XX000000-XX"} — the contact handle ID
    """
    payload = {
        "name": {"first_name": first_name, "last_name": last_name},
        "company_name": company_name,
        "email": email,
        "phone": {"country_code": "+971", "area_code": phone[:2] if len(phone) > 2 else phone, "subscriber_number": phone[2:] if len(phone) > 2 else ""},
        "address": {
            "street": address.get("street", ""),
            "number": address.get("number", ""),
            "zipcode": address.get("zipcode", ""),
            "city": address.get("city", "Dubai"),
            "state": address.get("state", "Dubai"),
            "country": address.get("country", "AE"),
        },
    }
    data = await _request("POST", "/customers", json=payload)
    return {"handle": data.get("handle", data.get("id", ""))}


async def get_contact(handle: str) -> dict:
    """Get contact details."""
    return await _request("GET", f"/customers/{handle}")


async def update_contact(handle: str, **fields) -> dict:
    """Update an existing contact handle's details.

    Accepts: first_name, last_name, company_name, email, phone, address (dict).
    """
    payload = {}
    if "first_name" in fields or "last_name" in fields:
        payload["name"] = {}
        if "first_name" in fields:
            payload["name"]["first_name"] = fields["first_name"]
        if "last_name" in fields:
            payload["name"]["last_name"] = fields["last_name"]
    if "company_name" in fields:
        payload["company_name"] = fields["company_name"]
    if "email" in fields:
        payload["email"] = fields["email"]
    if "phone" in fields:
        phone_raw = fields["phone"].strip()
        # OpenProvider REQUIRES area_code — can't be empty.
        # Format: country_code="+971", area_code="56", subscriber_number="1457066"
        country_code = "+971"
        number_part = phone_raw
        if phone_raw.startswith("+"):
            parts = phone_raw.split(None, 1)
            if len(parts) == 2:
                country_code = parts[0]
                number_part = parts[1]
            else:
                # No space — extract country code (+XXX for 3-digit, +XX for 2, +X for 1)
                for cc_len in (4, 3, 2):  # +971, +44, +1
                    if len(phone_raw) > cc_len:
                        country_code = phone_raw[:cc_len]
                        number_part = phone_raw[cc_len:]
                        break
        elif phone_raw.startswith("00"):
            country_code = "+" + phone_raw[2:5]
            number_part = phone_raw[5:]
        # Strip spaces/dashes
        number_part = number_part.replace(" ", "").replace("-", "")
        # Split into area_code (first 2 digits) + subscriber_number (rest)
        if len(number_part) > 2:
            area_code = number_part[:2]
            subscriber = number_part[2:]
        else:
            area_code = number_part
            subscriber = ""
        payload["phone"] = {"country_code": country_code, "area_code": area_code, "subscriber_number": subscriber}
    if "address" in fields:
        payload["address"] = fields["address"]

    if not payload:
        return {"handle": handle}

    await _request("PUT", f"/customers/{handle}", json=payload)
    return {"handle": handle, "updated": True}


async def reassign_domain_contact(
    domain_name: str, tld: str, old_handle: str, **new_fields
) -> dict:
    """Change domain owner by creating a new contact handle and reassigning.

    OpenProvider blocks name edits on contacts linked to active domains,
    so we: (1) fetch existing contact, (2) create a new one with merged fields,
    (3) reassign domain owner/admin/tech/billing to the new handle.

    Returns {"new_handle": "XX000000-XX"}.
    """
    # 1. Fetch existing contact to preserve fields not being changed
    existing = await _request("GET", f"/customers/{old_handle}")
    existing_name = existing.get("name", {})
    existing_phone = existing.get("phone", {})
    existing_address = existing.get("address", {})

    # 2. Merge: new fields override existing
    first_name = new_fields.get("first_name", existing_name.get("first_name", ""))
    last_name = new_fields.get("last_name", existing_name.get("last_name", ""))
    company = new_fields.get("company_name", existing.get("company_name", ""))
    email = new_fields.get("email", existing.get("email", ""))
    address = new_fields.get("address", existing_address)

    # Phone — use new if provided, else reconstruct from existing
    if "phone" in new_fields:
        phone_str = new_fields["phone"]
    else:
        cc = existing_phone.get("country_code", "+971")
        ac = existing_phone.get("area_code", "")
        sn = existing_phone.get("subscriber_number", "")
        phone_str = f"{cc} {ac}{sn}"

    # Parse phone into OpenProvider format
    phone_cc = "+971"
    number_part = phone_str.strip()
    if number_part.startswith("+"):
        parts = number_part.split(None, 1)
        if len(parts) == 2:
            phone_cc = parts[0]
            number_part = parts[1]
        else:
            for cc_len in (4, 3, 2):
                if len(number_part) > cc_len:
                    phone_cc = number_part[:cc_len]
                    number_part = number_part[cc_len:]
                    break
    number_part = number_part.replace(" ", "").replace("-", "")
    area_code = number_part[:2] if len(number_part) > 2 else number_part
    subscriber = number_part[2:] if len(number_part) > 2 else ""

    # 3. Create new contact handle
    payload = {
        "name": {"first_name": first_name, "last_name": last_name},
        "company_name": company,
        "email": email,
        "phone": {"country_code": phone_cc, "area_code": area_code, "subscriber_number": subscriber},
        "address": {
            "street": address.get("street", ""),
            "number": address.get("number", ""),
            "zipcode": address.get("zipcode", ""),
            "city": address.get("city", "Dubai"),
            "state": address.get("state", ""),
            "country": address.get("country", "AE"),
        },
    }
    data = await _request("POST", "/customers", json=payload)
    new_handle = data.get("handle", data.get("id", ""))
    if not new_handle:
        raise OpenProviderError(0, "Failed to create new contact handle")

    logger.info("[OpenProvider] Created new contact handle %s for domain %s.%s", new_handle, domain_name, tld)

    # 4. Reassign domain owner to the new handle
    domain_id = await _resolve_domain_id(domain_name, tld)
    await _request("PUT", f"/domains/{domain_id}", json={
        "owner_handle": new_handle,
        "admin_handle": new_handle,
        "tech_handle": new_handle,
        "billing_handle": new_handle,
    })
    logger.info("[OpenProvider] Reassigned %s.%s owner from %s to %s", domain_name, tld, old_handle, new_handle)

    return {"new_handle": new_handle}


# ═══════════════════════════════════════════════════════════════
# Domain Settings (WHOIS privacy, auto-renew, status sync)
# ═══════════════════════════════════════════════════════════════


async def set_whois_privacy(domain_name: str, tld: str, enabled: bool) -> dict:
    """Enable or disable WHOIS privacy."""
    domain_id = await _resolve_domain_id(domain_name, tld)
    data = await _request("PUT", f"/domains/{domain_id}", json={
        "is_private_whois_enabled": enabled,
    })
    logger.info("[OpenProvider] WHOIS privacy %s for %s.%s", "enabled" if enabled else "disabled", domain_name, tld)
    return data


async def set_auto_renew(domain_name: str, tld: str, enabled: bool) -> dict:
    """Toggle auto-renew on/off."""
    domain_id = await _resolve_domain_id(domain_name, tld)
    data = await _request("PUT", f"/domains/{domain_id}", json={
        "autorenew": "on" if enabled else "off",
    })
    logger.info("[OpenProvider] Auto-renew %s for %s.%s", "on" if enabled else "off", domain_name, tld)
    return data


async def sync_domain_status(domain_name: str, tld: str) -> dict:
    """Pull full live status from OpenProvider and return normalized dict."""
    data = await get_domain(domain_name, tld)

    # Parse nameservers
    ns_list = []
    for ns in data.get("name_servers", []):
        if isinstance(ns, dict):
            ns_list.append(ns.get("name", ""))
        else:
            ns_list.append(str(ns))

    # Parse contacts
    owner_handle = None
    if data.get("owner_handle"):
        owner_handle = str(data["owner_handle"])

    return {
        "status": data.get("status", "unknown"),
        "expiration_date": data.get("expiration_date"),
        "renewal_date": data.get("renewal_date"),
        "autorenew": data.get("autorenew") == "on",
        "is_locked": data.get("is_locked", False),
        "whois_privacy": data.get("is_private_whois_enabled", False),
        "nameservers": ns_list,
        "owner_handle": owner_handle,
        "admin_handle": str(data.get("admin_handle", "")),
        "tech_handle": str(data.get("tech_handle", "")),
    }


# ═══════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════


async def verify_credentials() -> bool:
    """Verify OpenProvider credentials are valid."""
    try:
        await _get_token()
        return True
    except Exception as e:
        logger.error("[OpenProvider] Credential verification failed: %s", e)
        return False
