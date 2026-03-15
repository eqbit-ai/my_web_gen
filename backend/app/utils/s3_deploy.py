"""
AWS S3 static website deployment — uploads generated websites to S3 as static sites.

Each site gets a folder: s3://{bucket}/{project_name}/
Files are served via S3 static website hosting or CloudFront.

Public URL pattern: http://{bucket}.s3-website.{region}.amazonaws.com/{project_name}/
"""

import logging
import os
import re

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        region_name=os.getenv("AWS_REGION", "me-central-1"),
    )


def _bucket() -> str:
    return os.getenv("AWS_S3_DEPLOY_BUCKET", "")


def _region() -> str:
    return os.getenv("AWS_REGION", "me-central-1")


def _sanitize_project_name(name: str) -> str:
    """Convert a site name to a valid S3 key prefix (lowercase, hyphens, max 58 chars)."""
    slug = re.sub(r"[^a-z0-9-]", "-", name.lower().strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:58] or "site"


MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
}


def _content_type(path: str) -> str:
    for ext, mime in MIME_TYPES.items():
        if path.endswith(ext):
            return mime
    return "application/octet-stream"


def _fix_svg_favicon(html: str) -> str:
    """URL-encode SVG data URIs in favicon link tags to prevent HTML parse breakage.

    Browsers treat raw <style>/<script> inside unencoded SVG data URIs as real
    HTML tags, which breaks the page.  Percent-encoding the SVG payload fixes it.
    """
    import urllib.parse

    # Match href="data:image/svg+xml,..." using the same quote char for open/close
    pattern = re.compile(
        r'''(<link\s[^>]*href\s*=\s*)(["'])data:image/svg\+xml,(.*?)\2''',
        re.DOTALL,
    )

    def _encode(m):
        prefix, quote, svg_raw = m.group(1), m.group(2), m.group(3)
        # If already percent-encoded, leave it alone
        if "%3C" in svg_raw or "%3c" in svg_raw:
            return m.group(0)
        encoded = urllib.parse.quote(svg_raw, safe='')
        return f"{prefix}{quote}data:image/svg+xml,{encoded}{quote}"

    return pattern.sub(_encode, html)


CDN_HEAD = """
  <!-- Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css">
  <!-- Animations -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.css">
"""

CDN_SCRIPTS = """
  <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.16/dist/typed.umd.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/vanilla-tilt@1.8.1/dist/vanilla-tilt.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/tsparticles-slim@2.12.0/tsparticles.slim.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/lenis@1.0.42/dist/lenis.min.js"></script>
"""


def _inline_css_js(html: str, css: str, js: str) -> str:
    """Inline CSS and JS into HTML for self-contained deployment.

    Injects CDN links (Font Awesome, AOS, Typed.js, etc.) and builtin
    animation CSS/JS so deployed sites match the in-app preview exactly.
    """
    from app.utils.animations import get_animation_css, get_animation_js

    # Fix SVG favicons that break HTML parsing
    html = _fix_svg_favicon(html)

    # Strip any kit.fontawesome.com scripts (replaced by CDN link above)
    html = re.sub(r'<script[^>]*src=["\']https?://kit\.fontawesome\.com/[^"\']*["\'][^>]*></script>', '', html)

    animation_css = get_animation_css()
    animation_js = get_animation_js()
    aos_init = """
  <script>
    if (typeof AOS !== 'undefined') { AOS.init({ duration: 800, once: true, offset: 50 }); }
  </script>"""

    has_doctype = "<!DOCTYPE" in html[:50] or "<!doctype" in html[:50]
    has_html_tag = "<html" in html[:200]
    has_head = "</head>" in html
    has_body = "</body>" in html

    if has_doctype and has_html_tag and has_head and has_body:
        # Inject CDN links + animation CSS before </head>
        head_inject = CDN_HEAD
        if animation_css:
            head_inject += f"<style>\n{animation_css}\n</style>\n"
        if css and css.strip():
            head_inject += f"<style>\n{css}\n</style>\n"
        html = html.replace("</head>", f"{head_inject}</head>", 1)

        # Inject CDN scripts + animation JS + user JS before </body>
        body_inject = CDN_SCRIPTS
        if animation_js:
            body_inject += f"<script>\n{animation_js}\n</script>\n"
        body_inject += aos_init + "\n"
        if js and js.strip():
            body_inject += f"<script>\n{js}\n</script>\n"
        html = html.replace("</body>", f"{body_inject}</body>", 1)
        return html

    # Incomplete HTML — wrap in proper structure
    import re as _re

    title = ""
    if "<title>" in html and "</title>" in html:
        start = html.index("<title>")
        end = html.index("</title>") + len("</title>")
        title = html[start:end]
        html = html[:start] + html[end:]

    meta_tags = []
    for m in _re.finditer(r"<meta\s[^>]*>", html):
        meta_tags.append(m.group())
    for mt in meta_tags:
        html = html.replace(mt, "", 1)

    link_tags = []
    for m in _re.finditer(r"<link\s[^>]*>", html):
        link_tags.append(m.group())
    for lt in link_tags:
        html = html.replace(lt, "", 1)

    head_parts = [title] + meta_tags + link_tags
    head_parts.append(CDN_HEAD)
    if animation_css:
        head_parts.append(f"<style>\n{animation_css}\n</style>")
    if css and css.strip():
        head_parts.append(f"<style>\n{css}\n</style>")

    body_end = CDN_SCRIPTS
    if animation_js:
        body_end += f"<script>\n{animation_js}\n</script>\n"
    body_end += aos_init + "\n"
    if js and js.strip():
        body_end += f"<script>\n{js}\n</script>"

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


