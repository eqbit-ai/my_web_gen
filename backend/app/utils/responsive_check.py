"""
Responsive quality checker and auto-fixer for generated HTML/CSS.

Validates generated output for common responsive/quality issues
and auto-fixes the ones that can be safely corrected.
"""

import re

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_inline_styles(html: str) -> list[dict]:
    """Pull every style='...' from the HTML with its tag context."""
    results = []
    for m in re.finditer(r'<(\w+)([^>]*?)\bstyle\s*=\s*["\']([^"\']*)["\']', html, re.I | re.S):
        results.append(
            {
                "tag": m.group(1).lower(),
                "attrs": m.group(2),
                "style": m.group(3),
                "start": m.start(),
                "end": m.end(),
                "full_match": m.group(0),
            }
        )
    return results


def _extract_css_rules(css: str) -> list[dict]:
    """Rough parse of CSS rules into selector + declarations."""
    rules = []
    # Strip comments
    cleaned = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    # Match top-level and @media blocks
    for m in re.finditer(r"([^{}]+)\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", cleaned):
        selector = m.group(1).strip()
        body = m.group(2).strip()
        rules.append({"selector": selector, "body": body})
    return rules


def _parse_px(value: str) -> int | None:
    """Extract integer from a px value like '800px'."""
    m = re.match(r"(\d+)\s*px", value.strip())
    return int(m.group(1)) if m else None


def _has_tailwind_responsive(html: str) -> bool:
    """Check if any Tailwind responsive prefixes are used."""
    return bool(re.search(r"\b(sm|md|lg|xl|2xl):", html))


def _color_to_rgb(color: str) -> tuple[int, int, int] | None:
    """Convert hex color to RGB tuple. Returns None if not parseable."""
    color = color.strip().lower()
    # #rgb
    m = re.match(r"^#([0-9a-f])([0-9a-f])([0-9a-f])$", color)
    if m:
        return tuple(int(c * 2, 16) for c in m.groups())
    # #rrggbb
    m = re.match(r"^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$", color)
    if m:
        return tuple(int(c, 16) for c in m.groups())
    return None


