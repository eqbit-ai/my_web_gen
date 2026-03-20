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

    # Fix hero-stagger + Splitting.js conflict:
    # Remove data-splitting from elements that also have hero-stagger class.
    # Splitting.js auto-inits on [data-splitting] and wraps chars in spans,
    # then hero-stagger JS also processes .hero-stagger and wipes innerHTML → invisible text.
    # Removing data-splitting lets hero-stagger handle the animation alone.
    html = re.sub(
        r'(<[^>]*class="[^"]*hero-stagger[^"]*"[^>]*)\s+data-splitting(?:="[^"]*")?',
        r'\1',
        html,
    )
    # Also handle reverse attribute order: data-splitting before class
    html = re.sub(
        r'(<[^>]*)\s+data-splitting(?:="[^"]*")?\s+([^>]*class="[^"]*hero-stagger[^"]*")',
        r'\1 \2',
        html,
    )

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
        # Force hero headings visible — prevents hero-stagger JS + CSS animation from hiding text.
        # CSS animations with "forwards" override !important on opacity/transform,
        # so we must also override the animation property itself.
        head_inject += """<style>
.hero-stagger, .hero-stagger span,
[data-section-type="hero"] h1, [data-section-type="hero"] h1 span,
.hero-section h1, .hero-section h1 span {
  opacity: 1 !important;
  visibility: visible !important;
  transform: none !important;
  animation: none !important;
}
</style>
"""
        html = html.replace("</head>", f"{head_inject}</head>", 1)

        # Inject CDN scripts + animation JS + user JS before </body>
        body_inject = CDN_SCRIPTS
        if animation_js:
            body_inject += f"<script>\n{animation_js}\n</script>\n"
        body_inject += aos_init + "\n"
        if js and js.strip():
            body_inject += f"<script>\n{js}\n</script>\n"

        # Safety: force all sections visible after load + short delay
        # Catches cases where LLM CSS hides sections with opacity:0 and the
        # scroll observer JS doesn't fire properly on deployed sites
        body_inject += """<script>
(function(){
  function showAll(){
    document.querySelectorAll('section, [data-section-type]').forEach(function(el){
      el.style.opacity='1';
      el.style.transform='none';
      el.classList.add('visible');
    });
    document.querySelectorAll('.hero-content, .hero-center-content, .hero-full-overlay').forEach(function(el){
      el.style.opacity='1';
      el.style.transform='none';
    });
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',function(){setTimeout(showAll,100)});}
  else{setTimeout(showAll,100);}
})();
</script>
"""
        # Fix hero-stagger + Splitting.js conflict:
        # Splitting.js wraps chars in spans, then LLM's hero-stagger JS clears innerHTML
        # and re-wraps with opacity:0 spans — resulting in invisible headings.
        # This script runs LAST, after both Splitting.js and LLM JS have executed,
        # and forces hero-stagger text (especially H1) to be visible.
        body_inject += """<script>
(function(){
  function fixHeroStagger(){
    document.querySelectorAll('.hero-stagger').forEach(function(el){
      // Force all child spans visible
      el.querySelectorAll('span').forEach(function(s){
        s.style.opacity='1';
        s.style.transform='none';
        s.style.display='inline-block';
      });
      // If element itself is hidden, show it
      var cs=window.getComputedStyle(el);
      if(cs.opacity==='0'||el.style.opacity==='0'){
        el.style.opacity='1';
        el.style.transform='none';
      }
      // If element has no visible text (Splitting.js or hero-stagger wiped it),
      // restore from data-original or aria-label
      if(el.textContent.trim().length===0){
        var orig=el.getAttribute('data-original')||el.getAttribute('aria-label')||'';
        if(orig)el.textContent=orig;
      }
    });
    // Also fix any h1 inside hero sections that might be invisible
    document.querySelectorAll('[data-section-type="hero"] h1, .hero-section h1').forEach(function(h1){
      var cs=window.getComputedStyle(h1);
      if(cs.opacity==='0'||h1.offsetHeight===0){
        h1.style.opacity='1';
        h1.style.transform='none';
        h1.style.visibility='visible';
        h1.querySelectorAll('span').forEach(function(s){
          s.style.opacity='1';
          s.style.transform='none';
        });
      }
    });
  }
  // Run after everything: DOMContentLoaded + extra delay for Splitting.js + hero-stagger
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',function(){setTimeout(fixHeroStagger,500);setTimeout(fixHeroStagger,1500);});
  }else{
    setTimeout(fixHeroStagger,500);
    setTimeout(fixHeroStagger,1500);
  }
})();
</script>
"""
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
    head_parts.append("""<style>
.hero-stagger, .hero-stagger span,
[data-section-type="hero"] h1, [data-section-type="hero"] h1 span,
.hero-section h1, .hero-section h1 span {
  opacity: 1 !important; visibility: visible !important; transform: none !important; animation: none !important;
}
</style>""")

    body_end = CDN_SCRIPTS
    if animation_js:
        body_end += f"<script>\n{animation_js}\n</script>\n"
    body_end += aos_init + "\n"
    if js and js.strip():
        body_end += f"<script>\n{js}\n</script>"
    body_end += """<script>
(function(){
  function showAll(){
    document.querySelectorAll('section, [data-section-type]').forEach(function(el){
      el.style.opacity='1';el.style.transform='none';el.classList.add('visible');
    });
    document.querySelectorAll('.hero-content, .hero-center-content, .hero-full-overlay').forEach(function(el){
      el.style.opacity='1';el.style.transform='none';
    });
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',function(){setTimeout(showAll,100)});}
  else{setTimeout(showAll,100);}
})();
</script>"""
    body_end += """<script>
(function(){
  function fixHeroStagger(){
    document.querySelectorAll('.hero-stagger').forEach(function(el){
      el.querySelectorAll('span').forEach(function(s){s.style.opacity='1';s.style.transform='none';s.style.display='inline-block';});
      var cs=window.getComputedStyle(el);
      if(cs.opacity==='0'||el.style.opacity==='0'){el.style.opacity='1';el.style.transform='none';}
    });
    document.querySelectorAll('[data-section-type="hero"] h1, .hero-section h1').forEach(function(h1){
      var cs=window.getComputedStyle(h1);
      if(cs.opacity==='0'||h1.offsetHeight===0){
        h1.style.opacity='1';h1.style.transform='none';h1.style.visibility='visible';
        h1.querySelectorAll('span').forEach(function(s){s.style.opacity='1';s.style.transform='none';});
      }
    });
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',function(){setTimeout(fixHeroStagger,500);setTimeout(fixHeroStagger,1500);});}
  else{setTimeout(fixHeroStagger,500);setTimeout(fixHeroStagger,1500);}
})();
</script>"""

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


