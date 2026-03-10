"""
Design System generator and utilities.
Produces structured design tokens (colors, typography, spacing, etc.)
and converts them to CSS custom properties.
"""

import json
import re

DEFAULT_DESIGN_SYSTEM = {
    "colors": {
        "primary": "#2563eb",
        "primary_light": "#3b82f6",
        "primary_dark": "#1d4ed8",
        "secondary": "#7c3aed",
        "accent": "#f59e0b",
        "background": "#ffffff",
        "surface": "#f9fafb",
        "text": "#1f2937",
        "text_secondary": "#6b7280",
        "text_muted": "#9ca3af",
        "border": "#e5e7eb",
        "success": "#22c55e",
        "warning": "#eab308",
        "error": "#ef4444",
        "info": "#3b82f6",
    },
    "typography": {
        "heading_family": "Inter",
        "body_family": "Inter",
        "scale": {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem",
            "4xl": "2.25rem",
            "5xl": "3rem",
            "6xl": "3.75rem",
        },
        "weights": {
            "light": 300,
            "normal": 400,
            "medium": 500,
            "semibold": 600,
            "bold": 700,
            "extrabold": 800,
        },
        "line_heights": {"tight": 1.25, "normal": 1.5, "relaxed": 1.75},
    },
    "spacing": {
        "base": "4px",
        "scale": {
            "1": "4px",
            "2": "8px",
            "3": "12px",
            "4": "16px",
            "5": "20px",
            "6": "24px",
            "8": "32px",
            "10": "40px",
            "12": "48px",
            "16": "64px",
            "20": "80px",
            "24": "96px",
        },
    },
    "borders": {
        "radius": {
            "none": "0",
            "sm": "4px",
            "md": "8px",
            "lg": "12px",
            "xl": "16px",
            "2xl": "24px",
            "full": "9999px",
        },
        "width": {"thin": "1px", "medium": "2px", "thick": "4px"},
    },
    "shadows": {
        "sm": "0 1px 2px rgba(0,0,0,0.05)",
        "md": "0 4px 6px rgba(0,0,0,0.07)",
        "lg": "0 10px 15px rgba(0,0,0,0.1)",
        "xl": "0 20px 25px rgba(0,0,0,0.15)",
    },
    "layout": {
        "max_width": "1280px",
        "columns": 12,
        "gutter": "24px",
        "breakpoints": {
            "sm": "640px",
            "md": "768px",
            "lg": "1024px",
            "xl": "1280px",
        },
    },
}


DESIGN_SYSTEM_PROMPT = """You are a design system expert. Generate a complete design system as JSON for a website.

User request: {prompt}
{niche_context}

Output ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
  "colors": {{
    "primary": "#hex",
    "primary_light": "#hex",
    "primary_dark": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "surface": "#hex",
    "text": "#hex",
    "text_secondary": "#hex",
    "text_muted": "#hex",
    "border": "#hex",
    "success": "#22c55e",
    "warning": "#eab308",
    "error": "#ef4444",
    "info": "#3b82f6"
  }},
  "typography": {{
    "heading_family": "Google Font Name",
    "body_family": "Google Font Name",
    "scale": {{"xs":"0.75rem","sm":"0.875rem","base":"1rem","lg":"1.125rem","xl":"1.25rem","2xl":"1.5rem","3xl":"1.875rem","4xl":"2.25rem","5xl":"3rem","6xl":"3.75rem"}},
    "weights": {{"light":300,"normal":400,"medium":500,"semibold":600,"bold":700,"extrabold":800}},
    "line_heights": {{"tight":1.25,"normal":1.5,"relaxed":1.75}}
  }},
  "spacing": {{
    "base": "4px",
    "scale": {{"1":"4px","2":"8px","3":"12px","4":"16px","5":"20px","6":"24px","8":"32px","10":"40px","12":"48px","16":"64px","20":"80px","24":"96px"}}
  }},
  "borders": {{
    "radius": {{"none":"0","sm":"4px","md":"8px","lg":"12px","xl":"16px","2xl":"24px","full":"9999px"}},
    "width": {{"thin":"1px","medium":"2px","thick":"4px"}}
  }},
  "shadows": {{
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.07)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.15)"
  }},
  "layout": {{
    "max_width": "1280px",
    "columns": 12,
    "gutter": "24px",
    "breakpoints": {{"sm":"640px","md":"768px","lg":"1024px","xl":"1280px"}}
  }}
}}

Rules:
- Choose colors that work together with proper contrast (WCAG AA)
- Pick real Google Fonts that match the brand feel
- Adjust border radius for the style (rounded for friendly, sharp for corporate)
- Output ONLY the JSON object, nothing else"""


