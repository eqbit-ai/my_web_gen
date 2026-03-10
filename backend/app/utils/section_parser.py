"""
HTML section parser for the layout composer.
Parses generated HTML into discrete sections, injects IDs,
and provides manipulation utilities (reorder, replace, delete, duplicate).
"""

import re
from html.parser import HTMLParser

# Tags that represent top-level sections
SECTION_TAGS = {"nav", "header", "section", "main", "article", "aside", "footer"}


class SectionExtractor(HTMLParser):
    """Extracts top-level section boundaries from HTML."""

    def __init__(self):
        super().__init__()
        self.sections = []
        self.depth = 0
        self.current_section = None
        self.current_tag = None
        self.body_depth = None
        self.in_body = False
        self._raw = ""
        self._pos = 0

    def feed(self, data):
        self._raw = data
        super().feed(data)

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
            self.body_depth = self.depth
            self.depth += 1
            return

        self.depth += 1

        if not self.in_body:
            return

        # Top-level children of body
        if self.depth == (self.body_depth or 0) + 2:
            if tag in SECTION_TAGS or self.current_section is None:
                # Start a new section
                pos = self.getpos()
                line, col = pos
                self.current_section = {
                    "tag": tag,
                    "attrs": dict(attrs),
                    "start_line": line,
                }
                self.current_tag = tag

    def handle_endtag(self, tag):
        if tag == "body":
            # Flush last section
            if self.current_section:
                self.current_section["end_line"] = self.getpos()[0]
                self.sections.append(self.current_section)
                self.current_section = None
            self.in_body = False

        self.depth -= 1

        if not self.in_body:
            return

        if self.depth == (self.body_depth or 0) + 1 and tag == self.current_tag:
            if self.current_section:
                self.current_section["end_line"] = self.getpos()[0]
                self.sections.append(self.current_section)
                self.current_section = None
                self.current_tag = None


def parse_sections(html: str) -> list[dict]:
    """
    Parse HTML into a list of section metadata.
    Returns list of dicts with: id, type, tag, label, html_snippet (first 200 chars).
    Uses a stack-based approach to correctly handle nested section-type tags.
    Treats <main> as a transparent wrapper — its children are parsed as top-level sections.
    """
    sections = []
    tag_names = "nav|header|section|footer|main|article|aside"

    # Tags that are transparent wrappers — their children are treated as top-level
    TRANSPARENT_TAGS = {"main"}

    # Find all opening and closing tags of section types
    tag_pattern = re.compile(
        r"<(/?)(" + tag_names + r")\b([^>]*)>",
        re.IGNORECASE,
    )

    # Track nesting: find top-level section-type elements only
    # depth 0 = top-level (direct child of body or <main>)
    depth = 0
    current_start = None
    current_tag = None
    current_attrs = None
    section_index = 0

    for m in tag_pattern.finditer(html):
        is_closing = m.group(1) == "/"
        tag = m.group(2).lower()
        attrs_str = m.group(3)

        # Skip self-closing tags
        if attrs_str.rstrip().endswith("/"):
            continue

        # Transparent wrappers: don't affect depth tracking
        if tag in TRANSPARENT_TAGS:
            continue

        if not is_closing:
            if depth == 0:
                # Start of a new top-level section
                current_start = m.start()
                current_tag = tag
                current_attrs = attrs_str
            depth += 1
        else:
            depth -= 1
            if depth < 0:
                depth = 0  # Malformed HTML recovery
            if depth == 0 and current_start is not None:
                # End of a top-level section
                end = m.end()
                open_tag = f"<{current_tag}{current_attrs}>"
                full = html[current_start:end]
                inner = full[len(open_tag) :]

                # Extract id if present
                id_match = re.search(r'id="([^"]*)"', current_attrs)
                existing_id = id_match.group(1) if id_match else None

                # Detect section type from content/classes
                section_type = _detect_section_type(current_tag, open_tag, inner)

                # Extract label from first heading
                heading_match = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", inner, re.DOTALL)
                label = heading_match.group(1).strip()[:60] if heading_match else section_type.title()
                label = re.sub(r"<[^>]+>", "", label).strip()

                section_id = existing_id or f"section-{section_index}"

                sections.append(
                    {
                        "id": section_id,
                        "index": section_index,
                        "type": section_type,
                        "tag": current_tag,
                        "label": label or section_type.replace("_", " ").title(),
                        "html_preview": full[:200],
                        "start": current_start,
                        "end": end,
                    }
                )
                section_index += 1
                current_start = None
                current_tag = None
                current_attrs = None

    return sections


