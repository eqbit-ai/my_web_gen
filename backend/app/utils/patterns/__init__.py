"""
Modular pattern library for the HTML generation pipeline.

Instead of injecting ALL 38 patterns into every prompt, this module
dynamically loads only the patterns needed for a specific generation
based on the planner's output.
"""

import json
import os
import random

from . import about, cta, features, hero, navigation, other, portfolio, team, testimonials

# ─── Pattern Registry ───────────────────────────────────────────────
# Maps pattern_name -> (module, template_string)

_PATTERN_MODULES = {
    # Hero
    "hero_split": hero,
    "hero_center": hero,
    "hero_full_image": hero,
    "hero_minimal": hero,
    "hero_video_bg": hero,
    "hero_product_mockup": hero,
    "hero_mockup_center": hero,
    "hero_asymmetric": hero,
    "hero_parallax_layers": hero,
    "hero_text_reveal": hero,
    "hero_scroll_morph": hero,
    # Features
    "card_grid": features,
    "icon_grid": features,
    "feature_split": features,
    "feature_cards": features,
    "feature_stacked": features,
    "feature_steps": features,
    "feature_bento_grid": features,
    "feature_hover_cards": features,
    "feature_accordion_visual": features,
    # Testimonials
    "testimonial_cards": testimonials,
    "testimonial_slider": testimonials,
    "testimonial_split": testimonials,
    "testimonial_video": testimonials,
    "testimonial_marquee": testimonials,
    # Team
    "team_grid": team,
    "team_cards": team,
    "team_masonry": team,
    # CTA
    "cta_banner": cta,
    "cta_split": cta,
    "cta_gradient": cta,
    "cta_centered": cta,
    "cta_sticky_reveal": cta,
    "cta_parallax": cta,
    # Navigation
    "navbar": navigation,
    "footer_columns": navigation,
    # Other
    "pricing_table": other,
    "faq_accordion": other,
    "stats_row": other,
    "gallery_grid": other,
    "image_carousel": other,
    "service_modal": other,
    "timeline": other,
    "newsletter_cta": other,
    "comparison_table": other,
    "logo_cloud": other,
    "logo_carousel": other,
    "trust_badges": other,
    "contact_split": other,
    "pricing_toggle": other,
    "pricing_comparison": other,
    "contact_map_split": other,
    "contact_minimal": other,
    "marquee_text": other,
    "before_after": other,
    "vertical_tabs": other,
    # About
    "about_split_scroll": about,
    "about_timeline_visual": about,
    "about_numbers": about,
    # Portfolio
    "portfolio_case_study": portfolio,
    "portfolio_hover_reveal": portfolio,
    "portfolio_filterable": portfolio,
}

# All valid pattern names
ALL_PATTERNS = set(_PATTERN_MODULES.keys())


def get_pattern_template(pattern_name: str) -> str | None:
    """Get the HTML template string for a single pattern."""
    module = _PATTERN_MODULES.get(pattern_name)
    if module is None:
        return None
    templates = module.PATTERNS
    return templates.get(pattern_name)


def get_patterns_for_plan(plan: dict) -> str:
    """Extract pattern names from a plan and return their combined templates.

    This is the core function — it reads plan.sections[*].pattern and
    loads only those pattern definitions, dramatically reducing prompt size.
    """
    sections = plan.get("sections", [])
    needed = set()
    for section in sections:
        pattern = section.get("pattern", "")
        if pattern in ALL_PATTERNS:
            needed.add(pattern)

    # Always include navbar and footer
    needed.add("navbar")
    needed.add("footer_columns")

    # Build the combined template text
    parts = []
    for name in sorted(needed):
        template = get_pattern_template(name)
        if template:
            parts.append(template)

    return "\n\n".join(parts)


def get_style_additions_for_plan(plan: dict) -> str:
    """Return only the CSS style additions needed for the selected patterns."""
    sections = plan.get("sections", [])
    needed = {s.get("pattern", "") for s in sections}

    additions = []

    # Always include base styles
    additions.append(navigation.STYLE_ADDITIONS)

    # Conditional style additions
    if needed & {"feature_steps"}:
        additions.append(other.STEPS_STYLE)
    if needed & {"timeline"}:
        additions.append(other.TIMELINE_STYLE)
    if needed & {"testimonial_slider"}:
        additions.append(testimonials.SLIDER_STYLE)
    if needed & {"image_carousel"}:
        additions.append(other.CAROUSEL_STYLE)
    if needed & {"gallery_grid"}:
        additions.append(other.LIGHTBOX_STYLE)
    if needed & {"service_modal"}:
        additions.append(other.MODAL_STYLE)
    if needed & {"logo_carousel"}:
        additions.append(other.LOGO_CAROUSEL_STYLE)
    if needed & {"comparison_table"}:
        additions.append(other.COMPARISON_STYLE)
    if needed & {"portfolio_filterable"}:
        additions.append(portfolio.FILTERABLE_STYLE)

    return "\n".join(additions)


