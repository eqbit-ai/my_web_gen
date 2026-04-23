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


def _strip_html_comments_for_deploy(html: str) -> str:
    """Strip HTML comments before uploading to S3.

    Two failure modes this guards against on the live site:
      1. Closed comments (``<!-- ... -->``) leaking visible LLM artefacts.
      2. UNCLOSED comment labels (``<!-- Hero Section<section ...``) — without
         the closing ``-->`` the browser treats everything after ``<!--`` as a
         comment, blanking the page.

    CRITICAL: ``<script>`` and ``<style>`` blocks are masked out before the
    regex runs. Inline JS frequently contains strings like ``"<!-- foo"`` for
    legacy reasons, and my unclosed-comment regex would greedily eat
    everything up to the next ``<`` character in the script — truncating the
    JS mid-file and causing ``Uncaught SyntaxError: Unexpected end of input``
    on the deployed site. Masking them preserves script bodies verbatim.
    """
    if not html:
        return html

    # ── Mask <script> and <style> blocks so the comment regexes below can't
    #    chew on their contents (JS often contains "<!--" in strings and CSS
    #    occasionally contains legacy comment-hiding markers). ──
    script_blocks: list[str] = []
    style_blocks: list[str] = []

    def _stash_script(m):
        script_blocks.append(m.group(0))
        return f"\x00SCRIPT_{len(script_blocks) - 1}\x00"

    def _stash_style(m):
        style_blocks.append(m.group(0))
        return f"\x00STYLE_{len(style_blocks) - 1}\x00"

    html = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', _stash_script, html, flags=re.IGNORECASE)
    html = re.sub(r'<style\b[^>]*>[\s\S]*?</style>', _stash_style, html, flags=re.IGNORECASE)

    # Preserve removal markers (in-app uses them to hide elements). Tolerate
    # near-miss spellings: <!-- removed -->, <!-- remove -->, <!-- delete(d) -->.
    html = re.sub(
        r'<!--\s*(?:removed?|deleted?|element\s+removed)\s*-->',
        '\x00REMOVED\x00',
        html,
        flags=re.IGNORECASE,
    )
    # Strip CLOSED HTML comments FIRST. This must run before the unclosed
    # fallback below — otherwise a properly-formed comment that wraps inline
    # markup (e.g. `<!-- CTA <strong>Book</strong> -->`) would be partially
    # eaten by the unclosed regex, leaving the inner markup as visible content.
    html = re.sub(r'<!--[\s\S]*?-->', '', html)
    # Strip UNCLOSED comment labels (no closing `-->` before the next tag).
    # Safe to run AFTER the closed-comment strip because all well-formed
    # comments have already been removed.
    html = re.sub(r'<!--\s*[^<>]+?(?=<)', '', html)
    # Strip stray fragments like --> or ----> from truncated comments
    html = re.sub(r'<!-+>|(?<!\w)--+>(?!\s*\})', '', html)
    # Restore removal markers
    html = html.replace('\x00REMOVED\x00', '<!-- removed -->')

    # ── Restore <script> and <style> blocks ──
    for i, block in enumerate(script_blocks):
        html = html.replace(f"\x00SCRIPT_{i}\x00", block)
    for i, block in enumerate(style_blocks):
        html = html.replace(f"\x00STYLE_{i}\x00", block)

    return html


def _strip_cms_artifacts(html: str) -> str:
    """Strip CMS inline-editing artifacts before deploy.

    `contenteditable="true"` is a plain HTML attribute — if it leaks into
    saved/deployed HTML, the browser makes that element editable in any
    viewer (live site, admin preview) without needing any script. Heals
    existing polluted sessions on next deploy.
    """
    if not html:
        return html
    html = re.sub(r'\s+contenteditable\s*=\s*"[^"]*"', '', html, flags=re.IGNORECASE)
    html = re.sub(r"\s+contenteditable\s*=\s*'[^']*'", '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s+contenteditable(?=[\s/>])', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s+class\s*=\s*"([^"]*)"', lambda m: _scrub_cms_classes(m, '"'), html, flags=re.IGNORECASE)
    html = re.sub(r"\s+class\s*=\s*'([^']*)'", lambda m: _scrub_cms_classes(m, "'"), html, flags=re.IGNORECASE)
    return html


