"""
Multi-page site support (preparation module).

Converts single-page plans into multi-page structures, generates
inter-page navigation, and links pages together. This is groundwork
for future multi-page generation — currently used for planning only.
"""

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Section type → page mapping
# ---------------------------------------------------------------------------

_SECTION_PAGE_MAP = {
    # Sections that stay on home page
    "hero": "/",
    "cta": "/",
    "testimonials": "/",
    "stats": "/",
    "partners": "/",
    "clients": "/",
    "logos": "/",
    "newsletter": "/",
    "faq": "/",

    # Sections that can become their own page
    "about": "/about",
    "team": "/about",
    "history": "/about",
    "mission": "/about",
    "values": "/about",

    "services": "/services",
    "features": "/services",
    "solutions": "/services",
    "products": "/services",

    "pricing": "/pricing",
    "plans": "/pricing",

    "contact": "/contact",
    "map": "/contact",
    "location": "/contact",

    "blog": "/blog",
    "news": "/blog",
    "articles": "/blog",

    "portfolio": "/portfolio",
    "gallery": "/portfolio",
    "projects": "/portfolio",
    "work": "/portfolio",
    "case-studies": "/portfolio",
}

# Minimum sections to warrant splitting to a separate page
_MIN_SECTIONS_FOR_SPLIT = 2


# ---------------------------------------------------------------------------
# 1. plan_site_pages
# ---------------------------------------------------------------------------

def plan_site_pages(plan: dict) -> list[dict]:
    """
    Convert a single-page plan into multi-page structure.

    Groups sections logically by type. Only creates separate pages
    when there are enough sections to justify it.

    Returns list of page dicts:
      [{"slug": "/", "title": "Home", "sections": [...]}, ...]
    """
    sections = plan.get("sections", [])
    brand = plan.get("brand", {})
    brand_name = brand.get("name", "Website")

    # Group sections by target page
    page_sections: dict[str, list] = {"/": []}
    for section in sections:
        stype = section.get("type", "").lower().strip()
        target_page = _SECTION_PAGE_MAP.get(stype, "/")
        if target_page not in page_sections:
            page_sections[target_page] = []
        page_sections[target_page].append(section)

    # Build page list — only create separate pages if enough sections
    pages = []

    # Home page always exists
    home_sections = list(page_sections.get("/", []))

    # Merge small pages back into home
    for slug, secs in list(page_sections.items()):
        if slug == "/":
            continue
        if len(secs) < _MIN_SECTIONS_FOR_SPLIT:
            home_sections.extend(secs)
        else:
            page_title = _slug_to_title(slug)
            pages.append({
                "slug": slug,
                "title": page_title,
                "sections": secs,
                "meta": {
                    "title": f"{page_title} — {brand_name}",
                    "description": f"{page_title} page for {brand_name}",
                },
            })

    # Home is always first
    pages.insert(0, {
        "slug": "/",
        "title": "Home",
        "sections": home_sections,
        "meta": {
            "title": brand_name,
            "description": brand.get("tagline", f"Welcome to {brand_name}"),
        },
    })

    return pages


# ---------------------------------------------------------------------------
# 2. generate_navigation
# ---------------------------------------------------------------------------

def generate_navigation(pages: list[dict], brand_name: str = "") -> str:
    """
    Generate nav HTML for multi-page site.

    Returns an HTML <nav> element with links to all pages.
    """
    if not pages:
        return ""

    links = []
    for page in pages:
        slug = page["slug"]
        title = page["title"]
        href = slug if slug != "/" else "/"
        is_home = slug == "/"

        if is_home:
            links.append(f'<a href="{href}" class="nav-link active">{title}</a>')
        else:
            links.append(f'<a href="{href}" class="nav-link">{title}</a>')

    logo = brand_name or "Home"

    nav_html = f'''<nav class="site-nav flex items-center justify-between px-6 py-4">
    <a href="/" class="nav-logo font-bold text-xl">{_escape_html(logo)}</a>
    <div class="nav-links flex gap-6">
        {chr(10) + "        ".join(links)}
    </div>
    <button class="nav-toggle md:hidden" aria-label="Toggle menu">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
    </button>
</nav>'''

    return nav_html


# ---------------------------------------------------------------------------
# 3. link_pages
# ---------------------------------------------------------------------------

def link_pages(pages: dict[str, str]) -> dict[str, str]:
    """
    Add internal navigation links between pages.

    Args:
        pages: dict mapping slug → HTML content

    Returns:
        dict mapping slug → updated HTML with inter-page links
    """
    if len(pages) <= 1:
        return pages

    # Build nav for all pages
    page_list = [{"slug": slug, "title": _slug_to_title(slug)} for slug in pages]
    nav_html = generate_navigation(page_list)

    linked = {}
    for slug, html in pages.items():
        # If page already has a <nav>, update links inside it
        if re.search(r'<nav\b', html, re.I):
            # Add links to existing nav items
            for target_slug in pages:
                if target_slug == slug:
                    continue
                title = _slug_to_title(target_slug)
                href = target_slug if target_slug != "/" else "/"
                # Check if this link already exists
                if href not in html or f'"{href}"' not in html:
                    # Find the nav links container and append
                    nav_match = re.search(
                        r'(<nav\b[^>]*>)(.*?)(</nav>)',
                        html,
                        re.I | re.S,
                    )
                    if nav_match:
                        nav_content = nav_match.group(2)
                        new_link = f' <a href="{href}" class="nav-link">{_escape_html(title)}</a>'
                        updated_nav = nav_match.group(1) + nav_content + new_link + nav_match.group(3)
                        html = html[:nav_match.start()] + updated_nav + html[nav_match.end():]
        else:
            # No nav exists — inject one after <body>
            body_match = re.search(r'(<body[^>]*>)', html, re.I)
            if body_match:
                pos = body_match.end()
                html = html[:pos] + "\n" + nav_html + "\n" + html[pos:]

        # Mark current page's nav link as active
        current_href = slug if slug != "/" else "/"
        html = re.sub(
            rf'(<a[^>]+href\s*=\s*["\']){re.escape(current_href)}(["\'][^>]*class\s*=\s*["\'][^"\']*)',
            lambda m: m.group(0) + " active" if "active" not in m.group(0) else m.group(0),
            html,
            flags=re.I,
        )

        linked[slug] = html

    return linked


# ---------------------------------------------------------------------------
# 4. get_page_count_estimate
# ---------------------------------------------------------------------------

def get_page_count_estimate(plan: dict) -> int:
    """
    Estimate how many pages the plan would generate.
    Useful for UI hints without running full page planning.
    """
    pages = plan_site_pages(plan)
    return len(pages)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug_to_title(slug: str) -> str:
    """Convert a URL slug to a page title."""
    if slug == "/":
        return "Home"
    name = slug.strip("/").split("/")[-1]
    return name.replace("-", " ").replace("_", " ").title()


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
