"""Tests for HTML, CSS, and JS validators in the generator module."""

import pytest

# Import the validators directly from the generator module
from app.routes.generator import validate_css, validate_html, validate_js

# ---------------------------------------------------------------------------
# Sample content generators
# ---------------------------------------------------------------------------


def _make_html(length: int = 500, with_section_type: bool = True) -> str:
    """Generate valid-enough HTML of a given length."""
    section_attr = ' data-section-type="hero"' if with_section_type else ""
    base = f"""<!DOCTYPE html>
<html><head><title>Test</title></head>
<body>
<section{section_attr}>
<h1>Test Page</h1>
<p>{"x" * max(0, length - 200)}</p>
</section>
</body></html>"""
    return base


def _make_css(length: int = 500) -> str:
    """Generate valid-enough CSS of a given length."""
    return f":root {{ --primary: #000; }}\n.test {{ color: red; }}\n/* {'x' * max(0, length - 60)} */"


# ---------------------------------------------------------------------------
# HTML Validator Tests
# ---------------------------------------------------------------------------


def test_validate_html_minimum_length():
    """HTML shorter than 200 chars raises ValueError."""
    with pytest.raises(ValueError, match="too short"):
        validate_html("<div>tiny</div>")


def test_validate_html_maximum_length():
    """HTML longer than 50000 chars raises ValueError."""
    huge_html = _make_html(60000)
    with pytest.raises(ValueError, match="too large"):
        validate_html(huge_html)


def test_validate_html_requires_section_type():
    """HTML without data-section-type raises ValueError."""
    html = _make_html(500, with_section_type=False)
    with pytest.raises(ValueError, match="data-section-type"):
        validate_html(html)


def test_validate_html_converts_div_to_section():
    """Divs with data-section-type are converted to <section> tags."""
    html = '<div data-section-type="hero"><h1>Hello</h1></div><!-- end section -->'
    html = html + "x" * 200  # Pad to minimum length
    # Add a real section-type so it doesn't fail the check
    result = validate_html(html)
    assert "<section" in result
    # The div with data-section-type should have been converted
    assert "<div data-section-type=" not in result


def test_validate_html_strips_fontawesome_kit():
    """Font Awesome kit script tags are stripped."""
    html = _make_html(500)
    html = html.replace("</head>", '<script src="https://kit.fontawesome.com/abc123.js"></script></head>')
    result = validate_html(html)
    assert "kit.fontawesome.com" not in result


def test_validate_html_valid_passes():
    """Valid HTML passes validation unchanged (except allowed cleanups)."""
    html = _make_html(500)
    result = validate_html(html)
    assert "Test Page" in result
    assert 'data-section-type="hero"' in result


# ---------------------------------------------------------------------------
# CSS Validator Tests
# ---------------------------------------------------------------------------


def test_validate_css_minimum_length():
    """CSS shorter than 200 chars raises ValueError."""
    with pytest.raises(ValueError, match="too short"):
        validate_css(".tiny { color: red; }")


def test_validate_css_valid_passes():
    """Valid CSS passes validation."""
    css = _make_css(500)
    result = validate_css(css)
    assert "--primary" in result


def test_validate_css_strips_aos_rules():
    """AOS-related rules are stripped from CSS."""
    css = _make_css(500) + "\n[data-aos] { opacity: 0; }\n"
    result = validate_css(css)
    assert "[data-aos]" not in result


# ---------------------------------------------------------------------------
# JS Validator Tests
# ---------------------------------------------------------------------------


def test_validate_js_valid_code():
    """Valid JS passes validation."""
    js = "document.addEventListener('DOMContentLoaded', function() { console.log('ready'); });"
    result = validate_js(js)
    assert "DOMContentLoaded" in result


def test_validate_js_empty_returns_empty():
    """Empty JS returns empty string (JS is optional)."""
    assert validate_js("") == ""
    assert validate_js(None) == ""


def test_validate_js_strips_markdown_fences():
    """Markdown code fences are stripped from JS output."""
    js = "```javascript\nconsole.log('hello');\n```"
    result = validate_js(js)
    assert "```" not in result
    assert "console.log" in result


def test_validate_js_maximum_length():
    """JS longer than 20000 chars raises ValueError."""
    huge_js = "x" * 25000
    with pytest.raises(ValueError, match="too large"):
        validate_js(huge_js)


def test_validate_js_strips_dom_manipulation():
    """JS validation strips markdown fences but keeps DOM manipulation code."""
    js = "```js\ndocument.querySelector('.btn').addEventListener('click', () => {});\n```"
    result = validate_js(js)
    assert "```" not in result
    assert "querySelector" in result
