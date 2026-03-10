"""
SEO analysis and tag generation for generated websites.

Pure Python — regex-based parsing, no external HTML parser dependencies.
Generates meta tags, JSON-LD structured data, sitemap, and robots.txt.
"""

import re
import json
from typing import Optional


# ---------------------------------------------------------------------------
# 1. check_seo
# ---------------------------------------------------------------------------

def check_seo(html: str, plan: dict = None) -> dict:
    """
    Analyze generated website for SEO issues.

    Returns dict with:
      - score (0-100)
      - issues (list of issue dicts)
      - passed (list of passed check names)
    """
    issues = []
    passed = []
    plan = plan or {}

    # ── Title tag ────────────────────────────────────────────────────
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
    if title_match:
        title_text = title_match.group(1).strip()
        title_len = len(title_text)
        if title_len < 10:
            issues.append({
                "type": "title_too_short",
                "severity": "warning",
                "message": f"Title tag too short ({title_len} chars, recommend 30-60)",
            })
        elif title_len > 70:
            issues.append({
                "type": "title_too_long",
                "severity": "info",
                "message": f"Title tag too long ({title_len} chars, recommend 30-60)",
            })
        else:
            passed.append("title_length")
    else:
        issues.append({
            "type": "missing_title",
            "severity": "critical",
            "message": "No <title> tag found",
        })

    # ── Meta description ─────────────────────────────────────────────
    desc_match = re.search(
        r'<meta[^>]+name\s*=\s*["\']description["\'][^>]+content\s*=\s*["\']([^"\']*)["\']',
        html, re.I,
    )
    if not desc_match:
        # Try reversed attribute order
        desc_match = re.search(
            r'<meta[^>]+content\s*=\s*["\']([^"\']*)["\'][^>]+name\s*=\s*["\']description["\']',
            html, re.I,
        )

    if desc_match:
        desc_text = desc_match.group(1).strip()
        desc_len = len(desc_text)
        if desc_len < 50:
            issues.append({
                "type": "description_too_short",
                "severity": "warning",
                "message": f"Meta description too short ({desc_len} chars, recommend 120-160)",
            })
        elif desc_len > 170:
            issues.append({
                "type": "description_too_long",
                "severity": "info",
                "message": f"Meta description too long ({desc_len} chars, recommend 120-160)",
            })
        else:
            passed.append("meta_description_length")
    else:
        issues.append({
            "type": "missing_description",
            "severity": "warning",
            "message": "No meta description tag found",
        })

    # ── H1 tag ───────────────────────────────────────────────────────
    h1_tags = re.findall(r'<h1\b[^>]*>(.*?)</h1>', html, re.I | re.S)
    if not h1_tags:
        issues.append({
            "type": "missing_h1",
            "severity": "warning",
            "message": "No <h1> tag found",
        })
    elif len(h1_tags) > 1:
        issues.append({
            "type": "multiple_h1",
            "severity": "info",
            "message": f"{len(h1_tags)} <h1> tags found (best practice: exactly 1)",
        })
    else:
        passed.append("single_h1")

    # ── Heading hierarchy ────────────────────────────────────────────
    headings = re.findall(r'<(h[1-6])\b', html, re.I)
    levels = [int(h[1]) for h in headings]
    hierarchy_ok = True
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            hierarchy_ok = False
            break
    if hierarchy_ok and levels:
        passed.append("heading_hierarchy")
    elif levels:
        issues.append({
            "type": "heading_hierarchy_broken",
            "severity": "info",
            "message": "Heading hierarchy skips levels",
        })

    # ── Image alt texts ──────────────────────────────────────────────
    img_tags = re.findall(r'<img\b[^>]*>', html, re.I | re.S)
    imgs_no_alt = sum(1 for img in img_tags if not re.search(r'\balt\s*=', img, re.I))
    imgs_empty_alt = sum(
        1 for img in img_tags
        if re.search(r'\balt\s*=\s*["\']["\']', img, re.I)
    )
    if imgs_no_alt > 0:
        issues.append({
            "type": "images_missing_alt",
            "severity": "warning",
            "message": f"{imgs_no_alt} image(s) missing alt attribute",
        })
    elif imgs_empty_alt > len(img_tags) * 0.5 and len(img_tags) > 2:
        issues.append({
            "type": "images_empty_alt",
            "severity": "info",
            "message": f"{imgs_empty_alt}/{len(img_tags)} images have empty alt text",
        })
    else:
        passed.append("image_alt_texts")

    # ── Structured data (JSON-LD) ────────────────────────────────────
    if re.search(r'<script[^>]+type\s*=\s*["\']application/ld\+json["\']', html, re.I):
        passed.append("structured_data")
    else:
        issues.append({
            "type": "missing_structured_data",
            "severity": "info",
            "message": "No JSON-LD structured data found",
        })

    # ── Open Graph tags ──────────────────────────────────────────────
    og_tags = re.findall(r'<meta[^>]+property\s*=\s*["\']og:', html, re.I)
    if len(og_tags) >= 3:
        passed.append("open_graph_tags")
    else:
        issues.append({
            "type": "missing_og_tags",
            "severity": "info",
            "message": f"Only {len(og_tags)} Open Graph tag(s) found (recommend og:title, og:description, og:image, og:type)",
        })

    # ── Canonical URL ────────────────────────────────────────────────
    if re.search(r'<link[^>]+rel\s*=\s*["\']canonical["\']', html, re.I):
        passed.append("canonical_url")
    else:
        issues.append({
            "type": "missing_canonical",
            "severity": "info",
            "message": "No canonical URL tag found",
        })

    # ── Robots meta ──────────────────────────────────────────────────
    if re.search(r'<meta[^>]+name\s*=\s*["\']robots["\']', html, re.I):
        passed.append("robots_meta")
    else:
        # Not critical for generated sites — informational only
        issues.append({
            "type": "missing_robots_meta",
            "severity": "info",
            "message": "No robots meta tag found",
        })

    # ── Internal link structure ──────────────────────────────────────
    internal_links = re.findall(r'<a\b[^>]+href\s*=\s*["\']#[^"\']*["\']', html, re.I)
    if len(internal_links) >= 2:
        passed.append("internal_links")
    else:
        issues.append({
            "type": "few_internal_links",
            "severity": "info",
            "message": f"Only {len(internal_links)} internal anchor link(s) found",
        })

    # ── Score calculation ────────────────────────────────────────────
    severity_weights = {"critical": 15, "warning": 5, "info": 2}
    deductions = sum(severity_weights.get(i["severity"], 2) for i in issues)
    score = max(0, min(100, round(100 - deductions)))

    return {
        "score": score,
        "issues": issues,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# 2. generate_seo_tags
# ---------------------------------------------------------------------------

def generate_seo_tags(plan: dict) -> str:
    """
    Generate SEO meta tags based on the plan.

    Returns a string of HTML meta tags to inject into <head>.
    """
    brand = plan.get("brand", {})
    brand_name = brand.get("name", "").strip()
    tagline = brand.get("tagline", "").strip()
    description = brand.get("description", tagline).strip()

    # Build a good title
    if brand_name and tagline:
        title = f"{brand_name} — {tagline}"
    elif brand_name:
        title = brand_name
    else:
        title = "Website"

    # Truncate title to 60 chars
    if len(title) > 60:
        title = title[:57] + "..."

    # Build description (120-160 chars)
    if not description and tagline:
        description = tagline
    if not description:
        # Build from sections
        sections = plan.get("sections", [])
        section_types = [s.get("type", "") for s in sections]
        description = f"{brand_name or 'Our'} website featuring {', '.join(section_types[:4])}."

    if len(description) > 160:
        description = description[:157] + "..."

    # Extract primary color for theme-color
    tokens = plan.get("design_tokens", plan.get("tokens", {}))
    primary_color = tokens.get("primary_color", tokens.get("primary", "#2563eb"))

    tags = []

    # Basic SEO
    tags.append(f'<title>{_escape_html(title)}</title>')
    tags.append(f'<meta name="description" content="{_escape_attr(description)}">')
    tags.append('<meta name="robots" content="index, follow">')
    tags.append(f'<meta name="theme-color" content="{_escape_attr(primary_color)}">')

    # Open Graph
    tags.append(f'<meta property="og:title" content="{_escape_attr(title)}">')
    tags.append(f'<meta property="og:description" content="{_escape_attr(description)}">')
    tags.append('<meta property="og:type" content="website">')
    if brand_name:
        tags.append(f'<meta property="og:site_name" content="{_escape_attr(brand_name)}">')

    # Twitter Card
    tags.append('<meta name="twitter:card" content="summary_large_image">')
    tags.append(f'<meta name="twitter:title" content="{_escape_attr(title)}">')
    tags.append(f'<meta name="twitter:description" content="{_escape_attr(description)}">')

    # JSON-LD Organization schema
    org_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": brand_name or "Organization",
    }
    if tagline:
        org_schema["description"] = tagline

    tags.append(
        f'<script type="application/ld+json">{json.dumps(org_schema, ensure_ascii=False)}</script>'
    )

    return "\n    ".join(tags)