# ─── Pattern Rotation Memory ────────────────────────────────────────

HISTORY_FILE = os.environ.get(
    "PATTERN_HISTORY_FILE",
    os.path.join("/tmp", "meydan_pattern_history.json"),
)

CATEGORY_PATTERNS = {
    "hero": [
        "hero_split",
        "hero_center",
        "hero_full_image",
        "hero_minimal",
        "hero_video_bg",
        "hero_product_mockup",
        "hero_mockup_center",
        "hero_asymmetric",
        "hero_parallax_layers",
        "hero_text_reveal",
        "hero_scroll_morph",
    ],
    "features": [
        "card_grid",
        "icon_grid",
        "feature_split",
        "feature_cards",
        "feature_stacked",
        "feature_steps",
        "feature_bento_grid",
        "feature_hover_cards",
        "feature_accordion_visual",
    ],
    "testimonials": [
        "testimonial_cards",
        "testimonial_slider",
        "testimonial_split",
        "testimonial_video",
        "testimonial_marquee",
    ],
    "team": ["team_grid", "team_cards", "team_masonry"],
    "cta": ["cta_banner", "cta_split", "cta_gradient", "cta_centered", "cta_sticky_reveal", "cta_parallax"],
    "about": ["about_split_scroll", "about_timeline_visual", "about_numbers"],
    "portfolio": ["portfolio_case_study", "portfolio_hover_reveal", "portfolio_filterable"],
}


def _load_history() -> dict:
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_history(history: dict):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except OSError:
        pass


def record_used_patterns(plan: dict):
    """Record which patterns were used in a generation for rotation tracking."""
    history = _load_history()
    sections = list(plan.get("sections", []))

    # For multipage plans, collect sections from all pages + shared_sections
    if plan.get("multipage"):
        sections = list(plan.get("shared_sections", []))
        for page in plan.get("pages", []):
            sections.extend(page.get("sections", []))

    for section in sections:
        pattern = section.get("pattern", "")
        for category, patterns in CATEGORY_PATTERNS.items():
            if pattern in patterns:
                if category not in history:
                    history[category] = []
                history[category].append(pattern)
                # Keep only last 10
                history[category] = history[category][-10:]
                break

    _save_history(history)


def get_rotation_hints() -> str:
    """Generate hints for the planner about which patterns to avoid/prefer."""
    history = _load_history()
    if not history:
        return ""

    hints = []
    for category, candidates in CATEGORY_PATTERNS.items():
        recent = history.get(category, [])
        if len(recent) < 3:
            continue

        # Count frequencies in last 5
        last_5 = recent[-5:]
        from collections import Counter

        counts = Counter(last_5)
        overused = [p for p, c in counts.items() if c >= 2]

        if overused:
            fresh = [p for p in candidates if p not in overused]
            if fresh:
                hints.append(
                    f"AVOID {category} patterns: {', '.join(overused)} (recently overused). PREFER: {', '.join(fresh)}"
                )

    if hints:
        return (
            "\nPATTERN ROTATION (for variety — these were used recently):\n" + "\n".join(f"- {h}" for h in hints) + "\n"
        )
    return ""


# ─── Style Presets ──────────────────────────────────────────────────

