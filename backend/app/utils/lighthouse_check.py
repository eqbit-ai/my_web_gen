"""
Lightweight performance checker for generated websites.

Pure Python analysis — no Lighthouse dependency. Checks for common
performance, accessibility, and HTML structure issues. Fast (<50ms).
"""

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _color_to_rgb(color: str) -> Optional[tuple[int, int, int]]:
    """Convert hex color to RGB tuple."""
    color = color.strip().lower()
    m = re.match(r'^#([0-9a-f])([0-9a-f])([0-9a-f])$', color)
    if m:
        return tuple(int(c * 2, 16) for c in m.groups())
    m = re.match(r'^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$', color)
    if m:
        return tuple(int(c, 16) for c in m.groups())
    return None


def _relative_luminance(r: int, g: int, b: int) -> float:
    srgb = []
    for c in (r, g, b):
        s = c / 255.0
        srgb.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2]


def _contrast_ratio(c1: tuple, c2: tuple) -> float:
    l1 = _relative_luminance(*c1)
    l2 = _relative_luminance(*c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# 1. check_performance
# ---------------------------------------------------------------------------

def check_performance(html: str, css: str, js: str) -> dict:
    """
    Analyze generated website for performance issues.

    Returns dict with:
      - score (0-100)
      - issues (list of issue dicts)
      - passed (list of passed check names)
      - auto_fixable (list of auto-fixable issues)
    """
    issues = []
    passed = []

    # ── Check 1: Image optimization ──────────────────────────────────
    img_tags = re.findall(r'<img\b[^>]*>', html, re.I | re.S)
    imgs_missing_lazy = 0
    imgs_missing_alt = 0
    imgs_missing_dimensions = 0

    for idx, img in enumerate(img_tags):
        # Skip first 2 (above-the-fold)
        if idx >= 2 and 'loading=' not in img.lower():
            imgs_missing_lazy += 1
        if not re.search(r'\balt\s*=', img, re.I):
            imgs_missing_alt += 1
        if not re.search(r'\b(width|w-)\s*=', img, re.I) and 'w-full' not in img:
            if not re.search(r'\bheight\s*=', img, re.I):
                imgs_missing_dimensions += 1

    if imgs_missing_lazy > 0:
        issues.append({
            "category": "images",
            "type": "missing_lazy_loading",
            "severity": "warning",
            "message": f"{imgs_missing_lazy} image(s) below fold missing loading=\"lazy\"",
            "auto_fix": True,
        })
    else:
        passed.append("image_lazy_loading")

    if imgs_missing_alt > 0:
        issues.append({
            "category": "images",
            "type": "missing_alt",
            "severity": "warning",
            "message": f"{imgs_missing_alt} image(s) missing alt attribute",
            "auto_fix": True,
        })
    else:
        passed.append("image_alt_attributes")

    if imgs_missing_dimensions > 0:
        issues.append({
            "category": "images",
            "type": "missing_dimensions",
            "severity": "info",
            "message": f"{imgs_missing_dimensions} image(s) missing width/height (causes layout shift)",
            "auto_fix": False,
        })
    else:
        passed.append("image_dimensions")

    # ── Check 2: CSS efficiency ──────────────────────────────────────
    # Count CSS rules
    css_cleaned = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css_selectors = re.findall(r'([^{}]+)\{', css_cleaned)
    selector_list = [s.strip() for s in css_selectors if s.strip() and not s.strip().startswith('@')]

    # Duplicate selectors
    seen_selectors = {}
    duplicate_count = 0
    for sel in selector_list:
        normalized = re.sub(r'\s+', ' ', sel).strip()
        if normalized in seen_selectors:
            duplicate_count += 1
        else:
            seen_selectors[normalized] = True

    if duplicate_count > 0:
        issues.append({
            "category": "css",
            "type": "duplicate_selectors",
            "severity": "info",
            "message": f"{duplicate_count} duplicate CSS selector(s) found",
            "auto_fix": True,
        })
    else:
        passed.append("no_duplicate_css")

    # !important usage
    important_count = len(re.findall(r'!important', css, re.I))
    if important_count > 5:
        issues.append({
            "category": "css",
            "type": "excessive_important",
            "severity": "warning",
            "message": f"{important_count} !important declarations (should be <5)",
            "auto_fix": False,
        })
    else:
        passed.append("limited_important_usage")

    # ── Check 3: JS efficiency ───────────────────────────────────────
    if js:
        # console.log statements
        console_logs = len(re.findall(r'\bconsole\.(log|debug|info)\s*\(', js))
        if console_logs > 0:
            issues.append({
                "category": "js",
                "type": "console_logs",
                "severity": "info",
                "message": f"{console_logs} console.log statement(s) in production code",
                "auto_fix": True,
            })
        else:
            passed.append("no_console_logs")

        # querySelectorAll in loops
        if re.search(r'(for|while)\s*\([^)]*\)[^{]*\{[^}]*querySelectorAll', js, re.S):
            issues.append({
                "category": "js",
                "type": "query_in_loop",
                "severity": "warning",
                "message": "querySelectorAll called inside a loop (cache the result)",
                "auto_fix": False,
            })
        else:
            passed.append("no_dom_queries_in_loops")

        # Passive event listeners for scroll/touch
        scroll_listeners = re.findall(
            r'addEventListener\s*\(\s*["\'](?:scroll|touchstart|touchmove|wheel)["\']',
            js
        )
        passive_listeners = re.findall(
            r'addEventListener\s*\(\s*["\'](?:scroll|touchstart|touchmove|wheel)["\'][^)]*passive\s*:\s*true',
            js
        )
        if len(scroll_listeners) > len(passive_listeners):
            issues.append({
                "category": "js",
                "type": "non_passive_listeners",
                "severity": "info",
                "message": f"{len(scroll_listeners) - len(passive_listeners)} scroll/touch listener(s) should use {{passive: true}}",
                "auto_fix": False,
            })
        else:
            passed.append("passive_scroll_listeners")
    else:
        passed.extend(["no_console_logs", "no_dom_queries_in_loops", "passive_scroll_listeners"])

    # ── Check 4: HTML structure ──────────────────────────────────────
    # Heading hierarchy
    headings = re.findall(r'<(h[1-6])\b', html, re.I)
    heading_levels = [int(h[1]) for h in headings]
    has_h1 = 1 in heading_levels
    h1_count = heading_levels.count(1)

    if not has_h1:
        issues.append({
            "category": "structure",
            "type": "missing_h1",
            "severity": "warning",
            "message": "No <h1> tag found",
            "auto_fix": False,
        })
    elif h1_count > 1:
        issues.append({
            "category": "structure",
            "type": "multiple_h1",
            "severity": "info",
            "message": f"{h1_count} <h1> tags found (should be exactly 1)",
            "auto_fix": False,
        })
    else:
        passed.append("single_h1")

    # Check heading order (no skipping levels)
    heading_skip = False
    for i in range(1, len(heading_levels)):
        if heading_levels[i] > heading_levels[i - 1] + 1:
            heading_skip = True
            break
    if heading_skip:
        issues.append({
            "category": "structure",
            "type": "heading_skip",
            "severity": "info",
            "message": "Heading hierarchy skips levels (e.g., h1 to h3)",
            "auto_fix": False,
        })
    else:
        passed.append("heading_hierarchy")

    # Missing lang attribute
    if not re.search(r'<html[^>]+lang\s*=', html, re.I):
        issues.append({
            "category": "structure",
            "type": "missing_lang",
            "severity": "warning",
            "message": "Missing lang attribute on <html>",
            "auto_fix": True,
        })
    else:
        passed.append("html_lang_attribute")

    # Missing viewport meta
    if not re.search(r'<meta[^>]+name\s*=\s*["\']viewport["\']', html, re.I):
        issues.append({
            "category": "structure",
            "type": "missing_viewport",
            "severity": "critical",
            "message": "Missing viewport meta tag",
            "auto_fix": True,
        })
    else:
        passed.append("viewport_meta")

    # Semantic HTML usage
    semantic_tags = ['<header', '<nav', '<main', '<footer', '<section', '<article']
    semantic_count = sum(1 for tag in semantic_tags if tag in html.lower())
    if semantic_count < 3:
        issues.append({
            "category": "structure",
            "type": "low_semantic_html",
            "severity": "info",
            "message": f"Only {semantic_count} semantic HTML tags used (header, nav, main, footer, section, article)",
            "auto_fix": False,
        })
    else:
        passed.append("semantic_html")

    # ── Check 5: Accessibility ───────────────────────────────────────
    # Interactive elements without aria-labels
    buttons_no_aria = re.findall(
        r'<button\b(?![^>]*aria-label)(?![^>]*aria-labelledby)[^>]*>\s*<(?:svg|img|i)\b',
        html, re.I | re.S,
    )
    links_no_text = re.findall(
        r'<a\b(?![^>]*aria-label)[^>]*>\s*<(?:svg|img|i)\b',
        html, re.I | re.S,
    )
    icon_only_count = len(buttons_no_aria) + len(links_no_text)
    if icon_only_count > 0:
        issues.append({
            "category": "accessibility",
            "type": "missing_aria_labels",
            "severity": "warning",
            "message": f"{icon_only_count} icon-only button(s)/link(s) missing aria-label",
            "auto_fix": False,
        })
    else:
        passed.append("aria_labels_on_icons")

    # Color contrast (basic check using CSS custom properties)
    color_vars = {}
    combined = html + "\n" + css
    for m in re.finditer(r'--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})', combined):
        color_vars[m.group(1)] = m.group(2)

    text_keys = [k for k in color_vars if any(w in k for w in ('text', 'foreground', 'heading', 'body'))]
    bg_keys = [k for k in color_vars if any(w in k for w in ('bg', 'background', 'surface'))]
    contrast_ok = True
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
                contrast_ok = False
                issues.append({
                    "category": "accessibility",
                    "type": "low_contrast",
                    "severity": "warning",
                    "message": f"Low contrast: --{tk} on --{bk} (ratio {ratio:.1f}:1, need 4.5:1)",
                    "auto_fix": False,
                })
                break
        if not contrast_ok:
            break
    if contrast_ok:
        passed.append("color_contrast")

    # Skip-nav link
    if not re.search(r'skip.*(nav|content|main)', html, re.I):
        issues.append({
            "category": "accessibility",
            "type": "missing_skip_nav",
            "severity": "info",
            "message": "No skip-to-content navigation link found",
            "auto_fix": False,
        })
    else:
        passed.append("skip_nav_link")

    # Form labels
    forms = re.findall(r'<form\b.*?</form>', html, re.I | re.S)
    inputs_without_labels = 0
    for form in forms:
        inputs = re.findall(r'<input\b[^>]*>', form, re.I | re.S)
        for inp in inputs:
            if re.search(r'type\s*=\s*["\'](?:hidden|submit|button)["\']', inp, re.I):
                continue
            has_id = re.search(r'\bid\s*=\s*["\'](\w+)["\']', inp, re.I)
            if has_id:
                input_id = has_id.group(1)
                if f'for="{input_id}"' not in form and f"for='{input_id}'" not in form:
                    if not re.search(r'aria-label', inp, re.I):
                        if not re.search(r'placeholder\s*=', inp, re.I):
                            inputs_without_labels += 1
            elif not re.search(r'(aria-label|placeholder)\s*=', inp, re.I):
                inputs_without_labels += 1

    if inputs_without_labels > 0:
        issues.append({
            "category": "accessibility",
            "type": "missing_form_labels",
            "severity": "warning",
            "message": f"{inputs_without_labels} form input(s) missing associated label or aria-label",
            "auto_fix": False,
        })
    else:
        passed.append("form_labels")

    # ── Score calculation ────────────────────────────────────────────
    severity_weights = {"critical": 15, "warning": 5, "info": 2}
    deductions = sum(severity_weights.get(i["severity"], 2) for i in issues)
    # Auto-fixable issues get half deduction (they'll be fixed)
    auto_recovery = sum(
        severity_weights.get(i["severity"], 2) * 0.5
        for i in issues if i.get("auto_fix")
    )
    score = max(0, min(100, round(100 - deductions + auto_recovery)))

    auto_fixable = [i for i in issues if i.get("auto_fix")]

    return {
        "score": score,
        "issues": issues,
        "passed": passed,
        "auto_fixable": auto_fixable,
    }


# ---------------------------------------------------------------------------
# 2. auto_fix_performance
# ---------------------------------------------------------------------------

def auto_fix_performance(html: str, css: str, js: str) -> tuple[str, str, str]:
    """
    Auto-fix common performance issues.
    Returns (fixed_html, fixed_css, fixed_js).
    """
    fixed_html = html
    fixed_css = css
    fixed_js = js

    # ── Add loading="lazy" + decoding="async" to images (except first 2) ──
    img_count = 0

    def _add_lazy(m):
        nonlocal img_count
        img_count += 1
        tag = m.group(0)
        if img_count <= 2:
            # Add fetchpriority="high" to first image
            if img_count == 1 and 'fetchpriority=' not in tag.lower():
                tag = tag[:-1] + ' fetchpriority="high">'
            return tag
        additions = ''
        if 'loading=' not in tag.lower():
            additions += ' loading="lazy"'
        if 'decoding=' not in tag.lower():
            additions += ' decoding="async"'
        if additions:
            tag = tag[:-1] + additions + '>'
        return tag

    fixed_html = re.sub(r'<img\b[^>]*>', _add_lazy, fixed_html, flags=re.I | re.S)

    # ── Add alt="" to images missing alt ──────────────────────────────
    def _add_alt(m):
        tag = m.group(0)
        if not re.search(r'\balt\s*=', tag, re.I):
            return tag[:-1] + ' alt="">'
        return tag

    fixed_html = re.sub(r'<img\b[^>]*>', _add_alt, fixed_html, flags=re.I | re.S)

    # ── Remove console.log from JS ────────────────────────────────────
    if fixed_js:
        fixed_js = re.sub(
            r'^\s*console\.(log|debug|info)\s*\([^)]*\)\s*;?\s*\n?',
            '',
            fixed_js,
            flags=re.MULTILINE,
        )

    # ── Add lang="en" to <html> if missing ────────────────────────────
    if not re.search(r'<html[^>]+lang\s*=', fixed_html, re.I):
        fixed_html = re.sub(
            r'<html\b',
            '<html lang="en"',
            fixed_html,
            count=1,
            flags=re.I,
        )

    # ── Add viewport meta if missing ──────────────────────────────────
    if not re.search(r'<meta[^>]+name\s*=\s*["\']viewport["\']', fixed_html, re.I):
        viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        head_match = re.search(r'(<head[^>]*>)', fixed_html, re.I)
        if head_match:
            pos = head_match.end()
            fixed_html = fixed_html[:pos] + "\n    " + viewport + fixed_html[pos:]

    # ── Remove duplicate CSS rules ────────────────────────────────────
    # Simple dedup: if same selector appears multiple times, merge declarations
    def _dedup_css(css_text: str) -> str:
        cleaned = re.sub(r'/\*.*?\*/', '', css_text, flags=re.S)
        # Track selectors and their rule positions in original text
        seen = {}
        duplicates = []
        for m in re.finditer(r'([^{}@]+)\{([^{}]*)\}', cleaned):
            sel = re.sub(r'\s+', ' ', m.group(1)).strip()
            if sel in seen:
                duplicates.append(m.group(0))
            else:
                seen[sel] = True
        # Remove duplicate rules from original (work on original with comments)
        result = css_text
        for dup in duplicates:
            # Only remove the second occurrence (keep original)
            idx = result.find(dup)
            if idx >= 0:
                next_idx = result.find(dup, idx + len(dup))
                if next_idx >= 0:
                    result = result[:next_idx] + result[next_idx + len(dup):]
        return result

    fixed_css = _dedup_css(fixed_css)

    return fixed_html, fixed_css, fixed_js