def _upload_local_images(html: str, project_name: str, s3, bucket: str) -> str:
    """Find local /uploads/... URLs in HTML/CSS, upload them to S3, rewrite URLs.

    Local images are served by the backend at /uploads/{user_id}/{project_id}/{uuid}.ext.
    These don't exist on S3, so we upload them to s3://{bucket}/{project_name}/images/
    and rewrite the URLs to relative paths (images/{filename}).

    Handles both relative (/uploads/...) and absolute (http://localhost:8000/uploads/...) URLs.
    """
    from app.utils.storage import UPLOAD_DIR

    # First, normalize full localhost URLs to relative /uploads/... paths
    # Matches http://localhost:PORT/uploads/... or http://127.0.0.1:PORT/uploads/...
    html = re.sub(
        r'https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(/uploads/[^"\')\s]+)',
        r'\1',
        html,
    )

    # Find all /uploads/... references in HTML (src, url(), background-image, etc.)
    upload_pattern = re.compile(r'''(?:src|href)\s*=\s*["'](/uploads/[^"']+)["']|url\(\s*['"]?(/uploads/[^)'"\s]+)['"]?\s*\)''')
    matches = upload_pattern.findall(html)

    # Flatten — each match is a tuple of (src_match, url_match), one will be empty
    local_urls = set()
    for groups in matches:
        for url in groups:
            if url:
                local_urls.add(url)

    if not local_urls:
        return html

    uploaded_count = 0
    for local_url in local_urls:
        # Strip leading / and uploads/ prefix to get relative path on disk
        rel_path = local_url.lstrip("/")
        if rel_path.startswith("uploads/"):
            rel_path = rel_path[len("uploads/"):]

        abs_path = UPLOAD_DIR / rel_path

        if not abs_path.exists() or not abs_path.is_file():
            logger.warning("Local image not found on disk: %s", abs_path)
            continue

        # Read the image
        try:
            with open(abs_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            logger.warning("Failed to read local image %s: %s", abs_path, e)
            continue

        # Upload to S3 under project_name/images/
        filename = abs_path.name  # uuid.ext
        s3_key = f"{project_name}/images/{filename}"

        try:
            s3.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=image_bytes,
                ContentType=_content_type(filename),
            )
            uploaded_count += 1
        except ClientError as e:
            logger.warning("Failed to upload image %s to S3: %s", filename, e)
            continue

        # Rewrite URL in HTML: /uploads/... → images/filename (relative)
        html = html.replace(local_url, f"images/{filename}")

    if uploaded_count:
        logger.info("Uploaded %d local images to S3 for %s", uploaded_count, project_name)

    return html


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


