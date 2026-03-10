"""
Image optimization utilities for generated HTML.

Adds lazy loading, responsive srcsets, WebP hints, and fetchpriority
to image tags. Pure regex-based — no external parser dependencies.
"""

import re

# ---------------------------------------------------------------------------
# Known image CDN patterns that support size parameters
# ---------------------------------------------------------------------------

_UNSPLASH_RE = re.compile(r'(images\.unsplash\.com/photo[^"\'>\s]+)', re.I)
_PEXELS_RE = re.compile(r'(images\.pexels\.com/photos/[^"\'>\s]+)', re.I)
_PIXABAY_RE = re.compile(r'(pixabay\.com/get/[^"\'>\s]+)', re.I)

# Standard responsive widths
_RESPONSIVE_WIDTHS = [400, 800, 1200, 1600]


# ---------------------------------------------------------------------------
# 1. optimize_image_tags
# ---------------------------------------------------------------------------


def optimize_image_tags(html: str) -> str:
    """
    Optimize image tags in generated HTML.

    - Adds loading="lazy" + decoding="async" to images below the fold (skip first 2)
    - Adds fetchpriority="high" to first image
    - Adds width/height hints from URL params if available
    - Wraps images with responsive srcset for known CDNs
    """
    img_count = 0

    def _optimize_single_img(m):
        nonlocal img_count
        img_count += 1
        tag = m.group(0)

        # ── First image: fetchpriority="high" ──
        if img_count == 1:
            if "fetchpriority=" not in tag.lower():
                tag = tag[:-1] + ' fetchpriority="high">'

        # ── Below-fold images: lazy loading ──
        if img_count > 2:
            if "loading=" not in tag.lower():
                tag = tag[:-1] + ' loading="lazy">'
            if "decoding=" not in tag.lower():
                tag = tag[:-1] + ' decoding="async">'

        # ── Add srcset for known CDN images ──
        src_match = re.search(r'src\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if src_match and "srcset=" not in tag.lower():
            src = src_match.group(1)
            srcset = generate_image_srcset(src)
            if srcset:
                tag = (
                    tag[:-1]
                    + f' srcset="{srcset}" sizes="(max-width: 640px) 400px, (max-width: 1024px) 800px, 1200px">'
                )

        # ── Add width/height from URL hints ──
        if "width=" not in tag.lower() and "w-full" not in tag and "w-screen" not in tag:
            if src_match:
                dims = _extract_dimensions_from_url(src_match.group(1))
                if dims:
                    w, h = dims
                    tag = tag[:-1] + f' width="{w}" height="{h}">'

        return tag

    return re.sub(r"<img\b[^>]*>", _optimize_single_img, html, flags=re.I | re.S)


# ---------------------------------------------------------------------------
# 2. generate_image_srcset
# ---------------------------------------------------------------------------


def generate_image_srcset(url: str) -> str:
    """
    Generate srcset attribute for responsive images.

    For Unsplash/Pexels URLs, generates multiple size variants.
    Returns empty string if URL is not from a supported CDN.
    """
    # Unsplash: supports ?w=WIDTH parameter
    if "images.unsplash.com" in url:
        return _build_unsplash_srcset(url)

    # Pexels: supports ?auto=compress&w=WIDTH
    if "images.pexels.com" in url:
        return _build_pexels_srcset(url)

    return ""


# ---------------------------------------------------------------------------
# 3. generate_picture_element
# ---------------------------------------------------------------------------


def generate_picture_element(img_tag: str) -> str:
    """
    Wrap an <img> tag in a <picture> element with WebP source.

    Only works for known CDNs that support format conversion.
    Falls back to returning the original tag if not supported.
    """
    src_match = re.search(r'src\s*=\s*["\']([^"\']+)["\']', img_tag, re.I)
    if not src_match:
        return img_tag

    src = src_match.group(1)

    # Unsplash supports &fm=webp
    if "images.unsplash.com" in src:
        webp_src = _add_url_param(src, "fm", "webp")
        return f'<picture>\n  <source type="image/webp" srcset="{webp_src}">\n  {img_tag}\n</picture>'

    return img_tag


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_unsplash_srcset(url: str) -> str:
    """Build srcset for Unsplash URLs using ?w= parameter."""
    # Strip existing w= parameter
    base = re.sub(r"[?&]w=\d+", "", url)
    sep = "&" if "?" in base else "?"

    parts = []
    for w in _RESPONSIVE_WIDTHS:
        parts.append(f"{base}{sep}w={w}&q=80 {w}w")
        sep = "&" if "?" in base else "?"

    return ", ".join(parts)


def _build_pexels_srcset(url: str) -> str:
    """Build srcset for Pexels URLs using ?w= parameter."""
    base = re.sub(r"[?&]w=\d+", "", url)
    base = re.sub(r"[?&]h=\d+", "", base)
    sep = "&" if "?" in base else "?"

    parts = []
    for w in _RESPONSIVE_WIDTHS:
        parts.append(f"{base}{sep}auto=compress&w={w} {w}w")

    return ", ".join(parts)


def _extract_dimensions_from_url(url: str) -> tuple[int, int] | None:
    """Try to extract width/height from URL query parameters."""
    w_match = re.search(r"[?&]w=(\d+)", url)
    h_match = re.search(r"[?&]h=(\d+)", url)

    if w_match and h_match:
        return int(w_match.group(1)), int(h_match.group(1))

    # Common Unsplash default aspect ratio
    if w_match and "unsplash.com" in url:
        w = int(w_match.group(1))
        return w, int(w * 0.667)  # 3:2 aspect ratio default

    return None


def _add_url_param(url: str, key: str, value: str) -> str:
    """Add or replace a URL query parameter."""
    pattern = rf"([?&]){re.escape(key)}=[^&]*"
    if re.search(pattern, url):
        return re.sub(pattern, rf"\g<1>{key}={value}", url)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{key}={value}"
