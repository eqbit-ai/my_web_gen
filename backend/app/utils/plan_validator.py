"""
Plan validation and auto-fix layer.

Validates the JSON plan from Stage 1 and auto-corrects common LLM mistakes:
- Wrong item counts for grid patterns
- Missing required content fields per pattern type
- Duplicate image queries
- Missing section IDs in plan
"""

import copy
import logging
import random

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# EXPECTED ITEM COUNTS PER PATTERN
# ═══════════════════════════════════════════════════════════════════════

# {pattern: (exact_count, [allowed_counts])}
# If exact_count is set, items MUST be that count.
# If allowed_counts is set, items must be one of those counts.
PATTERN_ITEM_COUNTS = {
    "card_grid": {"allowed": [6], "default": 6},
    "icon_grid": {"allowed": [6], "default": 6},
    "feature_cards": {"allowed": [6], "default": 6},
    "feature_split": {"allowed": [2, 3], "default": 3},
    "feature_stacked": {"allowed": [4, 5], "default": 4},
    "feature_steps": {"allowed": [3, 4], "default": 3},
    "team_grid": {"allowed": [3, 6], "default": 3},
    "team_cards": {"allowed": [3, 6], "default": 3},
    "team_masonry": {"allowed": [6], "default": 6},
    "gallery_grid": {"allowed": [6, 9], "default": 6},
    "image_carousel": {"allowed": [3, 4, 5], "default": 4},
    "service_modal": {"allowed": [3, 6], "default": 6},
    "timeline": {"allowed": [4, 5, 6], "default": 4},
    "comparison_table": {"allowed": [2], "default": 2},  # columns
    "logo_carousel": {"allowed": [6, 7, 8, 9, 10], "default": 8},
    "testimonial_cards": {"allowed": [3], "default": 3},
    "pricing_table": {"allowed": [3], "default": 3},
    "stats_row": {"allowed": [4], "default": 4},
}


# ═══════════════════════════════════════════════════════════════════════
# REQUIRED CONTENT FIELDS PER SECTION TYPE
# ═══════════════════════════════════════════════════════════════════════

REQUIRED_FIELDS = {
    "navbar": ["logo_text", "links"],
    "hero": ["headline", "subheadline", "cta_primary"],
    "features": ["headline", "items"],
    "services": ["headline", "items"],
    "stats": ["items"],
    "testimonials": ["items"],
    "pricing": ["items"],
    "faq": ["items"],
    "cta": ["headline", "cta_primary"],
    "team": ["headline", "items"],
    "gallery": ["items"],
    "about": ["headline", "subheadline"],
    "contact": ["headline"],
    "footer": ["links"],
}

# Fields that items should have per section type
REQUIRED_ITEM_FIELDS = {
    "features": ["title", "description"],
    "services": ["title", "description"],
    "stats": ["title"],  # title = number, description = label
    "testimonials": ["title", "description"],  # title = name, description = quote
    "pricing": ["title"],  # title = plan name
    "faq": ["title", "description"],  # title = question, description = answer
    "team": ["title"],  # title = name
    "gallery": ["image_query"],
    "about": ["title", "description"],
}


# ═══════════════════════════════════════════════════════════════════════
# VALIDATION + AUTO-FIX
# ═══════════════════════════════════════════════════════════════════════


