"""Tests for the HTML section parser module."""

from app.utils.section_parser import (
    _detect_section_type,
    inject_section_ids,
    parse_sections,
    replace_section_html,
)

# ---------------------------------------------------------------------------
# Fixtures: sample HTML documents
# ---------------------------------------------------------------------------

SIMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<nav id="navbar" class="navbar">
    <a href="#">Logo</a>
</nav>
<section id="hero" data-section-type="hero">
    <h1>Welcome to Our Site</h1>
</section>
<section id="features" data-section-type="features">
    <h2>Our Features</h2>
    <p>Feature list here</p>
</section>
<footer id="footer">
    <p>Copyright 2025</p>
</footer>
</body>
</html>"""


MAIN_WRAPPER_HTML = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<main>
<nav id="navbar">
    <a href="#">Logo</a>
</nav>
<section id="hero" data-section-type="hero">
    <h1>Welcome</h1>
</section>
<footer id="footer">
    <p>Footer</p>
</footer>
</main>
</body>
</html>"""


NO_IDS_HTML = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<nav class="navbar">
    <a href="#">Logo</a>
</nav>
<section data-section-type="hero">
    <h1>Welcome</h1>
</section>
<footer>
    <p>Footer</p>
</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_parse_sections_from_html():
    """parse_sections returns correct section list with id, type, tag."""
    sections = parse_sections(SIMPLE_HTML)
    assert len(sections) >= 3  # nav, hero section, features section, footer

    # Check the nav section
    nav = next((s for s in sections if s["tag"] == "nav"), None)
    assert nav is not None
    assert nav["type"] == "navbar"

    # Check the hero section
    hero = next((s for s in sections if s["id"] == "hero"), None)
    assert hero is not None
    assert hero["type"] == "hero"

    # Check that each section has required keys
    for section in sections:
        assert "id" in section
        assert "type" in section
        assert "tag" in section
        assert "start" in section
        assert "end" in section


def test_inject_section_ids():
    """inject_section_ids adds data-section-id to sections that lack them."""
    result = inject_section_ids(NO_IDS_HTML)

    assert "data-section-id=" in result

    # Parse the result to verify all sections have IDs
    sections = parse_sections(result)
    for section in sections:
        section_html = result[section["start"] : section["end"]]
        assert "data-section-id=" in section_html


def test_replace_section_html():
    """replace_section_html swaps out a section by ID."""
    new_hero = '<section id="hero" data-section-type="hero"><h1>New Hero</h1></section>'
    result = replace_section_html(SIMPLE_HTML, "hero", new_hero)

    assert "New Hero" in result
    assert "Welcome to Our Site" not in result

    # Other sections should remain unchanged
    assert "Our Features" in result
    assert "Copyright 2025" in result


def test_sections_inside_main_wrapper():
    """Sections inside <main> wrapper are parsed as top-level sections."""
    sections = parse_sections(MAIN_WRAPPER_HTML)

    # <main> is transparent — its children should be parsed
    assert len(sections) >= 2

    tags = [s["tag"] for s in sections]
    assert "nav" in tags
    assert "footer" in tags


def test_section_type_detection():
    """_detect_section_type correctly identifies section types."""
    # data-section-type attribute takes precedence
    assert _detect_section_type("section", '<section data-section-type="hero">', "") == "hero"
    assert _detect_section_type("section", '<section data-section-type="features">', "") == "features"

    # Tag-based detection
    assert _detect_section_type("nav", "<nav>", "") == "navbar"
    assert _detect_section_type("footer", "<footer>", "") == "footer"

    # Class-based heuristic
    assert _detect_section_type("section", '<section class="hero-section">', "") == "hero"
    assert _detect_section_type("section", '<section class="testimonial-area">', "") == "testimonials"

    # ID-based heuristic
    assert _detect_section_type("section", '<section id="pricing">', "") == "pricing"

    # Fallback
    assert _detect_section_type("section", "<section>", "") == "section"


def test_parse_sections_preserves_order():
    """Sections are returned in document order with correct indices."""
    sections = parse_sections(SIMPLE_HTML)
    for i, section in enumerate(sections):
        assert section["index"] == i

    # Verify ordering: nav comes before hero, hero before features
    ids = [s["id"] for s in sections]
    if "navbar" in ids and "hero" in ids:
        assert ids.index("navbar") < ids.index("hero")


def test_parse_sections_extracts_labels():
    """Sections with headings have their text extracted as labels."""
    sections = parse_sections(SIMPLE_HTML)
    hero = next((s for s in sections if s["id"] == "hero"), None)
    assert hero is not None
    assert "Welcome" in hero["label"]
