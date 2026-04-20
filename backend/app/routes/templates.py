"""
Templates routes — serve pre-built website templates for users to preview and customize.
"""

import os

from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer

from app.utils.animations import get_animation_js
from app.utils.form_handler import inject_form_handler
from app.utils.section_parser import inject_section_ids

router = APIRouter()
security = HTTPBearer()

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates_data")

# Curated catalog of 20 premium hand-built templates.
# The HTML files live in app/templates_data/ and are produced by
# scripts/build_premium_templates.py (run that script to regenerate after edits).
TEMPLATE_CATALOG = [
    {
        "id": "restaurant",
        "name": "Lumière Fine Dining",
        "category": "Restaurant",
        "description": "A high-end fine-dining restaurant template with warm tones, dishes gallery, reservations and wine pairing notes.",
        "niche": "restaurant",
        "colors": ["#b8860b", "#8b6508", "#1a120b", "#fbf7f0"],
    },
    {
        "id": "business_consultancy",
        "name": "Veridia Strategy",
        "category": "Business Consultancy",
        "description": "A premium strategy consulting firm template — case studies, partner profiles, sector expertise, and a discovery-call CTA.",
        "niche": "consulting",
        "colors": ["#0b3b3a", "#c9a45a", "#0a1a1a", "#f7f5ef"],
    },
    {
        "id": "tech",
        "name": "Nexus Cloud Platform",
        "category": "Technology",
        "description": "A modern SaaS landing page template — dark hero, product features, integrations grid, pricing tiers and developer-first copy.",
        "niche": "tech_startup",
        "colors": ["#6366f1", "#22d3ee", "#0a0e1a", "#111827"],
    },
    {
        "id": "pet_shop",
        "name": "Pawhaus",
        "category": "Pet Care",
        "description": "A warm, friendly pet shop & grooming template — services, product gallery, adoption stories, and booking.",
        "niche": "pet_shop",
        "colors": ["#e85d2f", "#0c5e60", "#1f1611", "#fff8f1"],
    },
    {
        "id": "rental",
        "name": "Drift Premium Car Rental",
        "category": "Rental",
        "description": "A premium car rental template — fleet showcase, reservation flow, daily/weekly pricing, and chauffeur add-on.",
        "niche": "car_dealership",
        "colors": ["#ea580c", "#fbbf24", "#0a0a0a", "#161616"],
    },
    {
        "id": "law",
        "name": "Halverson & Reed",
        "category": "Law Firm",
        "description": "A boutique law firm template — practice areas, attorney profiles, case results, and a confidential consultation form.",
        "niche": "law_firm",
        "colors": ["#1e293b", "#a8743d", "#0f172a", "#f9f7f1"],
    },
    {
        "id": "real_estate",
        "name": "Atelier Estates",
        "category": "Real Estate",
        "description": "A luxury real estate template — featured listings gallery, agent profiles, market data, and viewing request form.",
        "niche": "real_estate",
        "colors": ["#0f3a2e", "#bd8b3a", "#0e1f1a", "#f4f1eb"],
    },
    {
        "id": "healthcare",
        "name": "Lumen Clinic",
        "category": "Healthcare",
        "description": "A modern medical clinic template — services, doctor profiles, insurance partners, appointment booking.",
        "niche": "dentist",
        "colors": ["#0e7490", "#5eead4", "#0f1a1d", "#f0fdfa"],
    },
    {
        "id": "creative_studio",
        "name": "Studio Mira",
        "category": "Creative Studio",
        "description": "A bold creative branding studio template — projects gallery, services, philosophy, and discovery call CTA.",
        "niche": "portfolio",
        "colors": ["#7c3aed", "#fb923c", "#1a0a2e", "#fdf6ff"],
    },
    {
        "id": "beauty_spa",
        "name": "Saskia & Co.",
        "category": "Beauty & Spa",
        "description": "A luxurious beauty salon and spa template — services menu, stylist profiles, gallery, and online booking.",
        "niche": "beauty_salon",
        "colors": ["#b8678c", "#a8743d", "#1a0f12", "#fdf6f3"],
    },
    {
        "id": "fitness_gym",
        "name": "Ironhaus Strength Club",
        "category": "Fitness & Gym",
        "description": "A high-energy strength gym template — full-bleed hero, bold black background with neon-green accents, classes and coaching focus.",
        "niche": "fitness",
        "colors": ["#a3e635", "#65a30d", "#0a0a0a", "#141414"],
    },
    {
        "id": "wedding_planner",
        "name": "Amélie & Wren Weddings",
        "category": "Wedding Planner",
        "description": "An elegant wedding planning template — asymmetric hero, blush and gold palette, planning packages and past weddings gallery.",
        "niche": "wedding_planner",
        "colors": ["#c97b84", "#a8613c", "#1f1612", "#fdf8f5"],
    },
    {
        "id": "architecture_firm",
        "name": "Meridian & Stone Architects",
        "category": "Architecture",
        "description": "A minimal editorial architecture studio template — centered hero, charcoal and warm sand palette, dense 4-column project grid.",
        "niche": "architecture",
        "colors": ["#2a2a2a", "#525252", "#b8925a", "#f2efe9"],
    },
    {
        "id": "photography_studio",
        "name": "North & Field Photography",
        "category": "Photography",
        "description": "An image-first photographer portfolio template — cinematic full-bleed hero, amber accents on black, editorial gallery grid.",
        "niche": "photography",
        "colors": ["#f59e0b", "#d97706", "#0a0a0a", "#1a1a1a"],
    },
    {
        "id": "yoga_studio",
        "name": "Still & Soft Yoga",
        "category": "Yoga Studio",
        "description": "A calming yoga studio template — split hero with nature imagery, sage green and terracotta palette, class schedule and teacher profiles.",
        "niche": "yoga_studio",
        "colors": ["#87a96b", "#5b7a48", "#c47b4d", "#f8f5ef"],
    },
    {
        "id": "coffee_shop",
        "name": "Fernside Coffee Roasters",
        "category": "Coffee Shop",
        "description": "A warm artisan coffee roaster template — asymmetric hero, cream and espresso palette, roasting story and café gallery.",
        "niche": "coffee_shop",
        "colors": ["#8b4513", "#d2691e", "#2b1d0f", "#faf6f0"],
    },
    {
        "id": "fashion_boutique",
        "name": "Maison Linde",
        "category": "Fashion Boutique",
        "description": "A modern fashion boutique template — editorial split hero, monochrome base with magenta accent, lookbook grid and collection story.",
        "niche": "ecommerce",
        "colors": ["#111111", "#262626", "#e11d74", "#fafafa"],
    },
    {
        "id": "music_studio",
        "name": "Gravel Room Recording",
        "category": "Music Studio",
        "description": "A hybrid recording studio template — full-bleed dark hero, black and crimson palette, session workflow and gear showcase.",
        "niche": "music_artist",
        "colors": ["#dc2626", "#991b1b", "#0a0a0a", "#141414"],
    },
    {
        "id": "travel_agency",
        "name": "Meridian Atlas Travel",
        "category": "Travel Agency",
        "description": "A boutique travel design agency template — asymmetric hero with destination photography, ocean blue and coral palette, bespoke trip types.",
        "niche": "travel_agency",
        "colors": ["#0e5f87", "#0a4361", "#ff6b6b", "#f5f9fc"],
    },
    {
        "id": "online_academy",
        "name": "Verdant Academy",
        "category": "Online Academy",
        "description": "An online education platform template — split hero, course grid, indigo and amber palette, stats row and hiring partner logos.",
        "niche": "coding_bootcamp",
        "colors": ["#4f46e5", "#7c3aed", "#f59e0b", "#fdfcf9"],
    },
]