def validate_and_fix_plan(plan: dict) -> tuple[dict, list[str]]:
    """
    Validate plan and auto-fix issues. Returns (fixed_plan, list_of_fixes).
    Non-destructive: only adds missing data, never removes valid data.
    """
    fixes = []
    plan = copy.deepcopy(plan)

    # Collect all section lists to validate (single-page + multipage pages + shared_sections)
    all_section_lists = []
    if plan.get("sections"):
        all_section_lists.append(("main", plan["sections"]))
    for page in plan.get("pages", []):
        page_slug = page.get("slug", "unknown")
        all_section_lists.append((page_slug, page.get("sections", [])))
    for label, shared in [("shared", plan.get("shared_sections", []))]:
        if shared:
            all_section_lists.append((label, shared))

    for _source_label, sections in all_section_lists:
        for section in sections:
            stype = section.get("type", "")
            pattern = section.get("pattern", "")
            content = section.get("content", {})

            # 1. Validate required content fields
            field_fixes = _fix_missing_fields(section, stype, content)
            fixes.extend(field_fixes)

            # 2. Validate and fix item counts
            count_fixes = _fix_item_counts(section, stype, pattern, content)
            fixes.extend(count_fixes)

            # 3. Validate item sub-fields
            item_fixes = _fix_item_fields(section, stype, content)
            fixes.extend(item_fixes)

            # 4. Deduplicate image queries within a section
            dedup_fixes = _dedup_image_queries(section, content)
            fixes.extend(dedup_fixes)

    # 5. Cap navbar links at 5 (prevents overflow on desktop)
    nav_fixes = _cap_navbar_links(plan)
    fixes.extend(nav_fixes)

    # 6. Ensure hero section always has image_query + correct pattern
    _MOCKUP_HEROES = {"hero_product_mockup", "hero_mockup_center"}
    _TECH_INDUSTRIES = {"saas", "software", "tech", "technology", "app", "startup", "platform", "ai", "devtools"}
    industry = (plan.get("brand", {}).get("industry", "") or "").lower()

    for source_label, sections in all_section_lists:
        for section in sections:
            if section.get("type") == "hero":
                content = section.get("content", {})
                pattern = section.get("pattern", "")

                # Force non-tech businesses away from mockup heroes
                if pattern in _MOCKUP_HEROES and not any(kw in industry for kw in _TECH_INDUSTRIES):
                    section["pattern"] = "hero_split"
                    fixes.append(
                        f"[PLAN FIX] {source_label}/hero: changed {pattern} → hero_split (not a tech/SaaS business)"
                    )
                    logger.info(f"🖼️ Plan Fix → {source_label} hero: {pattern} → hero_split (industry: {industry})")

                # Force no-image heroes to hero_split
                if pattern in {"hero_minimal", "hero_video_bg"}:
                    section["pattern"] = "hero_split"
                    fixes.append(f"[PLAN FIX] {source_label}/hero: changed {pattern} → hero_split (must have image)")
                    logger.info(f"🖼️ Plan Fix → {source_label} hero: {pattern} → hero_split (needs image)")

                if not content.get("image_query"):
                    industry_word = industry if industry else "business"
                    page_context = source_label.replace("-", " ") if source_label != "main" else ""
                    content["image_query"] = f"{industry_word} {page_context} professional photography".strip()
                    fixes.append(
                        f"[PLAN FIX] {source_label}/hero: added missing image_query '{content['image_query']}'"
                    )
                    logger.info(
                        f"🖼️ Plan Fix → {source_label} hero missing image_query, added: '{content['image_query']}'"
                    )

    # 7. Assign section IDs in the plan itself
    _assign_plan_ids(plan)

    return plan, fixes


def _fix_missing_fields(section: dict, stype: str, content: dict) -> list[str]:
    """Ensure required content fields exist."""
    fixes = []
    required = REQUIRED_FIELDS.get(stype, [])

    for field in required:
        if field not in content or not content[field]:
            if field == "headline":
                content["headline"] = f"{stype.replace('_', ' ').title()} Section"
                fixes.append(f"[PLAN FIX] {stype}: added missing headline")
            elif field == "subheadline":
                content["subheadline"] = ""
            elif field == "cta_primary":
                content["cta_primary"] = "Get Started"
                fixes.append(f"[PLAN FIX] {stype}: added missing CTA")
            elif field == "items":
                content["items"] = []
                fixes.append(f"[PLAN FIX] {stype}: items field was missing")
            elif field == "links":
                if stype == "navbar":
                    content["links"] = ["Services", "About", "Contact"]
                else:
                    content["links"] = []
                fixes.append(f"[PLAN FIX] {stype}: added default links")
            elif field == "logo_text":
                content["logo_text"] = "Brand"
                fixes.append("[PLAN FIX] navbar: added missing logo_text")

    section["content"] = content
    return fixes