def _inject_form_action(html: str, site_id: str, page_slug: str = "index") -> str:
    """Inject the form submission API endpoint into contact forms.

    Replaces {{FORM_ACTION}} placeholders and also patches any <form> with
    class containing 'contact' that doesn't already point to our API.
    """
    api_base = os.getenv("API_BASE_URL", "").rstrip("/")
    if not api_base:
        alb = os.getenv("ALB_URL", "")
        if alb:
            api_base = alb.rstrip("/")

    if not api_base or not site_id:
        return html

    form_url = f"{api_base}/api/forms/submit/{site_id}"

    # Replace template placeholders
    html = html.replace("{{FORM_ACTION}}", form_url)
    html = html.replace("{{PAGE_SLUG}}", page_slug)

    # Fallback: patch <form> tags that have contact/inquiry/get-in-touch related classes
    # but no action or action="#" or action=""
    def _patch_form(match):
        tag = match.group(0)
        # Skip if already pointing to our API
        if "/api/forms/submit/" in tag:
            return tag
        # Add/replace action and method
        tag = re.sub(r'action\s*=\s*["\'][^"\']*["\']', '', tag)
        tag = re.sub(r'method\s*=\s*["\'][^"\']*["\']', '', tag)
        tag = tag.rstrip(">")
        tag += f' action="{form_url}" method="POST">'
        # Add hidden page field
        hidden = f'<input type="hidden" name="_page" value="{page_slug}">'
        return tag + hidden

    html = re.sub(
        r'<form[^>]*class="[^"]*(?:contact|inquiry|get-in-touch|message)[^"]*"[^>]*>',
        _patch_form,
        html,
        flags=re.IGNORECASE,
    )

    # Also patch forms with id containing "contact" or whose parent section is contact
    html = re.sub(
        r'<form[^>]*id="[^"]*contact[^"]*"[^>]*>',
        _patch_form,
        html,
        flags=re.IGNORECASE,
    )

    return html


def _inject_tracking_and_custom_code(
    html: str, site_id: str,
    custom_head: str = "", custom_body: str = "",
) -> str:
    """Inject page view tracking script and custom code into deployed HTML."""
    api_base = os.getenv("API_BASE_URL", "").rstrip("/")
    if not api_base:
        alb = os.getenv("ALB_URL", "")
        if alb:
            api_base = alb.rstrip("/")

    # Build injection blocks
    head_inject = ""
    body_inject = ""

    # Custom head code (e.g. Google Analytics, meta tags, external CSS)
    if custom_head:
        head_inject += f"\n<!-- Custom Head Code -->\n{custom_head}\n"

    # Page view tracking script
    if api_base and site_id:
        track_url = f"{api_base}/api/sites/track/{site_id}"
        body_inject += f"""
<!-- Page View Tracking -->
<script>
(function(){{
  try {{
    var d = {{path: location.pathname, referrer: document.referrer}};
    navigator.sendBeacon ? navigator.sendBeacon("{track_url}", JSON.stringify(d))
      : fetch("{track_url}", {{method:"POST", body:JSON.stringify(d), headers:{{"Content-Type":"application/json"}}, keepalive:true}});
  }} catch(e) {{}}
}})();
</script>
"""

    # Custom body code (e.g. chat widgets, custom JS)
    if custom_body:
        body_inject += f"\n<!-- Custom Body Code -->\n{custom_body}\n"

    # Inject into HTML
    if head_inject and "</head>" in html:
        html = html.replace("</head>", f"{head_inject}</head>", 1)
    if body_inject and "</body>" in html:
        html = html.replace("</body>", f"{body_inject}</body>", 1)

    return html


async def deploy_site(
    site_name: str,
    html: str,
    css: str,
    js: str,
    pages: dict | None = None,
    is_multipage: bool = False,
    s3_prefix_override: str | None = None,
    site_id: str | None = None,
    custom_head_code: str = "",
    custom_body_code: str = "",
) -> dict:
    """Deploy a website to S3 as static files.

    Each site gets its own folder prefix in the bucket.
    If s3_prefix_override is given, reuses that exact prefix (for redeploying to the same URL).
    Returns {project_name, url, s3_prefix}.
    """
    project_name = s3_prefix_override or _sanitize_project_name(site_name)
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
            # Upload local images to S3 and rewrite URLs
            full_html = _upload_local_images(full_html, project_name, s3, bucket)
            # Inject form submission endpoint
            if site_id:
                full_html = _inject_form_action(full_html, site_id, slug)
            # Inject tracking script + custom code
            if site_id:
                full_html = _inject_tracking_and_custom_code(full_html, site_id, custom_head_code, custom_body_code)

            if slug == "index":
                files["index.html"] = full_html
            else:
                files[f"{slug}.html"] = full_html
    else:
        full_html = _inline_css_js(html, css, js)
        full_html = _upload_local_images(full_html, project_name, s3, bucket)
        # Inject form submission endpoint
        if site_id:
            full_html = _inject_form_action(full_html, site_id, "index")
        # Inject tracking script + custom code
        if site_id:
            full_html = _inject_tracking_and_custom_code(full_html, site_id, custom_head_code, custom_body_code)
        files["index.html"] = full_html

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
            raise RuntimeError(f"S3 upload failed for {file_path}: {e}") from e

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