def generate_design_system_prompt(prompt: str, niche_context: str = "") -> str:
    return DESIGN_SYSTEM_PROMPT.format(prompt=prompt, niche_context=niche_context)


def parse_design_system(llm_response: str) -> dict:
    """Extract JSON design system from LLM response."""
    # Try to find JSON in response
    text = llm_response.strip()

    # Remove markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
        return validate_design_system(data)
    except json.JSONDecodeError:
        # Try to extract JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                data = json.loads(match.group())
                return validate_design_system(data)
            except json.JSONDecodeError:
                pass
    return DEFAULT_DESIGN_SYSTEM.copy()


def validate_design_system(data: dict) -> dict:
    """Validate and fill missing fields with defaults."""
    result = {}
    for key, default_val in DEFAULT_DESIGN_SYSTEM.items():
        if key in data and isinstance(data[key], dict):
            if isinstance(default_val, dict):
                merged = default_val.copy()
                merged.update(data[key])
                result[key] = merged
            else:
                result[key] = data[key]
        else:
            result[key] = default_val
    return result


def merge_design_systems(base: dict, override: dict) -> dict:
    """Deep merge override into base."""
    result = {}
    for key in set(list(base.keys()) + list(override.keys())):
        if key in override and key in base:
            if isinstance(base[key], dict) and isinstance(override[key], dict):
                result[key] = {**base[key], **override[key]}
            else:
                result[key] = override[key]
        elif key in override:
            result[key] = override[key]
        else:
            result[key] = base[key]
    return result


def design_system_to_css_vars(ds: dict) -> str:
    """Convert design system JSON to CSS custom properties."""
    lines = [":root {"]

    # Colors
    colors = ds.get("colors", {})
    for key, val in colors.items():
        css_key = key.replace("_", "-")
        lines.append(f"  --color-{css_key}: {val};")

    # Typography
    typo = ds.get("typography", {})
    lines.append(f"  --font-heading: '{typo.get('heading_family', 'Inter')}', sans-serif;")
    lines.append(f"  --font-body: '{typo.get('body_family', 'Inter')}', sans-serif;")
    for key, val in typo.get("scale", {}).items():
        lines.append(f"  --text-{key}: {val};")
    for key, val in typo.get("weights", {}).items():
        lines.append(f"  --font-{key}: {val};")
    for key, val in typo.get("line_heights", {}).items():
        lines.append(f"  --leading-{key}: {val};")

    # Spacing
    for key, val in ds.get("spacing", {}).get("scale", {}).items():
        lines.append(f"  --space-{key}: {val};")

    # Borders
    for key, val in ds.get("borders", {}).get("radius", {}).items():
        lines.append(f"  --radius-{key}: {val};")

    # Shadows
    for key, val in ds.get("shadows", {}).items():
        lines.append(f"  --shadow-{key}: {val};")

    # Layout
    layout = ds.get("layout", {})
    lines.append(f"  --max-width: {layout.get('max_width', '1280px')};")
    lines.append(f"  --grid-gutter: {layout.get('gutter', '24px')};")

    lines.append("}")

    # Font imports
    hf = typo.get("heading_family", "Inter").replace(" ", "+")
    bf = typo.get("body_family", "Inter").replace(" ", "+")
    font_import = f'@import url("https://fonts.googleapis.com/css2?family={hf}:wght@300;400;500;600;700;800&family={bf}:wght@300;400;500;600;700&display=swap");'

    return font_import + "\n\n" + "\n".join(lines)


def design_system_to_prompt_context(ds: dict) -> str:
    """Convert design system to a text prompt context for LLMs."""
    colors = ds.get("colors", {})
    typo = ds.get("typography", {})
    borders = ds.get("borders", {})
    layout = ds.get("layout", {})

    return f"""DESIGN SYSTEM (use CSS custom properties var(--color-primary) etc.):
- Colors: primary {colors.get("primary")}, secondary {colors.get("secondary")}, accent {colors.get("accent")}, bg {colors.get("background")}, text {colors.get("text")}
- Typography: Headings "{typo.get("heading_family", "Inter")}", Body "{typo.get("body_family", "Inter")}"
- Border radius: sm {borders.get("radius", {}).get("sm", "4px")}, md {borders.get("radius", {}).get("md", "8px")}, lg {borders.get("radius", {}).get("lg", "12px")}
- Layout: max-width {layout.get("max_width", "1280px")}, {layout.get("columns", 12)}-column grid
- IMPORTANT: Use var(--color-primary), var(--font-heading), var(--radius-md), var(--shadow-md) etc. CSS custom properties
- Include the design system CSS variables at the top of your CSS"""
