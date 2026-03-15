"""
Cloudflare API client — Pages deployment, DNS zone management, cache purge.

Uses Cloudflare API v4:
  - Pages: Direct Upload for static site deployment
  - DNS: Zone + record management
  - SSL: Auto-provisioned by Cloudflare (no action needed)

Docs: https://developers.cloudflare.com/api/
"""

import hashlib
import json
import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

CF_API_BASE = "https://api.cloudflare.com/client/v4"


def _token() -> str:
    return os.getenv("CLOUDFLARE_API_TOKEN", "")


def _account_id() -> str:
    return os.getenv("CLOUDFLARE_ACCOUNT_ID", "")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
    }


def _upload_headers() -> dict:
    """Headers for multipart uploads (no Content-Type — httpx sets boundary)."""
    return {
        "Authorization": f"Bearer {_token()}",
    }


def _sanitize_project_name(name: str) -> str:
    """Convert a site name to a valid CF Pages project name (lowercase, hyphens, max 58 chars)."""
    slug = re.sub(r"[^a-z0-9-]", "-", name.lower().strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:58] or "site"


# ── Pages Project Management ────────────────────────────────────────────


async def create_pages_project(project_name: str) -> dict:
    """Create a new Cloudflare Pages project (Direct Upload type).

    Returns the project dict from CF API or raises on error.
    """
    url = f"{CF_API_BASE}/accounts/{_account_id()}/pages/projects"
    payload = {
        "name": project_name,
        "production_branch": "main",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        data = resp.json()

    if not data.get("success"):
        errors = data.get("errors", [])
        # Project already exists — that's fine, return it
        if any(e.get("code") == 8000007 for e in errors):
            logger.info("Pages project '%s' already exists, reusing", project_name)
            return await get_pages_project(project_name)
        raise RuntimeError(f"Failed to create Pages project: {errors}")

    logger.info("Created Pages project: %s", project_name)
    return data["result"]


async def get_pages_project(project_name: str) -> dict:
    """Get details of an existing Pages project."""
    url = f"{CF_API_BASE}/accounts/{_account_id()}/pages/projects/{project_name}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_headers())
        data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"Pages project '{project_name}' not found: {data.get('errors')}")
    return data["result"]


async def delete_pages_project(project_name: str) -> bool:
    """Delete a Pages project. Returns True on success."""
    url = f"{CF_API_BASE}/accounts/{_account_id()}/pages/projects/{project_name}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.delete(url, headers=_headers())
        data = resp.json()
    return data.get("success", False)


# ── Pages Direct Upload Deployment ──────────────────────────────────────


async def deploy_to_pages(
    project_name: str,
    files: dict[str, str | bytes],
    branch: str = "main",
) -> dict:
    """Deploy static files to Cloudflare Pages via Direct Upload.

    CF Pages Direct Upload requires a `manifest` JSON field that maps
    each file path (e.g. "/index.html") to its content hash. The actual
    file content is sent as separate multipart form fields keyed by the
    same content hash.

    Args:
        project_name: CF Pages project name (must already exist).
        files: dict mapping file path (e.g. "/index.html") to content.
        branch: deployment branch (default "main" for production).

    Returns:
        Deployment result dict with url, id, etc.
    """
    url = f"{CF_API_BASE}/accounts/{_account_id()}/pages/projects/{project_name}/deployments"

    # Build manifest: {"/index.html": "<sha256hash>", ...}
    # And collect file blobs keyed by hash
    manifest = {}
    hash_to_content: dict[str, bytes] = {}

    for path, content in files.items():
        normalized = path if path.startswith("/") else f"/{path}"
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        manifest[normalized] = content_hash
        hash_to_content[content_hash] = content_bytes

    # Build multipart form
    multipart_files = []

    # The manifest field — JSON string mapping paths to hashes
    manifest_json = json.dumps(manifest)
    multipart_files.append(("manifest", (None, manifest_json, "application/json")))

    # Each unique file, keyed by its content hash
    for content_hash, content_bytes in hash_to_content.items():
        multipart_files.append((content_hash, (content_hash, content_bytes, "application/octet-stream")))

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            url,
            headers=_upload_headers(),
            files=multipart_files,
        )
        data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"Deployment failed: {data.get('errors')}")

    result = data["result"]
    deploy_url = result.get("url", "")
    logger.info("Deployed to Pages: %s → %s", project_name, deploy_url)
    return result


# ── Full Deploy Flow ────────────────────────────────────────────────────


async def deploy_site(
    site_name: str,
    html: str,
    css: str,
    js: str,
    pages: dict | None = None,
    is_multipage: bool = False,
) -> dict:
    """High-level deploy: create project if needed, upload files, return URL.

    Args:
        site_name: Human-readable site name.
        html: Main page HTML (single-page) or index HTML (multi-page).
        css: CSS content.
        js: JS content.
        pages: For multipage — dict of {slug: {html, css}} for each page.
        is_multipage: Whether site has multiple pages.

    Returns:
        {project_name, url, deployment_id}
    """
    project_name = _sanitize_project_name(site_name)

    # Ensure project exists
    try:
        await create_pages_project(project_name)
    except Exception as e:
        logger.warning("Project creation issue (may already exist): %s", e)

    # Build file tree
    files: dict[str, str] = {}

    if is_multipage and pages:
        # Multi-page: each page gets its own HTML file
        for slug, page_data in pages.items():
            page_html = page_data.get("html", "")
            page_css = page_data.get("css", css)  # fallback to shared CSS

            # Inline CSS into each page
            full_html = _inline_css_js(page_html, page_css, js)

            if slug == "index":
                files["/index.html"] = full_html
            else:
                files[f"/{slug}.html"] = full_html
    else:
        # Single-page: one index.html with everything inlined
        files["/index.html"] = _inline_css_js(html, css, js)

    # Deploy
    deployment = await deploy_to_pages(project_name, files)
    deploy_url = deployment.get("url", f"https://{project_name}.pages.dev")

    return {
        "project_name": project_name,
        "url": deploy_url,
        "deployment_id": deployment.get("id", ""),
        "pages_dev_url": f"https://{project_name}.pages.dev",
    }