# ---------------------------------------------------------------------------
# 3. inject_seo_into_html
# ---------------------------------------------------------------------------

def inject_seo_into_html(html: str, seo_tags: str) -> str:
    """
    Inject SEO tags into existing HTML <head>, avoiding duplicates.

    Only adds tags that are not already present.
    """
    if not seo_tags:
        return html

    lines = seo_tags.split("\n")
    to_inject = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip if a similar tag already exists
        if line.startswith("<title") and re.search(r'<title[^>]*>.+</title>', html, re.I | re.S):
            continue
        if 'name="description"' in line and re.search(r'<meta[^>]+name\s*=\s*["\']description["\']', html, re.I):
            continue
        if 'name="robots"' in line and re.search(r'<meta[^>]+name\s*=\s*["\']robots["\']', html, re.I):
            continue
        if 'name="theme-color"' in line and re.search(r'<meta[^>]+name\s*=\s*["\']theme-color["\']', html, re.I):
            continue
        if 'property="og:' in line:
            prop_match = re.search(r'property="(og:[^"]+)"', line)
            if prop_match and re.search(
                rf'<meta[^>]+property\s*=\s*["\']' + re.escape(prop_match.group(1)) + r'["\']',
                html, re.I,
            ):
                continue
        if 'name="twitter:' in line:
            name_match = re.search(r'name="(twitter:[^"]+)"', line)
            if name_match and re.search(
                rf'<meta[^>]+name\s*=\s*["\']' + re.escape(name_match.group(1)) + r'["\']',
                html, re.I,
            ):
                continue
        if 'application/ld+json' in line and re.search(
            r'<script[^>]+type\s*=\s*["\']application/ld\+json["\']', html, re.I,
        ):
            continue

        to_inject.append(line)

    if not to_inject:
        return html

    injection = "\n    " + "\n    ".join(to_inject)

    # Inject before </head>
    head_close = re.search(r'</head>', html, re.I)
    if head_close:
        pos = head_close.start()
        return html[:pos] + injection + "\n" + html[pos:]

    # Fallback: inject after <head>
    head_open = re.search(r'<head[^>]*>', html, re.I)
    if head_open:
        pos = head_open.end()
        return html[:pos] + injection + html[pos:]

    # No head at all — prepend
    return injection + "\n" + html


# ---------------------------------------------------------------------------
# 4. generate_sitemap / robots.txt
# ---------------------------------------------------------------------------

def generate_sitemap(pages: list[dict], domain: str = "") -> str:
    """
    Generate sitemap.xml content.

    pages: list of {"slug": "/", "title": "Home", ...}
    """
    base = domain.rstrip("/") if domain else "https://example.com"

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for page in pages:
        slug = page.get("slug", "/")
        url = f"{base}{slug}" if slug != "/" else base + "/"
        priority = "1.0" if slug == "/" else "0.8"
        xml_lines.append(f"  <url>")
        xml_lines.append(f"    <loc>{_escape_xml(url)}</loc>")
        xml_lines.append(f"    <priority>{priority}</priority>")
        xml_lines.append(f"  </url>")

    xml_lines.append("</urlset>")
    return "\n".join(xml_lines)


def generate_robots_txt(domain: str = "") -> str:
    """Generate robots.txt content."""
    base = domain.rstrip("/") if domain else ""
    sitemap_line = f"\nSitemap: {base}/sitemap.xml" if base else ""
    return f"User-agent: *\nAllow: /{sitemap_line}\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
        .replace('"', "&quot;")
    )