def _relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG relative luminance."""
    srgb = []
    for c in (r, g, b):
        s = c / 255.0
        srgb.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2]


def _contrast_ratio(c1: tuple, c2: tuple) -> float:
    l1 = _relative_luminance(*c1)
    l2 = _relative_luminance(*c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# 1. check_responsive
# ---------------------------------------------------------------------------


def check_responsive(html: str, css: str) -> dict:
    """
    Analyze HTML + CSS for responsive / quality issues.

    Returns dict with score (0-100), issues list, and auto_fixed count.
    """
    issues: list[dict] = []
    combined = html + "\n" + css

    # --- Missing viewport meta tag ---
    if not re.search(r'<meta[^>]+name\s*=\s*["\']viewport["\']', html, re.I):
        issues.append(
            {
                "type": "missing_viewport",
                "severity": "critical",
                "fix": "auto",
            }
        )

    # --- Fixed pixel widths on containers (>600px without max-width) ---
    # Check inline styles
    for item in _extract_inline_styles(html):
        style = item["style"]
        w_match = re.search(r"\bwidth\s*:\s*(\d+)\s*px", style)
        if w_match:
            px = int(w_match.group(1))
            if px > 600 and "max-width" not in style:
                issues.append(
                    {
                        "type": "fixed_width",
                        "severity": "warning",
                        "element": f"<{item['tag']}> with width:{px}px",
                        "fix": "auto",
                    }
                )

    # Check CSS rules for fixed widths
    for rule in _extract_css_rules(css):
        w_match = re.search(r"\bwidth\s*:\s*(\d+)\s*px", rule["body"])
        if w_match:
            px = int(w_match.group(1))
            if px > 600 and "max-width" not in rule["body"]:
                issues.append(
                    {
                        "type": "fixed_width",
                        "severity": "warning",
                        "element": rule["selector"].strip(),
                        "fix": "suggestion",
                    }
                )

    # --- Images without max-width:100% or w-full ---
    img_tags = re.findall(r"<img\b[^>]*>", html, re.I | re.S)
    for img in img_tags:
        has_responsive = (
            "max-width" in img or "w-full" in img or "max-w-" in img or "w-screen" in img or "object-fit" in img
        )
        if not has_responsive:
            # Also check if there's a CSS rule targeting img
            img_rule_exists = bool(re.search(r"\bimg\b[^{]*\{[^}]*max-width", css, re.I))
            if not img_rule_exists:
                src_match = re.search(r'src\s*=\s*["\']([^"\']*)["\']', img)
                src = src_match.group(1)[:40] if src_match else "unknown"
                issues.append(
                    {
                        "type": "image_no_max_width",
                        "severity": "warning",
                        "element": f"img[src='{src}']",
                        "fix": "auto",
                    }
                )

    # --- Font sizes below 14px on body text ---
    small_fonts = re.findall(r"font-size\s*:\s*(\d+)\s*px", combined)
    for size_str in small_fonts:
        size = int(size_str)
        if size < 14:
            issues.append(
                {
                    "type": "small_font",
                    "severity": "warning",
                    "element": f"font-size: {size}px",
                    "fix": "suggestion",
                }
            )

    # --- Touch targets (buttons/links with small padding) ---
    for m in re.finditer(r'<(button|a)\b[^>]*style\s*=\s*["\']([^"\']*)["\']', html, re.I | re.S):
        tag = m.group(1).lower()
        style = m.group(2)
        padding_match = re.search(r"padding\s*:\s*(\d+)", style)
        if padding_match:
            pad = int(padding_match.group(1))
            if pad < 8:
                issues.append(
                    {
                        "type": "small_touch_target",
                        "severity": "warning",
                        "element": f"<{tag}> with padding:{pad}px",
                        "fix": "suggestion",
                    }
                )

    # --- Horizontal overflow potential ---
    has_overflow_hidden = bool(re.search(r"(body|html|\*)[^{]*\{[^}]*overflow-x\s*:\s*hidden", css, re.I))
    if not has_overflow_hidden:
        # Check for wide absolute/fixed positioned elements
        if re.search(r"(position\s*:\s*(absolute|fixed)[^}]*width\s*:\s*\d{4,})", combined, re.I):
            issues.append(
                {
                    "type": "horizontal_overflow",
                    "severity": "warning",
                    "fix": "auto",
                }
            )

    # --- Missing responsive Tailwind classes ---
    if not _has_tailwind_responsive(html):
        # Only flag if Tailwind classes are used at all
        if re.search(r"\b(flex|grid|p-\d|m-\d|text-\w+|bg-\w+)\b", html):
            issues.append(
                {
                    "type": "no_responsive_classes",
                    "severity": "info",
                    "fix": "suggestion",
                }
            )

    # --- Text overflow / long words ---
    if not re.search(r"(overflow-wrap|word-break|break-words|break-all)", combined, re.I):
        issues.append(
            {
                "type": "text_overflow_risk",
                "severity": "info",
                "fix": "auto",
            }
        )

    # --- Nav without mobile fallback ---
    has_nav = bool(re.search(r"<nav\b", html, re.I))
    if has_nav:
        has_mobile_menu = bool(
            re.search(
                r"(hamburger|mobile-menu|menu-toggle|nav-toggle|burger|md:hidden|lg:hidden|menu-btn|mobile-nav)",
                html,
                re.I,
            )
        )
        if not has_mobile_menu:
            issues.append(
                {
                    "type": "no_mobile_menu",
                    "severity": "warning",
                    "fix": "suggestion",
                }
            )

    # --- Missing alt attributes on images ---
    for img in img_tags:
        if not re.search(r"\balt\s*=", img, re.I):
            src_match = re.search(r'src\s*=\s*["\']([^"\']*)["\']', img)
            src = src_match.group(1)[:40] if src_match else "unknown"
            issues.append(
                {
                    "type": "missing_alt",
                    "severity": "warning",
                    "element": f"img[src='{src}']",
                    "fix": "auto",
                }
            )

    # --- Contrast issues (CSS custom properties) ---
    color_vars = {}
    for m in re.finditer(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", combined):
        color_vars[m.group(1)] = m.group(2)

    # Try to detect light-on-light or dark-on-dark
    text_keys = [k for k in color_vars if any(w in k for w in ("text", "foreground", "heading", "body"))]
    bg_keys = [k for k in color_vars if any(w in k for w in ("bg", "background", "surface"))]
    for tk in text_keys:
        tc = _color_to_rgb(color_vars[tk])
        if not tc:
            continue
        for bk in bg_keys:
            bc = _color_to_rgb(color_vars[bk])
            if not bc:
                continue
            ratio = _contrast_ratio(tc, bc)
            if ratio < 3.0:
                issues.append(
                    {
                        "type": "low_contrast",
                        "severity": "warning",
                        "element": f"--{tk} on --{bk} (ratio {ratio:.1f}:1)",
                        "fix": "suggestion",
                    }
                )

    # --- Body overflow-x: hidden missing (general) ---
    if not has_overflow_hidden and "horizontal_overflow" not in [i["type"] for i in issues]:
        issues.append(
            {
                "type": "missing_overflow_hidden",
                "severity": "info",
                "fix": "auto",
            }
        )

    # --- Score calculation ---
    auto_fixable = sum(1 for i in issues if i["fix"] == "auto")
    severity_weights = {"critical": 15, "warning": 5, "info": 2}
    deductions = sum(severity_weights.get(i["severity"], 2) for i in issues)
    # Auto-fixable issues count at half weight
    auto_deductions = sum(severity_weights.get(i["severity"], 2) * 0.5 for i in issues if i["fix"] == "auto")
    effective_deductions = deductions - auto_deductions
    score = max(0, min(100, round(100 - effective_deductions)))

    return {
        "score": score,
        "issues": issues,
        "auto_fixed": auto_fixable,
    }


# ---------------------------------------------------------------------------
# 2. auto_fix_responsive
# ---------------------------------------------------------------------------


def auto_fix_responsive(html: str, css: str) -> tuple[str, str]:
    """
    Auto-fix common responsive issues in HTML and CSS.
    Returns (fixed_html, fixed_css).
    """
    fixed_html = html
    fixed_css = css

    # --- Ensure viewport meta tag ---
    if not re.search(r'<meta[^>]+name\s*=\s*["\']viewport["\']', fixed_html, re.I):
        viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        head_match = re.search(r"(<head[^>]*>)", fixed_html, re.I)
        if head_match:
            insert_pos = head_match.end()
            fixed_html = fixed_html[:insert_pos] + "\n    " + viewport_tag + fixed_html[insert_pos:]
        else:
            # No <head> tag — prepend before first tag
            fixed_html = viewport_tag + "\n" + fixed_html

    # --- Add max-width: 100% to images missing it ---
    # Check if there's already a global img rule in CSS
    has_img_rule = bool(re.search(r"\bimg\b[^{]*\{[^}]*max-width", fixed_css, re.I))
    if not has_img_rule:
        # Add a global img rule to the CSS
        img_rule = "\nimg { max-width: 100%; height: auto; }\n"
        fixed_css = img_rule + fixed_css

    # --- Add overflow-x: hidden to body ---
    if not re.search(r"(body|html|\*)[^{]*\{[^}]*overflow-x\s*:\s*hidden", fixed_css, re.I):
        body_match = re.search(r"(body\s*\{)", fixed_css, re.I)
        if body_match:
            insert_pos = body_match.end()
            fixed_css = fixed_css[:insert_pos] + "\n    overflow-x: hidden;" + fixed_css[insert_pos:]
        else:
            fixed_css = "body { overflow-x: hidden; }\n" + fixed_css

    # --- Convert fixed px widths to max-width in inline styles ---
    def _fix_inline_width(m):
        tag = m.group(1)
        before_style = m.group(2)
        style = m.group(3)
        w_match = re.search(r"\bwidth\s*:\s*(\d+)\s*px", style)
        if w_match and int(w_match.group(1)) > 600 and "max-width" not in style:
            px_val = w_match.group(1)
            style = re.sub(
                r"\bwidth\s*:\s*" + px_val + r"\s*px",
                f"width: 100%; max-width: {px_val}px",
                style,
            )
        return f'<{tag}{before_style}style="{style}"'

    fixed_html = re.sub(
        r'<(\w+)([^>]*?)\bstyle\s*=\s*["\']([^"\']*)["\']',
        _fix_inline_width,
        fixed_html,
        flags=re.I | re.S,
    )

    # --- Convert fixed px widths in CSS rules ---
    def _fix_css_width(m):
        full = m.group(0)
        selector = m.group(1)
        body = m.group(2)
        w_match = re.search(r"\bwidth\s*:\s*(\d+)\s*px", body)
        if w_match and int(w_match.group(1)) > 600 and "max-width" not in body:
            px_val = w_match.group(1)
            body = re.sub(
                r"\bwidth\s*:\s*" + px_val + r"\s*px",
                f"width: 100%; max-width: {px_val}px",
                body,
            )
            return f"{selector}{{{body}}}"
        return full

    # Only fix top-level rules (not inside @media)
    fixed_css = re.sub(
        r"([^{}@]+)\{([^{}]*)\}",
        _fix_css_width,
        fixed_css,
    )

    # --- Add word-wrap safety ---
    if not re.search(r"(overflow-wrap|word-break|break-words)", fixed_css, re.I):
        body_match = re.search(r"(body\s*\{[^}]*)", fixed_css, re.I)
        if body_match:
            insert_pos = body_match.end()
            fixed_css = fixed_css[:insert_pos] + "\n    overflow-wrap: break-word;" + fixed_css[insert_pos:]

    # --- Add basic mobile media query if none exist ---
    has_media_query = bool(re.search(r"@media\s*\(", fixed_css, re.I))
    if not has_media_query:
        mobile_mq = """
