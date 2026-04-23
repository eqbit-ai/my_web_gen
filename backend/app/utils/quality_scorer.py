"""
Quality scorer — checks generated HTML/CSS for premium design indicators.

Returns a score (0-100) and a list of issues. Used to auto-fix common problems
and optionally reject/regenerate below-threshold output.
"""

import re


def score_generation(html: str, css: str, theme: str = "light") -> dict:
    """Score a generated website's visual quality.

    Returns:
        {
            "score": int (0-100),
            "issues": list of issue descriptions,
            "auto_fixes": list of auto-applied CSS fixes,
            "css": str (fixed CSS)
        }
    """
    score = 100
    issues = []
    auto_fixes = []
    combined = html + css

    # ── Hero Quality (30 points max deduction) ──

    hero_match = re.search(r'data-section-type="hero"', html)
    if not hero_match:
        score -= 15
        issues.append("Missing hero section")
    else:
        hero_html = _extract_section(html, "hero")
        if hero_html:
            # Check for any image in the hero — background-url, any <img> tag
            # (split-grid layouts put the image inside a wrapper div, not as a
            # background), or an {{IMG:...}} placeholder. Must be permissive:
            # forcing a dark-gradient auto-fix onto a light-theme hero makes the
            # hero text invisible.
            has_bg_image = bool(re.search(r'background.*url\(|background-image.*url\(|<img\s|\{\{IMG:', hero_html + css, re.IGNORECASE))
            if not has_bg_image:
                score -= 10
                issues.append("Hero has no background image — looks flat")
                # Auto-fix: add a gradient overlay to hero
                auto_fixes.append("section[data-section-type='hero'] { background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0a0a1a 100%); min-height: 70vh; }")

            # Check hero height
            has_min_height = bool(re.search(r'hero.*min-height|hero.*height:\s*[6-9]\d|hero.*height:\s*100', css, re.IGNORECASE))
            if not has_min_height:
                score -= 5
                issues.append("Hero section too short")
                auto_fixes.append("section[data-section-type='hero'] { min-height: 70vh; }")

            # Check hero has heading
            has_heading = bool(re.search(r'<h1[^>]*>(?!<)', hero_html))
            if not has_heading:
                score -= 5
                issues.append("Hero missing h1 heading")

            # Check hero has CTA button
            has_cta = bool(re.search(r'<a[^>]*class="[^"]*btn|<button[^>]*class="[^"]*btn', hero_html, re.IGNORECASE))
            if not has_cta:
                score -= 5
                issues.append("Hero missing CTA button")

    # ── Color Quality (20 points max deduction) ──

    # Check for raw Tailwind default colors (generic)
    generic_colors = ["#3b82f6", "#22c55e", "#ef4444", "#eab308", "#8b5cf6", "#ec4899"]
    for color in generic_colors:
        if color in css:
            score -= 3
            issues.append(f"Generic Tailwind color {color} used — looks template-y")
            break  # Only penalize once

    # Check for pure white/black backgrounds
    if re.search(r'background(?:-color)?:\s*#fff(?:fff)?[;\s]', css):
        score -= 3
        issues.append("Pure white (#fff) background — should use tinted neutral")

    if re.search(r'background(?:-color)?:\s*#000(?:000)?[;\s]', css):
        score -= 3
        issues.append("Pure black (#000) background — should use tinted dark")

    # Check CSS variables exist (design tokens)
    has_root_vars = ":root" in css and "--" in css
    if not has_root_vars:
        score -= 5
        issues.append("No CSS custom properties — design tokens missing")

    # ── Typography (10 points max deduction) ──

    has_font_import = "@import" in css and "fonts.googleapis" in css
    if not has_font_import:
        score -= 5
        issues.append("No Google Fonts import — using system fonts")

    # Check for Inter/Roboto as heading font (too generic)
    heading_font_match = re.search(r'h[1-3]\s*\{[^}]*font-family:\s*["\']?(Inter|Roboto|Arial)', css)
    if heading_font_match:
        score -= 3
        issues.append(f"Generic heading font ({heading_font_match.group(1)}) — should use distinctive font")

    # ── Spacing & Layout (15 points max deduction) ──

    # Check section padding
    section_count = len(re.findall(r'data-section-type=', html))
    has_section_padding = bool(re.search(r'section.*padding|py-\d{2}|padding:\s*[3-9]rem|padding:\s*[4-9]\d+px', css))
    if section_count > 3 and not has_section_padding:
        score -= 5
        issues.append("Sections lack padding — looks cramped")
        auto_fixes.append("section[data-section-type] { padding: 5rem 1.5rem; }")

    # Check for responsive breakpoints
    has_responsive = "@media" in css
    if not has_responsive:
        score -= 5
        issues.append("No responsive breakpoints — mobile will look broken")
        auto_fixes.append("""@media (max-width: 768px) {
  section[data-section-type] { padding: 3rem 1rem; }
  h1 { font-size: 2rem !important; }
  h2 { font-size: 1.5rem !important; }
}""")

    # ── Interactive Quality (10 points max deduction) ──

    # Check for hover effects
    has_hover = ":hover" in css
    if not has_hover:
        score -= 5
        issues.append("No hover effects — site feels static")

    # Check for transitions
    has_transitions = "transition" in css
    if not has_transitions:
        score -= 3
        issues.append("No CSS transitions — interactions feel abrupt")

    # ── Footer Quality (5 points max deduction) ──

    has_footer = bool(re.search(r'data-section-type="footer"', html))
    if not has_footer:
        score -= 5
        issues.append("Missing footer section")

    # ── Images (10 points max deduction) ──

    # Check for placeholder images
    if "placeholder.com" in html or "via.placeholder" in html or "placehold.it" in html:
        score -= 10
        issues.append("Placeholder images found — should use real photos")

    # Check images have alt text
    imgs_without_alt = len(re.findall(r'<img(?![^>]*alt=)[^>]*>', html))
    if imgs_without_alt > 2:
        score -= 3
        issues.append(f"{imgs_without_alt} images missing alt text")

    # ── Assemble fixed CSS ──
    fixed_css = css
    if auto_fixes:
        fixed_css = css.rstrip() + "\n\n/* === Quality auto-fixes === */\n" + "\n".join(auto_fixes) + "\n"

    return {
        "score": max(0, score),
        "issues": issues,
        "auto_fixes": auto_fixes,
        "css": fixed_css,
    }


def _extract_section(html: str, section_type: str) -> str:
    """Extract a section by data-section-type."""
    match = re.search(
        rf'<section[^>]*data-section-type="{section_type}"[^>]*>.*?</section>',
        html, re.DOTALL
    )
    return match.group(0) if match else ""