STYLE_PRESETS = {
    "apple": {
        "description": "Ultra-clean minimalism inspired by Apple. Massive whitespace, SF Pro/Inter typography, "
        "subtle shadows, rounded corners, mono-color palette with one accent. Content-first layout.",
        "preferred_patterns": ["hero_minimal", "hero_text_reveal", "icon_grid", "feature_bento_grid", "feature_split", "cta_centered", "stats_row", "about_numbers", "contact_minimal"],
        "avoid_patterns": ["hero_full_image", "hero_video_bg", "cta_gradient"],
        "design_hints": {
            "spacing": "spacious",
            "card_radius": "16px",
            "button_radius": "12px",
            "shadow_style": "soft",
            "style": "minimal",
        },
    },
    "stripe": {
        "description": "Stripe-style design. Clean gradients, vibrant blues/purples, code-friendly typography, "
        "diagonal gradient backgrounds, frosted glass cards, technical yet approachable.",
        "preferred_patterns": ["hero_split", "card_grid", "feature_bento_grid", "feature_split", "pricing_toggle", "cta_gradient"],
        "avoid_patterns": ["hero_full_image", "team_masonry"],
        "design_hints": {
            "spacing": "normal",
            "card_radius": "12px",
            "button_radius": "8px",
            "shadow_style": "soft",
            "style": "bold",
        },
    },
    "linear": {
        "description": "Linear.app style. Dark theme, purple/violet accents, clean geometric UI, monospace touches, "
        "subtle glow effects, card-based layout with sharp edges.",
        "preferred_patterns": [
            "hero_mockup_center",
            "hero_text_reveal",
            "icon_grid",
            "feature_bento_grid",
            "feature_stacked",
            "pricing_comparison",
            "cta_centered",
        ],
        "avoid_patterns": ["hero_full_image", "team_masonry", "gallery_grid"],
        "design_hints": {
            "theme": "dark",
            "spacing": "normal",
            "card_radius": "8px",
            "button_radius": "8px",
            "shadow_style": "none",
            "style": "minimal",
        },
    },
    "framer": {
        "description": "Framer-style design. Bold typography, playful animations, asymmetric layouts, "
        "black + bright accent color, oversized headings, creative grid breaking.",
        "preferred_patterns": ["hero_asymmetric", "hero_parallax_layers", "feature_hover_cards", "testimonial_marquee", "cta_split", "marquee_text"],
        "avoid_patterns": ["hero_minimal", "icon_grid", "cta_centered"],
        "design_hints": {
            "spacing": "spacious",
            "card_radius": "16px",
            "button_radius": "50px",
            "shadow_style": "sharp",
            "style": "playful",
        },
    },
    "luxury": {
        "description": "High-end luxury aesthetic. Dark backgrounds (#1a1a2e), gold/champagne accents, "
        "serif headings (Playfair Display), dramatic imagery, generous negative space.",
        "preferred_patterns": ["hero_full_image", "hero_scroll_morph", "feature_accordion_visual", "testimonial_video", "gallery_grid", "cta_parallax", "about_split_scroll", "portfolio_case_study"],
        "avoid_patterns": ["icon_grid", "comparison_table", "pricing_table"],
        "design_hints": {
            "theme": "dark",
            "spacing": "spacious",
            "card_radius": "4px",
            "button_radius": "4px",
            "shadow_style": "none",
            "style": "elegant",
        },
    },
    "corporate": {
        "description": "Professional corporate style. Navy/slate blues, clean grid layout, Inter/system font, "
        "trust signals prominent, data-driven, enterprise-grade feel.",
        "preferred_patterns": [
            "hero_split",
            "card_grid",
            "stats_row",
            "testimonial_cards",
            "pricing_comparison",
            "cta_banner",
            "about_numbers",
            "vertical_tabs",
        ],
        "avoid_patterns": ["hero_asymmetric", "team_masonry", "gallery_grid"],
        "design_hints": {
            "spacing": "compact",
            "card_radius": "8px",
            "button_radius": "8px",
            "shadow_style": "soft",
            "style": "corporate",
        },
    },
}


def enforce_pattern_rotation(plan: dict) -> dict:
    """Post-plan enforcement: swap overused patterns with fresh alternatives.

    The planner often ignores rotation hints, so we enforce variety here
    by replacing patterns that were used 3+ times in the last 5 generations.
    Only swaps within the same category (hero→hero, cta→cta, etc.).
    The plan is modified in-place and returned.
    """
    history = _load_history()
    if not history:
        return plan

    sections = plan.get("sections", [])
    # For multipage, also process page sections
    if plan.get("multipage"):
        for page in plan.get("pages", []):
            sections = sections + page.get("sections", [])
        sections = sections + plan.get("shared_sections", [])

    for section in sections:
        pattern = section.get("pattern", "")
        if not pattern:
            continue

        for category, candidates in CATEGORY_PATTERNS.items():
            if pattern not in candidates:
                continue

            recent = history.get(category, [])
            if len(recent) < 3:
                break

            # Count usage in last 5
            last_5 = recent[-5:]
            count = last_5.count(pattern)

            if count >= 3:
                # This pattern was used 3+ times in last 5 — force a swap
                fresh = [p for p in candidates if last_5.count(p) < 2]
                if fresh:
                    new_pattern = random.choice(fresh)
                    section["pattern"] = new_pattern
            break

    return plan


def get_random_style_preset() -> tuple[str, dict]:
    """Pick a random style preset. Returns (name, preset_dict)."""
    name = random.choice(list(STYLE_PRESETS.keys()))
    return name, STYLE_PRESETS[name]


def format_style_hint(preset_name: str, preset: dict) -> str:
    """Format a style preset as a prompt injection for the planner."""
    hints = preset["design_hints"]
    preferred = ", ".join(preset["preferred_patterns"])
    avoid = ", ".join(preset.get("avoid_patterns", []))

    parts = [
        f"\nDESIGN STYLE: {preset_name.upper()}",
        f"Visual direction: {preset['description']}",
        f"Preferred patterns: {preferred}",
    ]
    if avoid:
        parts.append(f"Avoid patterns: {avoid}")
    for key, val in hints.items():
        parts.append(f"  {key}: {val}")

    return "\n".join(parts) + "\n"