def _make_links_relative(html: str) -> str:
    """Convert absolute page links (href="/about.html", href="/") to relative paths.

    S3 static hosting serves sites under a prefix folder (e.g. /project-name/).
    Absolute paths like href="/about.html" resolve to the bucket root, not the
    project folder, causing 404s.  Relative paths (href="about.html") work correctly.
    """
    # href="/" → href="index.html"
    html = re.sub(r'href\s*=\s*"/"', 'href="index.html"', html)
    html = re.sub(r"href\s*=\s*'/'", "href='index.html'", html)

    # href="/about.html" → href="about.html" (strip leading slash from .html links)
    html = re.sub(r'href\s*=\s*"/([a-zA-Z0-9_-]+\.html)"', r'href="\1"', html)
    html = re.sub(r"href\s*=\s*'/([a-zA-Z0-9_-]+\.html)'", r"href='\1'", html)

    return html


async def deploy_site(
    site_name: str,
    html: str,
    css: str,
    js: str,
    pages: dict | None = None,
    is_multipage: bool = False,
) -> dict:
    """Deploy a website to S3 as static files.

    Each site gets its own folder prefix in the bucket.
    Returns {project_name, url, s3_prefix}.
    """
    project_name = _sanitize_project_name(site_name)
    bucket = _bucket()
    region = _region()

    if not bucket:
        raise RuntimeError("AWS_S3_DEPLOY_BUCKET not configured")

    s3 = _get_s3_client()

    # Ensure bucket has static website hosting enabled
    try:
        s3.get_bucket_website(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchWebsiteConfiguration":
            logger.info("Enabling static website hosting on bucket %s", bucket)
            s3.put_bucket_website(
                Bucket=bucket,
                WebsiteConfiguration={
                    "IndexDocument": {"Suffix": "index.html"},
                    "ErrorDocument": {"Key": "404.html"},
                },
            )

    # Build file tree
    files: dict[str, str] = {}

    if is_multipage and pages:
        for slug, page_data in pages.items():
            page_html = page_data.get("html", "")
            page_css = page_data.get("css", css)
            full_html = _inline_css_js(page_html, page_css, js)
            # Convert absolute links to relative for S3 prefix hosting
            full_html = _make_links_relative(full_html)

            if slug == "index":
                files["index.html"] = full_html
            else:
                files[f"{slug}.html"] = full_html
    else:
        files["index.html"] = _inline_css_js(html, css, js)

    # Upload each file
    uploaded = 0
    for file_path, content in files.items():
        s3_key = f"{project_name}/{file_path}"
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content

        try:
            s3.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=content_bytes,
                ContentType=_content_type(file_path),
            )
            uploaded += 1
            logger.debug("Uploaded s3://%s/%s (%d bytes)", bucket, s3_key, len(content_bytes))
        except ClientError as e:
            logger.error("Failed to upload %s: %s", s3_key, e)
            raise RuntimeError(f"S3 upload failed for {file_path}: {e}")

    # Set bucket policy for public read (if not already set)
    try:
        s3.get_bucket_policy(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            try:
                import json
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket}/*",
                    }],
                }
                s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
                logger.info("Set public-read bucket policy on %s", bucket)
            except ClientError as pe:
                logger.warning("Could not set bucket policy (may need manual config): %s", pe)

    # Build the deployed URL
    site_url = f"http://{bucket}.s3-website.{region}.amazonaws.com/{project_name}/"

    logger.info("Deployed %d files to S3: %s → %s", uploaded, project_name, site_url)

    return {
        "project_name": project_name,
        "url": site_url,
        "s3_prefix": project_name,
        "bucket": bucket,
        "region": region,
        "files_uploaded": uploaded,
    }


async def delete_site(project_name: str) -> bool:
    """Delete all files for a site from S3."""
    bucket = _bucket()
    s3 = _get_s3_client()

    try:
        # List all objects with the site prefix
        response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{project_name}/")
        objects = response.get("Contents", [])

        if objects:
            s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
            )
            logger.info("Deleted %d files for site %s", len(objects), project_name)

        return True
    except ClientError as e:
        logger.error("Failed to delete site %s: %s", project_name, e)
        return False


async def verify_credentials() -> bool:
    """Verify AWS credentials and bucket access."""
    try:
        s3 = _get_s3_client()
        s3.head_bucket(Bucket=_bucket())
        return True
    except Exception:
        return False