def _fix_item_counts(section: dict, stype: str, pattern: str, content: dict) -> list[str]:
    """Fix item counts to match pattern requirements."""
    fixes = []

    if pattern not in PATTERN_ITEM_COUNTS:
        return fixes

    items = content.get("items", [])
    if not items:
        return fixes  # No items to fix — _fix_missing_fields handles empty items

    rules = PATTERN_ITEM_COUNTS[pattern]
    allowed = rules["allowed"]
    default = rules["default"]
    current_count = len(items)

    if current_count in allowed:
        return fixes  # Count is valid

    # Find the closest allowed count
    target = _closest_allowed(current_count, allowed, default)

    if current_count < target:
        # Too few items — duplicate existing items to fill
        while len(items) < target:
            # Clone a random existing item with slight variation
            source = random.choice(items[:current_count])
            clone = copy.deepcopy(source)
            # Add a suffix to avoid exact duplicates
            if "title" in clone:
                clone["title"] = clone["title"] + " "  # slight variation to avoid exact duplicate
            items.append(clone)

        fixes.append(f"[PLAN FIX] {stype}/{pattern}: padded {current_count} → {target} items")

    elif current_count > target:
        # Too many items — trim to target
        content["items"] = items[:target]
        fixes.append(f"[PLAN FIX] {stype}/{pattern}: trimmed {current_count} → {target} items")

    return fixes


def _closest_allowed(current: int, allowed: list[int], default: int) -> int:
    """Find the closest allowed count to the current count."""
    if not allowed:
        return default

    # Find the nearest allowed count >= current, or the max allowed
    above = [a for a in allowed if a >= current]

    if above:
        return min(above)
    return max(allowed)


def _fix_item_fields(section: dict, stype: str, content: dict) -> list[str]:
    """Ensure items have required sub-fields."""
    fixes = []
    required_item = REQUIRED_ITEM_FIELDS.get(stype, [])

    if not required_item:
        return fixes

    items = content.get("items", [])
    for i, item in enumerate(items):
        for field in required_item:
            if field not in item or not item[field]:
                if field == "title":
                    item["title"] = f"Item {i + 1}"
                    fixes.append(f"[PLAN FIX] {stype} item {i}: added missing title")
                elif field == "description":
                    item["description"] = ""
                elif field == "image_query":
                    item["image_query"] = f"{stype} image"
                    fixes.append(f"[PLAN FIX] {stype} item {i}: added missing image_query")

    return fixes


def _dedup_image_queries(section: dict, content: dict) -> list[str]:
    """Ensure image queries within a section aren't duplicated."""
    fixes = []
    items = content.get("items", [])

    seen_queries = set()
    for i, item in enumerate(items):
        query = item.get("image_query", "")
        if query and query in seen_queries:
            # Add index variation
            item["image_query"] = f"{query} {i + 1}"
            fixes.append(f"[PLAN FIX] dedup image_query for item {i}: '{query}' → '{item['image_query']}'")
        if query:
            seen_queries.add(query)

    return fixes


def _cap_navbar_links(plan: dict) -> list[str]:
    """Cap navbar links at 5 to prevent desktop overflow."""
    MAX_NAV_LINKS = 5
    fixes = []

    for section in plan.get("sections", []):
        if section.get("type") != "navbar":
            continue
        links = section.get("content", {}).get("links", [])
        if len(links) > MAX_NAV_LINKS:
            old_count = len(links)
            section["content"]["links"] = links[:MAX_NAV_LINKS]
            fixes.append(f"[PLAN FIX] navbar: trimmed {old_count} → {MAX_NAV_LINKS} links (prevents overflow)")

    return fixes


def _assign_plan_ids(plan: dict):
    """Assign unique IDs to each section in the plan (single-page + multipage)."""
    # Single-page sections
    type_counts = {}
    for section in plan.get("sections", []):
        stype = section.get("type", "section")
        count = type_counts.get(stype, 0)
        type_counts[stype] = count + 1
        section["id"] = f"{stype}_{count + 1}" if count > 0 else stype

    # Multipage: assign IDs per page (each page has its own namespace)
    for page in plan.get("pages", []):
        page_counts = {}
        for section in page.get("sections", []):
            stype = section.get("type", "section")
            count = page_counts.get(stype, 0)
            page_counts[stype] = count + 1
            section["id"] = f"{stype}_{count + 1}" if count > 0 else stype

    # Shared sections
    for section in plan.get("shared_sections", []):
        stype = section.get("type", "section")
        section["id"] = f"shared_{stype}"