def _detect_section_type(tag: str, open_tag: str, inner: str) -> str:
    """Detect section type. Prefers data-section-type attr, then tag, then heuristics."""
    # 1. Best source: data-section-type attribute (set by the generation pipeline)
    dst_match = re.search(r'data-section-type="([^"]*)"', open_tag)
    if dst_match:
        return dst_match.group(1).lower()

    # 2. Unambiguous tags
    if tag == "nav":
        return "navbar"
    if tag == "footer":
        return "footer"

    # 3. Heuristic fallback: check classes, id, and content keywords
    classes = ""
    class_match = re.search(r'class="([^"]*)"', open_tag)
    if class_match:
        classes = class_match.group(1).lower()
    id_attr = ""
    id_match = re.search(r'id="([^"]*)"', open_tag)
    if id_match:
        id_attr = id_match.group(1).lower()

    # Use opening tag attrs + id for keyword matching (NOT inner content — too noisy)
    tag_context = f"{tag} {classes} {id_attr}"

    type_keywords = {
        "hero": ["hero", "banner", "jumbotron", "landing"],
        "features": ["feature", "capability", "what-we-do"],
        "services": ["service", "our-service"],
        "about": ["about", "who-we-are", "our-story", "company"],
        "testimonials": ["testimonial", "review", "feedback", "client-say"],
        "pricing": ["pricing", "plan", "subscription", "tier"],
        "contact": ["contact", "get-in-touch", "reach-us"],
        "cta": ["cta", "call-to-action", "sign-up", "get-started", "book", "booking"],
        "faq": ["faq", "question", "accordion"],
        "gallery": ["gallery", "portfolio", "showcase"],
        "team": ["team", "staff", "people", "member"],
        "stats": ["stat", "number", "metric", "counter"],
        "navbar": ["nav", "navbar", "navigation"],
        "footer": ["footer", "site-footer"],
        "header": ["header", "top-bar"],
        "case_studies": ["case-stud", "success-stor"],
    }

    # First pass: match against tag + class + id only (most reliable)
    for stype, keywords in type_keywords.items():
        for kw in keywords:
            if kw in tag_context:
                return stype

    # Second pass: check inner content (first 300 chars) as last resort
    inner_lower = inner[:300].lower()
    combined = f"{tag_context} {inner_lower}"

    for stype, keywords in type_keywords.items():
        for kw in keywords:
            if kw in combined:
                return stype

    if tag == "header":
        return "header"
    return "section"


def inject_section_ids(html: str) -> str:
    """Add data-section-id attributes to top-level sections."""
    sections = parse_sections(html)
    if not sections:
        return html

    # Process from end to start to preserve offsets
    result = html
    for section in reversed(sections):
        start = section["start"]
        end = section["end"]
        section_html = result[start:end]

        sid = section["id"]
        tag = section["tag"]

        # Check if data-section-id already exists
        if "data-section-id" in section_html[:200]:
            continue

        # Inject into the opening tag
        old_open = f"<{tag}"
        new_open = f'<{tag} data-section-id="{sid}"'
        section_html = section_html.replace(old_open, new_open, 1)
        result = result[:start] + section_html + result[end:]

    return result


def extract_section_html(html: str, section_id: str) -> str | None:
    """Extract the full HTML of a specific section by its ID."""
    sections = parse_sections(html)
    for section in sections:
        if section["id"] == section_id:
            return html[section["start"] : section["end"]]
    return None


def replace_section_html(html: str, section_id: str, new_section_html: str) -> str:
    """Replace a section's HTML with new content."""
    sections = parse_sections(html)
    for section in sections:
        if section["id"] == section_id:
            return html[: section["start"]] + new_section_html + html[section["end"] :]
    return html