@media (max-width: 768px) {
    .container, [class*="container"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    h1 { font-size: 1.75rem; }
    h2 { font-size: 1.5rem; }
    .grid { grid-template-columns: 1fr !important; }
    .flex { flex-wrap: wrap; }
}
"""
        fixed_css += mobile_mq

    # --- Add loading="lazy" to images below the fold ---
    img_count = 0

    def _add_lazy(m):
        nonlocal img_count
        img_count += 1
        tag = m.group(0)
        # Skip first 2 images (above the fold)
        if img_count <= 2:
            return tag
        # Don't add if already present
        if "loading=" in tag:
            return tag
        return tag[:-1] + ' loading="lazy">'

    fixed_html = re.sub(r"<img\b[^>]*>", _add_lazy, fixed_html, flags=re.I | re.S)

    # --- Add alt="" to images missing alt ---
    def _add_alt(m):
        tag = m.group(0)
        if not re.search(r"\balt\s*=", tag, re.I):
            return tag[:-1] + ' alt="">'
        return tag

    fixed_html = re.sub(r"<img\b[^>]*>", _add_alt, fixed_html, flags=re.I | re.S)

    return fixed_html, fixed_css


# ---------------------------------------------------------------------------
# 3. generate_fix_suggestions
# ---------------------------------------------------------------------------


def generate_fix_suggestions(issues: list[dict]) -> str:
    """
    Generate a prompt string for the LLM to fix remaining
    non-auto-fixable issues.
    """
    non_auto = [i for i in issues if i["fix"] != "auto"]
    if not non_auto:
        return ""

    lines = ["Fix these responsive issues in the HTML/CSS:\n"]

    type_descriptions = {
        "fixed_width": "uses a fixed pixel width that will break on smaller screens. Convert to responsive width (e.g. max-width + width:100% or Tailwind w-full max-w-*)",
        "small_font": "has a font-size below 14px which is too small for mobile readability. Increase to at least 14px / text-sm",
        "small_touch_target": "is too small for touch interaction (minimum 44x44px). Increase padding to at least p-3 / 12px",
        "no_responsive_classes": "No Tailwind responsive breakpoints (sm:/md:/lg:) are used. Add responsive classes for grid columns, font sizes, padding, and layout changes",
        "no_mobile_menu": "Navigation has no mobile menu fallback. Add a hamburger toggle that shows/hides nav links on mobile (hidden md:flex pattern)",
        "low_contrast": "has insufficient color contrast (below 3:1 ratio). Adjust colors to meet WCAG AA standards",
    }

    for idx, issue in enumerate(non_auto, 1):
        itype = issue["type"]
        element = issue.get("element", "")
        desc = type_descriptions.get(itype, f"has a {itype} issue")

        if element:
            lines.append(f"{idx}. `{element}` {desc}")
        else:
            lines.append(f"{idx}. {desc}")

    lines.append("\nApply fixes while preserving the existing design and layout.")

    return "\n".join(lines)