def _scrub_cms_classes(match, quote: str) -> str:
    classes = match.group(1).split()
    kept = [c for c in classes if c not in {"cms-hover-outline", "cms-editing", "cms-img-outline"}]
    if not kept:
        return ""
    return f' class={quote}{" ".join(kept)}{quote}'


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
  <script src="https://cdn.jsdelivr.net/npm/lenis@1.3.23/dist/lenis.min.js"></script>
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

    # ── Strip `hero-stagger` class from every element ──
    #
    # The hero-stagger animation JS (in animations.py) does:
    #     el.textContent → flatten all descendant text
    #     el.innerHTML = ''  → WIPE h1, p, buttons, background structure
    #     rebuild as flat list of word spans
    #
    # LLM-generated sites frequently put `hero-stagger` on the entire <section>
    # element (not just the h1), so this destructive JS wipes the whole hero's
    # HTML structure — leaving a flat stream of text with no layout. The user
    # sees "AUTHENTICITALIANExperiencethetruetaste..." jammed together.
    #
    # Disabling the class neuters the JS without touching anything else. The
    # page still renders with all the normal fade/scroll animations.
    html = re.sub(r'\bhero-stagger\b', '', html)
    # Clean up any empty class="" attrs left behind
    html = re.sub(r'\s*class="\s*"', '', html)
    # Collapse extra spaces inside class attributes
    html = re.sub(r'(class="[^"]*?)\s{2,}([^"]*?")', r'\1 \2', html)

    # Strip data-splitting from EVERY element (not just .hero-stagger).
    #
    # Splitting.js auto-initializes on any element with [data-splitting] and
    # replaces its text content with per-character <span class="char"> nodes.
    # The .char spans use display:inline-block which — combined with the way
    # Splitting.js handles the text nodes — collapses whitespace between
    # words, so "Authentic Italian Pizza" renders as "AuthenticItalianPizza"
    # on the deployed site.
    #
    # The in-app preview is unaffected because its iframe never loads
    # Splitting.js and force-disables all animations, so the DOM mutation
    # never happens there — making the bug invisible until deploy.
    #
    # Splitting.js has caused more bugs than value across the codebase, so
    # we disable it entirely on deployed output. All the animation effects
    # users actually care about (fade-up, slide-in, stagger) come from AOS
    # and from our own animation CSS, not Splitting.js.
    html = re.sub(r'\s+data-splitting(?:="[^"]*")?', '', html)

    animation_css = get_animation_css()
    animation_js = get_animation_js()
    aos_init = """
  <script>
    if (typeof AOS !== 'undefined') { AOS.init({ duration: 800, once: true, offset: 50 }); }
  </script>"""

    # CRITICAL FIX: Templates (and legacy projects built from templates) store
    # a copy of animation_js in their `js` field via templates.py. Without
    # this guard we inject animation_js twice — once via _inline_css_js below
    # and once via the user `js` block — which creates two nested
    # `document.addEventListener('DOMContentLoaded', function() {` wrappers.
    # The second one's `});` closes the inner scope, but the outer one is
    # never closed → "Uncaught SyntaxError: Unexpected end of input" and ALL
    # inline JS stops executing (hero hidden/mangled, animations don't run).
    # Detect the signature marker and strip the duplicate copy from user js.
    ANIMATION_JS_MARKER = "ANIMATION & EFFECT LIBRARY"
    if js and ANIMATION_JS_MARKER in js:
        # User js is (or contains) a copy of the animation library.
        # Remove it entirely — the canonical copy is injected below.
        js = ""

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
  // Force-visibility fallback. IMPORTANT: do NOT reset `transform` on
  // arbitrary elements — that wipes user-applied positioning transforms from
  // the element editor. Only reset transform on elements that explicitly
  // opt in to a reveal animation.
  function isAnimEl(el){
    return el.hasAttribute('data-aos')
      || el.classList.contains('stagger-child')
      || el.classList.contains('fade-in')
      || el.classList.contains('slide-up')
      || el.classList.contains('slide-in-left')
      || el.classList.contains('slide-in-right')
      || el.classList.contains('hero-stagger');
  }
  function showAll(){
    document.querySelectorAll('section, [data-section-type]').forEach(function(el){
      el.style.opacity='1';
      if(isAnimEl(el)) el.style.transform='none';
      el.classList.add('visible');
    });
    document.querySelectorAll('.hero-content, .hero-center-content, .hero-full-overlay').forEach(function(el){
      el.style.opacity='1';
      if(isAnimEl(el)) el.style.transform='none';
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
    // Also fix any h1 inside hero sections that might be invisible.
    // Only touch transform if the element is actually invisible (opacity 0
    // or zero-height), to avoid wiping user-applied positioning transforms.
    document.querySelectorAll('[data-section-type="hero"] h1, .hero-section h1').forEach(function(h1){
      var cs=window.getComputedStyle(h1);
      if(cs.opacity==='0'||h1.offsetHeight===0){
        h1.style.opacity='1';
        h1.style.visibility='visible';
        // Only reset transform if it looks like an animation transform
        // (matrix with translation or scale!=1). Skip if user has set an
        // inline transform via the element editor.
        if(!h1.style.transform || h1.style.transform==='none'){
          h1.style.transform='none';
        }
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
  // See note in body_inject above — never blanket-reset transform here.
  function isAnimEl(el){
    return el.hasAttribute('data-aos')
      || el.classList.contains('stagger-child')
      || el.classList.contains('fade-in')
      || el.classList.contains('slide-up')
      || el.classList.contains('slide-in-left')
      || el.classList.contains('slide-in-right')
      || el.classList.contains('hero-stagger');
  }
  function showAll(){
    document.querySelectorAll('section, [data-section-type]').forEach(function(el){
      el.style.opacity='1';if(isAnimEl(el))el.style.transform='none';el.classList.add('visible');
    });
    document.querySelectorAll('.hero-content, .hero-center-content, .hero-full-overlay').forEach(function(el){
      el.style.opacity='1';if(isAnimEl(el))el.style.transform='none';
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
        h1.style.opacity='1';h1.style.visibility='visible';
        // Only reset transform if user has not set their own inline transform.
        if(!h1.style.transform||h1.style.transform==='none'){h1.style.transform='none';}
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
    """Convert absolute page links to relative paths for S3 prefix hosting.

    S3 static hosting serves sites under a prefix folder (e.g. /project-name/).
    Absolute paths like href="/about.html" resolve to the bucket root, not the
    project folder, causing 404s.  Relative paths (href="about.html") work correctly.

    Handles:
      - href="/about.html" → href="about.html"
      - href="/" → href="index.html"
      - window.location.href = '/about.html' → 'about.html'
      - window.location = '/' → 'index.html'
      - location.assign('/services.html') → 'services.html'
    """
    # ── HTML href attributes ──
    # href="/" → href="index.html"
    html = re.sub(r'href\s*=\s*"/"', 'href="index.html"', html)
    html = re.sub(r"href\s*=\s*'/'", "href='index.html'", html)

    # href="/about.html" → href="about.html" (strip leading slash from .html links)
    html = re.sub(r'href\s*=\s*"/([a-zA-Z0-9_-]+\.html)"', r'href="\1"', html)
    html = re.sub(r"href\s*=\s*'/([a-zA-Z0-9_-]+\.html)'", r"href='\1'", html)

    # ── HTML action attributes (forms) ──
    html = re.sub(r'action\s*=\s*"/([a-zA-Z0-9_-]+\.html)"', r'action="\1"', html)

    # ── JavaScript navigation patterns ──
    # window.location.href = '/about.html' or location.href = '/about.html'
    html = re.sub(
        r"""((?:window\.)?location\.href\s*=\s*)(['"])\/([a-zA-Z0-9_-]+\.html)\2""",
        r"\1\2\3\2",
        html,
    )
    # window.location.href = '/' or location.href = '/'
    html = re.sub(
        r"""((?:window\.)?location\.href\s*=\s*)(['"])\/\2""",
        r"\1\2index.html\2",
        html,
    )

    # window.location = '/about.html' or location = '/about.html'
    # (must not match location.href, location.assign, location.replace)
    html = re.sub(
        r"""((?:window\.)?location\s*=\s*)(['"])\/([a-zA-Z0-9_-]+\.html)\2""",
        r"\1\2\3\2",
        html,
    )
    html = re.sub(
        r"""((?:window\.)?location\s*=\s*)(['"])\/\2""",
        r"\1\2index.html\2",
        html,
    )

    # location.assign('/about.html') or location.replace('/about.html')
    html = re.sub(
        r"""((?:window\.)?location\.(?:assign|replace)\s*\(\s*)(['"])\/([a-zA-Z0-9_-]+\.html)\2""",
        r"\1\2\3\2",
        html,
    )
    html = re.sub(
        r"""((?:window\.)?location\.(?:assign|replace)\s*\(\s*)(['"])\/\2""",
        r"\1\2index.html\2",
        html,
    )

    # navigate('/about.html') — generic helper some LLM JS uses
    html = re.sub(
        r"""(navigate\s*\(\s*)(['"])\/([a-zA-Z0-9_-]+\.html)\2""",
        r"\1\2\3\2",
        html,
    )

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
        logger.warning("[FORM INJECT] Skipped — API_BASE_URL not set (api_base=%s, site_id=%s)", bool(api_base), bool(site_id))
        return html

    form_url = f"{api_base}/api/forms/submit/{site_id}"
    logger.info("[FORM INJECT] Injecting form action: %s", form_url)

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
        # Add/replace action, method, and data-form-handler
        tag = re.sub(r'action\s*=\s*["\'][^"\']*["\']', '', tag)
        tag = re.sub(r'method\s*=\s*["\'][^"\']*["\']', '', tag)
        tag = re.sub(r'data-form-handler\s*=\s*["\'][^"\']*["\']', '', tag)
        tag = tag.rstrip(">")
        tag += f' action="{form_url}" method="POST" data-form-handler="{form_url}">'
        # Add hidden page field
        hidden = f'<input type="hidden" name="_page" value="{page_slug}">'
        return tag + hidden

    # Match forms with contact-related classes
    html = re.sub(
        r'<form[^>]*class="[^"]*(?:contact|inquiry|get-in-touch|message)[^"]*"[^>]*>',
        _patch_form,
        html,
        flags=re.IGNORECASE,
    )

    # Match forms with contact-related ids
    html = re.sub(
        r'<form[^>]*id="[^"]*contact[^"]*"[^>]*>',
        _patch_form,
        html,
        flags=re.IGNORECASE,
    )

    # Match forms with data-form-handler attribute (LLM-generated placeholder)
    html = re.sub(
        r'<form[^>]*data-form-handler[^>]*>',
        _patch_form,
        html,
        flags=re.IGNORECASE,
    )

    # Fallback: match ANY remaining form tag that doesn't already have our API action
    # (catches forms without contact/inquiry class/id/data attributes — e.g. newsletter, reservation)
    html = re.sub(
        r'<form(?![^>]*/api/forms/submit)[^>]*>',
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
    logger.info("[TRACKING INJECT] api_base=%s, site_id=%s", api_base or "NOT SET", site_id)

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
            # Defensive: skip pages that have no HTML at all. Without this
            # guard, an empty page_data (e.g. from a race during page-add
            # before the HTML was written) would deploy as a literal blank
            # file at /{slug}.html, and the user would see a white page on
            # the live site. Better to skip and log so they notice it's
            # missing rather than ship a broken page.
            if not page_html or not page_html.strip():
                logger.warning(
                    "deploy_site: skipping empty page slug=%r in project %r — page_data has no html",
                    slug, project_name,
                )
                continue
            # Strip stray HTML comments (closed AND unclosed labels) BEFORE
            # any further transformation. This heals legacy sessions where
            # the in-app strip pass missed an unclosed `<!--` and the live
            # site renders blank.
            page_html = _strip_html_comments_for_deploy(page_html)
            page_html = _strip_cms_artifacts(page_html)
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
        # Single-page deploy — apply the same comment-strip safety net.
        html = _strip_html_comments_for_deploy(html)
        html = _strip_cms_artifacts(html)
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
            put_kwargs = {
                "Bucket": bucket,
                "Key": s3_key,
                "Body": content_bytes,
                "ContentType": _content_type(file_path),
            }
            # HTML files: set no-cache so browsers always fetch fresh content after redeploy
            if file_path.endswith(".html"):
                put_kwargs["CacheControl"] = "no-cache, no-store, must-revalidate"
            s3.put_object(**put_kwargs)
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