def reorder_sections(html: str, new_order: list[str]) -> str:
    """Reorder sections by their IDs.

    Works by placing sections from new_order into the original section slots,
    preserving all wrapper elements (<main>, etc.) and inter-section content.
    """
    sections = parse_sections(html)
    if not sections or len(sections) < 2:
        return html

    # Build map of section ID → original HTML
    section_map = {}
    for section in sections:
        section_map[section["id"]] = html[section["start"] : section["end"]]

    # Build the ordered list of section HTML contents
    ordered = []
    for sid in new_order:
        if sid in section_map:
            ordered.append(section_map[sid])
    # Append any sections not in new_order
    for section in sections:
        if section["id"] not in new_order:
            ordered.append(section_map[section["id"]])

    # Replace each original section slot with the reordered content
    # Process from end to start to preserve offsets
    result = html
    for i in range(len(sections) - 1, -1, -1):
        if i < len(ordered):
            s = sections[i]
            result = result[: s["start"]] + ordered[i] + result[s["end"] :]

    return result


def remove_section(html: str, section_id: str) -> str:
    """Remove a section from the HTML."""
    sections = parse_sections(html)
    for section in sections:
        if section["id"] == section_id:
            return html[: section["start"]] + html[section["end"] :]
    return html


def insert_section_at(html: str, new_section_html: str, reference_section_id: str, position: str = "after") -> str:
    """Insert new section before or after a reference section."""
    sections = parse_sections(html)
    for section in sections:
        if section["id"] == reference_section_id:
            if position == "before":
                return html[: section["start"]] + new_section_html + "\n\n" + html[section["start"] :]
            else:  # after
                return html[: section["end"]] + "\n\n" + new_section_html + html[section["end"] :]
    # If reference not found, append at end of body or end of HTML
    body_end = html.rfind("</body>")
    if body_end != -1:
        return html[:body_end] + new_section_html + "\n" + html[body_end:]
    return html + "\n\n" + new_section_html


def update_section_style(html: str, section_id: str, styles_dict: dict) -> str:
    """Add/update inline styles on a section's root element."""
    sections = parse_sections(html)
    for section in sections:
        if section["id"] == section_id:
            section_html = html[section["start"] : section["end"]]

            # Build style string
            style_str = "; ".join(f"{k}: {v}" for k, v in styles_dict.items())

            # Check if style attribute already exists on the opening tag
            open_tag_end = section_html.index(">")
            open_tag = section_html[: open_tag_end + 1]

            style_match = re.search(r'style="([^"]*)"', open_tag)
            if style_match:
                # Merge: parse existing styles, update with new ones
                existing = style_match.group(1).rstrip(";")
                existing_styles = {}
                for part in existing.split(";"):
                    part = part.strip()
                    if ":" in part:
                        k, v = part.split(":", 1)
                        existing_styles[k.strip()] = v.strip()
                existing_styles.update(styles_dict)
                merged = "; ".join(f"{k}: {v}" for k, v in existing_styles.items())
                new_open_tag = open_tag[: style_match.start()] + f'style="{merged}"' + open_tag[style_match.end() :]
            else:
                # Insert style attribute before the closing >
                new_open_tag = open_tag[:-1] + f' style="{style_str}">'

            new_section = new_open_tag + section_html[open_tag_end + 1 :]
            return html[: section["start"]] + new_section + html[section["end"] :]
    return html


def toggle_section_visibility(html: str, section_id: str, visible: bool = True) -> str:
    """Add/remove display:none on a section."""
    if visible:
        # Remove display:none
        sections = parse_sections(html)
        for section in sections:
            if section["id"] == section_id:
                section_html = html[section["start"] : section["end"]]
                # Remove display:none from inline style
                section_html = re.sub(r"display\s*:\s*none\s*;?\s*", "", section_html)
                # Clean up empty style attributes
                section_html = re.sub(r'\s*style="\s*"', "", section_html)
                return html[: section["start"]] + section_html + html[section["end"] :]
        return html
    else:
        return update_section_style(html, section_id, {"display": "none"})


def duplicate_section(html: str, section_id: str) -> str:
    """Duplicate a section (insert copy immediately after)."""
    sections = parse_sections(html)
    for section in sections:
        if section["id"] == section_id:
            original = html[section["start"] : section["end"]]
            # Give the duplicate a new id
            dup_id = f"{section_id}-copy"
            duplicate = original.replace(
                f'data-section-id="{section_id}"',
                f'data-section-id="{dup_id}"',
                1,
            )
            if f'id="{section_id}"' in duplicate:
                duplicate = duplicate.replace(f'id="{section_id}"', f'id="{dup_id}"', 1)
            return html[: section["end"]] + "\n\n" + duplicate + html[section["end"] :]
    return html