def _inline_css_js(html: str, css: str, js: str) -> str:
    """Inline CSS and JS into an HTML document for self-contained deployment.

    If the HTML is missing <!DOCTYPE>, <html>, <head>, or <body> tags,
    wraps it in a proper document structure so browsers render it correctly.
    """
    has_doctype = "<!DOCTYPE" in html[:50] or "<!doctype" in html[:50]
    has_html_tag = "<html" in html[:200]
    has_head = "</head>" in html
    has_body = "</body>" in html

    if has_doctype and has_html_tag and has_head and has_body:
        # Well-formed HTML — inject inline
        if css and css.strip() and "<style>" not in html[:500]:
            style_tag = f"<style>\n{css}\n</style>"
            html = html.replace("</head>", f"{style_tag}\n</head>", 1)

        if js and js.strip():
            script_tag = f"<script>\n{js}\n</script>"
            html = html.replace("</body>", f"{script_tag}\n</body>", 1)

        return html

    # Incomplete HTML — wrap in proper document structure
    # Extract <title> if present in the fragment
    title = ""
    if "<title>" in html and "</title>" in html:
        start = html.index("<title>")
        end = html.index("</title>") + len("</title>")
        title = html[start:end]
        # Remove title from body content (it belongs in <head>)
        html = html[:start] + html[end:]

    # Extract all <meta> tags from the fragment
    meta_tags = []
    import re as _re
    for m in _re.finditer(r"<meta\s[^>]*>", html):
        meta_tags.append(m.group())
    # Remove meta tags from body
    for mt in meta_tags:
        html = html.replace(mt, "", 1)

    # Extract any <link> tags (fonts, etc.)
    link_tags = []
    for m in _re.finditer(r"<link\s[^>]*>", html):
        link_tags.append(m.group())
    for lt in link_tags:
        html = html.replace(lt, "", 1)

    # Build proper document
    head_parts = [title] + meta_tags + link_tags
    if css and css.strip():
        head_parts.append(f"<style>\n{css}\n</style>")

    body_end = ""
    if js and js.strip():
        body_end = f"<script>\n{js}\n</script>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{chr(10).join(head_parts)}
</head>
<body>
{html.strip()}
{body_end}
</body>
</html>"""


# ── DNS Zone Management ─────────────────────────────────────────────────


async def create_dns_zone(domain_name: str) -> dict:
    """Create a DNS zone in Cloudflare for a domain.

    Returns zone dict with id, name_servers, etc.
    """
    url = f"{CF_API_BASE}/zones"
    payload = {
        "name": domain_name,
        "account": {"id": _account_id()},
        "type": "full",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        data = resp.json()

    if not data.get("success"):
        errors = data.get("errors", [])
        # Zone already exists
        if any(e.get("code") == 1061 for e in errors):
            return await get_dns_zone(domain_name)
        raise RuntimeError(f"Failed to create DNS zone: {errors}")

    logger.info("Created DNS zone for %s", domain_name)
    return data["result"]


async def get_dns_zone(domain_name: str) -> dict | None:
    """Look up a DNS zone by domain name."""
    url = f"{CF_API_BASE}/zones"
    params = {"name": domain_name, "status": "active"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_headers(), params=params)
        data = resp.json()

    if data.get("success") and data.get("result"):
        return data["result"][0]
    return None


async def add_dns_record(zone_id: str, record_type: str, name: str, content: str, proxied: bool = True) -> dict:
    """Add a DNS record to a zone."""
    url = f"{CF_API_BASE}/zones/{zone_id}/dns_records"
    payload = {
        "type": record_type,
        "name": name,
        "content": content,
        "proxied": proxied,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"Failed to add DNS record: {data.get('errors')}")
    return data["result"]


async def connect_custom_domain(project_name: str, domain_name: str) -> dict:
    """Connect a custom domain to a CF Pages project.

    This adds the domain to the Pages project and creates the CNAME record.
    """
    url = f"{CF_API_BASE}/accounts/{_account_id()}/pages/projects/{project_name}/domains"
    payload = {"name": domain_name}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"Failed to connect domain: {data.get('errors')}")

    logger.info("Connected %s → %s.pages.dev", domain_name, project_name)
    return data["result"]


# ── Cache ───────────────────────────────────────────────────────────────


async def purge_cache(zone_id: str) -> bool:
    """Purge all cached content for a zone."""
    url = f"{CF_API_BASE}/zones/{zone_id}/purge_cache"
    payload = {"purge_everything": True}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
        data = resp.json()
    return data.get("success", False)


# ── Verification ────────────────────────────────────────────────────────


async def verify_token() -> bool:
    """Verify the CF API token is valid."""
    url = f"{CF_API_BASE}/user/tokens/verify"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, headers=_headers())
        data = resp.json()
    return data.get("success", False) and data.get("result", {}).get("status") == "active"