def _load_template_file(template_id: str) -> tuple[str, str, str]:
    """Load a template HTML file and split into HTML body + CSS + JS.

    Injects section IDs, form handler attributes, and standard animation JS
    so templates work identically to pipeline-generated sites.
    """
    # Sanitize template_id to prevent path traversal
    safe_id = os.path.basename(template_id)
    file_path = os.path.join(TEMPLATES_DIR, f"{safe_id}.html")
    # Ensure resolved path stays within TEMPLATES_DIR
    if not os.path.realpath(file_path).startswith(os.path.realpath(TEMPLATES_DIR)):
        raise HTTPException(status_code=400, detail="Invalid template ID")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template file not found")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Split CSS from HTML — template files have <style>...</style> at the top
    css = ""
    html = content
    if "<style>" in content and "</style>" in content:
        style_start = content.index("<style>") + len("<style>")
        style_end = content.index("</style>")
        css = content[style_start:style_end].strip()
        html = content[style_end + len("</style>") :].strip()

    # Inject section IDs so section operations work
    html = inject_section_ids(html)

    # Inject form handler attributes and JS.
    #
    # IMPORTANT: start with an EMPTY js field. We used to initialise this with
    # get_animation_js() but the deploy pipeline (s3_deploy._inline_css_js)
    # ALSO injects animation_js unconditionally. Having it in both places
    # produces two nested `document.addEventListener('DOMContentLoaded', ...)`
    # wrappers on deployed sites, which breaks brace matching and throws
    # "Uncaught SyntaxError: Unexpected end of input" — wiping out every
    # inline script on the page and mangling the hero layout.
    #
    # Templates don't need their own copy of the animation library; the
    # deploy pipeline and the in-app preview both inject it at the right
    # moment.
    js = ""
    html, js = inject_form_handler(html, js)

    return html, css, js


@router.get("/")
async def list_templates():
    """List all available templates with metadata (no HTML/CSS)."""
    return {"templates": TEMPLATE_CATALOG}


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get a specific template with its full HTML, CSS, and JS."""
    # Find metadata
    meta = next((t for t in TEMPLATE_CATALOG if t["id"] == template_id), None)
    if not meta:
        raise HTTPException(status_code=404, detail="Template not found")

    html, css, js = _load_template_file(template_id)

    return {
        **meta,
        "html": html,
        "css": css,
        "js": js,
    }


@router.get("/{template_id}/preview")
async def get_template_preview(template_id: str):
    """Get template HTML+CSS+JS combined for iframe preview."""
    meta = next((t for t in TEMPLATE_CATALOG if t["id"] == template_id), None)
    if not meta:
        raise HTTPException(status_code=404, detail="Template not found")

    html, css, js = _load_template_file(template_id)

    return {
        "id": template_id,
        "name": meta["name"],
        "html": html,
        "css": css,
        "js": js,
    }
