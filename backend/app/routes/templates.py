"""
Templates routes — serve pre-built website templates for users to preview and customize.
"""

import os

from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer

router = APIRouter()
security = HTTPBearer()

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates_data")

TEMPLATE_CATALOG = [
    {
        "id": "restaurant",
        "name": "Elegant Restaurant",
        "category": "Food & Beverage",
        "description": "A sophisticated dining website with dark/gold color scheme, menu highlights, reservations, and gallery.",
        "niche": "restaurant",
        "colors": ["#1a1a2e", "#c9a96e", "#e8d5b7", "#faf8f5"],
    },
    {
        "id": "tech_startup",
        "name": "Tech Startup",
        "category": "Technology",
        "description": "Modern SaaS landing page with gradient hero, pricing tiers, features grid, and FAQ accordion.",
        "niche": "tech_startup",
        "colors": ["#0f0f23", "#4f8cff", "#ffffff", "#f8fafc"],
    },
    {
        "id": "real_estate",
        "name": "Luxury Real Estate",
        "category": "Real Estate",
        "description": "Premium property agency site with featured listings, market stats, agent profiles, and search.",
        "niche": "real_estate",
        "colors": ["#0a1628", "#c5a55a", "#ffffff", "#f5f5f0"],
    },
    {
        "id": "portfolio",
        "name": "Creative Portfolio",
        "category": "Creative",
        "description": "Bold designer portfolio with filterable project grid, skills showcase, and timeline.",
        "niche": "portfolio",
        "colors": ["#0a0a0a", "#00ff88", "#ffffff", "#1a1a1a"],
    },
    {
        "id": "consulting",
        "name": "Business Consulting",
        "category": "Professional Services",
        "description": "Corporate consulting site with case studies, service cards, team profiles, and client logos.",
        "niche": "consulting",
        "colors": ["#1B2A4A", "#0891b2", "#ffffff", "#f8fafc"],
    },
    {
        "id": "ecommerce",
        "name": "Fashion Boutique",
        "category": "E-Commerce",
        "description": "Stylish fashion store with product grid, collection showcase, newsletter, and reviews.",
        "niche": "ecommerce",
        "colors": ["#111111", "#e11d48", "#fafafa", "#ffffff"],
    },
    {
        "id": "coffee_shop",
        "name": "Artisan Coffee House",
        "category": "Food & Beverage",
        "description": "Warm, cozy cafe website with menu, brewing methods, loyalty program, and bean origins.",
        "niche": "coffee_shop",
        "colors": ["#2c1810", "#d4915e", "#f5ebe0", "#fefcf9"],
    },
    {
        "id": "fitness",
        "name": "Fitness & Gym",
        "category": "Health & Fitness",
        "description": "High-energy gym site with class schedules, trainer profiles, membership plans, and transformation gallery.",
        "niche": "fitness",
        "colors": ["#0a0a0a", "#ff4d4d", "#ffffff", "#1a1a1a"],
    },
    {
        "id": "beauty_salon",
        "name": "Beauty & Spa",
        "category": "Beauty & Wellness",
        "description": "Elegant salon website with service menu, booking CTA, stylist profiles, and before/after gallery.",
        "niche": "beauty_salon",
        "colors": ["#1a1a1a", "#c4a882", "#fdf6f0", "#ffffff"],
    },
    {
        "id": "law_firm",
        "name": "Law Firm",
        "category": "Professional Services",
        "description": "Authoritative legal practice site with practice areas, attorney profiles, case results, and consultation CTA.",
        "niche": "law_firm",
        "colors": ["#1a2332", "#8b7355", "#f8f7f4", "#ffffff"],
    },
    {
        "id": "dentist",
        "name": "Dental Clinic",
        "category": "Healthcare",
        "description": "Clean, trustworthy dental website with services, team, patient reviews, and appointment booking.",
        "niche": "dentist",
        "colors": ["#0e4a6e", "#4fc3f7", "#f0f9ff", "#ffffff"],
    },
    {
        "id": "photography",
        "name": "Photography Studio",
        "category": "Creative",
        "description": "Minimal photographer portfolio with full-width galleries, pricing packages, and booking form.",
        "niche": "photography",
        "colors": ["#111111", "#e0c097", "#ffffff", "#f5f5f5"],
    },
    {
        "id": "hotel",
        "name": "Luxury Hotel & Resort",
        "category": "Hospitality",
        "description": "Premium hotel site with room showcases, amenities, dining, virtual tour, and booking CTA.",
        "niche": "hotel",
        "colors": ["#0f1923", "#c8a45c", "#faf9f6", "#ffffff"],
    },
    {
        "id": "wedding_planner",
        "name": "Wedding Planner",
        "category": "Events",
        "description": "Romantic event planning site with packages, real wedding galleries, vendor list, and contact form.",
        "niche": "wedding_planner",
        "colors": ["#2c2c2c", "#d4a574", "#fef7f0", "#ffffff"],
    },
    {
        "id": "bakery",
        "name": "Artisan Bakery",
        "category": "Food & Beverage",
        "description": "Charming bakery site with product showcase, custom orders, daily specials, and our story.",
        "niche": "bakery",
        "colors": ["#8b5e3c", "#f2c879", "#fff8ed", "#ffffff"],
    },
    {
        "id": "travel_agency",
        "name": "Travel & Adventures",
        "category": "Travel & Tourism",
        "description": "Vibrant travel agency with destination cards, tour packages, traveler testimonials, and booking.",
        "niche": "travel_agency",
        "colors": ["#0c2340", "#00b894", "#f0faf7", "#ffffff"],
    },
    {
        "id": "interior_design",
        "name": "Interior Design Studio",
        "category": "Design & Architecture",
        "description": "Sophisticated design studio with project portfolio, process steps, before/after reveals, and consultation.",
        "niche": "interior_design",
        "colors": ["#2d2d2d", "#a68b6b", "#f7f4ef", "#ffffff"],
    },
    {
        "id": "car_dealership",
        "name": "Auto Dealership",
        "category": "Automotive",
        "description": "Bold car dealership with featured vehicles, inventory search, financing, and test drive booking.",
        "niche": "car_dealership",
        "colors": ["#0d1117", "#e63946", "#f8f9fa", "#ffffff"],
    },
    {
        "id": "flower_shop",
        "name": "Flower & Gift Shop",
        "category": "Retail",
        "description": "Colorful florist site with arrangement gallery, occasion collections, delivery info, and ordering.",
        "niche": "flower_shop",
        "colors": ["#2d4a3e", "#e8a0bf", "#fef5f8", "#ffffff"],
    },
    {
        "id": "pet_shop",
        "name": "Pet Care & Shop",
        "category": "Pets & Animals",
        "description": "Playful pet store with products, grooming services, pet adoption, and care tips blog.",
        "niche": "pet_shop",
        "colors": ["#1b3a4b", "#ff8c42", "#fff8f0", "#ffffff"],
    },
    {
        "id": "podcast",
        "name": "Podcast & Media",
        "category": "Media & Entertainment",
        "description": "Modern podcast site with episode player, show notes, guest profiles, and subscribe links.",
        "niche": "podcast",
        "colors": ["#16161a", "#7f5af0", "#f2f0ff", "#ffffff"],
    },
    {
        "id": "yoga_studio",
        "name": "Yoga & Meditation",
        "category": "Health & Fitness",
        "description": "Calm, zen yoga studio with class schedule, instructor profiles, retreats, and membership.",
        "niche": "mental_health",
        "colors": ["#2d3436", "#6c9a8b", "#f0f7f4", "#ffffff"],
    },
    {
        "id": "music_artist",
        "name": "Music Artist",
        "category": "Creative",
        "description": "Edgy artist page with music player, tour dates, merch store, and social media links.",
        "niche": "music_artist",
        "colors": ["#0a0a0a", "#ff006e", "#1a1a2e", "#ffffff"],
    },
    {
        "id": "architecture",
        "name": "Architecture Firm",
        "category": "Design & Architecture",
        "description": "Minimal architecture firm with project showcase, design philosophy, awards, and contact.",
        "niche": "architecture_firm",
        "colors": ["#1a1a1a", "#c0c0c0", "#f5f5f5", "#ffffff"],
    },
    {
        "id": "coding_bootcamp",
        "name": "Coding Bootcamp",
        "category": "Education",
        "description": "Modern tech school with course catalog, curriculum, student outcomes, and enrollment CTA.",
        "niche": "coding_bootcamp",
        "colors": ["#0d1117", "#58a6ff", "#f0f6fc", "#ffffff"],
    },
    {
        "id": "accounting",
        "name": "Accounting & Tax",
        "category": "Professional Services",
        "description": "Professional accounting firm with services, industry expertise, team, and free consultation.",
        "niche": "accounting",
        "colors": ["#1a3a5c", "#2ecc71", "#f4f9f4", "#ffffff"],
    },
    {
        "id": "cleaning_service",
        "name": "Cleaning Service",
        "category": "Home Services",
        "description": "Clean, fresh home services site with packages, booking, coverage areas, and trust badges.",
        "niche": "cleaning_service",
        "colors": ["#1e3a5f", "#00b4d8", "#f0faff", "#ffffff"],
    },
    {
        "id": "event_management",
        "name": "Event Management",
        "category": "Events",
        "description": "Dynamic event company with past events gallery, services, client logos, and inquiry form.",
        "niche": "event_management",
        "colors": ["#1a1a2e", "#f72585", "#fff0f6", "#ffffff"],
    },
    {
        "id": "charity",
        "name": "Nonprofit & Charity",
        "category": "Nonprofit",
        "description": "Heartfelt charity site with mission, impact stats, programs, donate CTA, and volunteer signup.",
        "niche": "charity",
        "colors": ["#1b4332", "#e9c46a", "#fefae0", "#ffffff"],
    },
    {
        "id": "bookstore",
        "name": "Bookstore & Library",
        "category": "Retail",
        "description": "Literary bookshop with featured reads, genre browsing, author spotlights, and events calendar.",
        "niche": "bookstore",
        "colors": ["#3d2b1f", "#c9815b", "#faf3eb", "#ffffff"],
    },
    {
        "id": "moving_company",
        "name": "Moving & Logistics",
        "category": "Home Services",
        "description": "Reliable moving company site with service areas, pricing calculator, process steps, and booking.",
        "niche": "moving_company",
        "colors": ["#1a1a2e", "#f39c12", "#fff9e6", "#ffffff"],
    },
]


def _load_template_file(template_id: str) -> tuple[str, str]:
    """Load a template HTML file and split into HTML body + CSS."""
    file_path = os.path.join(TEMPLATES_DIR, f"{template_id}.html")
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

    return html, css


@router.get("/")
async def list_templates():
    """List all available templates with metadata (no HTML/CSS)."""
    return {"templates": TEMPLATE_CATALOG}


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get a specific template with its full HTML and CSS."""
    # Find metadata
    meta = next((t for t in TEMPLATE_CATALOG if t["id"] == template_id), None)
    if not meta:
        raise HTTPException(status_code=404, detail="Template not found")

    html, css = _load_template_file(template_id)

    return {
        **meta,
        "html": html,
        "css": css,
    }


@router.get("/{template_id}/preview")
async def get_template_preview(template_id: str):
    """Get template HTML+CSS combined for iframe preview."""
    meta = next((t for t in TEMPLATE_CATALOG if t["id"] == template_id), None)
    if not meta:
        raise HTTPException(status_code=404, detail="Template not found")

    html, css = _load_template_file(template_id)

    return {
        "id": template_id,
        "name": meta["name"],
        "html": html,
        "css": css,
    }
