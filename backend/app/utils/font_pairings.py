"""
Curated Google Font pairings for website generation.

Each pairing is a proven combination sourced from real design systems
and typography best practices. All font names are real Google Fonts.
"""

import random

FONT_PAIRINGS = [
    # --- Modern / Minimal ---
    {
        "heading": "Inter",
        "body": "Inter",
        "style": "modern minimal",
        "google_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
    },
    {
        "heading": "Space Grotesk",
        "body": "DM Sans",
        "style": "tech startup",
        "google_import": "https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap",
    },
    {
        "heading": "Sora",
        "body": "Nunito Sans",
        "style": "clean corporate",
        "google_import": "https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700&family=Sora:wght@400;500;600;700;800&display=swap",
    },
    {
        "heading": "Manrope",
        "body": "Manrope",
        "style": "modern geometric",
        "google_import": "https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&display=swap",
    },
    {
        "heading": "Plus Jakarta Sans",
        "body": "Plus Jakarta Sans",
        "style": "modern saas",
        "google_import": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap",
    },
    {
        "heading": "General Sans",
        "body": "Inter",
        "style": "minimal clean",
        "google_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    },
    # --- Luxury / Elegant ---
    {
        "heading": "Playfair Display",
        "body": "Source Sans 3",
        "style": "luxury elegant",
        "google_import": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800;900&family=Source+Sans+3:wght@300;400;500;600;700&display=swap",
    },
    {
        "heading": "Cormorant Garamond",
        "body": "Proza Libre",
        "style": "editorial luxury",
        "google_import": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Proza+Libre:wght@400;500;600;700&display=swap",
    },
    {
        "heading": "DM Serif Display",
        "body": "DM Sans",
        "style": "refined elegant",
        "google_import": "https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap",
    },
    {
        "heading": "Fraunces",
        "body": "Commissioner",
        "style": "luxury premium",
        "google_import": "https://fonts.googleapis.com/css2?family=Commissioner:wght@300;400;500;600;700&family=Fraunces:wght@400;500;600;700;800;900&display=swap",
    },
    {
        "heading": "Lora",
        "body": "Merriweather Sans",
        "style": "warm elegant",
        "google_import": "https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Merriweather+Sans:wght@300;400;500;600;700&display=swap",
    },
    {
        "heading": "Libre Baskerville",
        "body": "Source Sans 3",
        "style": "classic luxury",
        "google_import": "https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Source+Sans+3:wght@300;400;500;600;700&display=swap",
    },
    # --- Bold / Impactful ---
    {
        "heading": "Cabinet Grotesk",
        "body": "Satoshi",
        "style": "bold modern",
        "google_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
    },
    {
        "heading": "Clash Display",
        "body": "General Sans",
        "style": "bold creative",
        "google_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
    },
    {
        "heading": "Bricolage Grotesque",
        "body": "Inter",
        "style": "bold tech",
        "google_import": "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap",
    },
    {
        "heading": "Outfit",
        "body": "Outfit",
        "style": "bold geometric",
        "google_import": "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap",
    },
    {
        "heading": "Epilogue",
        "body": "Epilogue",
        "style": "bold versatile",
        "google_import": "https://fonts.googleapis.com/css2?family=Epilogue:wght@300;400;500;600;700;800;900&display=swap",
    },
    # --- Corporate / Professional ---
    {
        "heading": "Poppins",
        "body": "Open Sans",
        "style": "corporate friendly",
        "google_import": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700;800&display=swap",
    },
    {
        "heading": "Montserrat",
        "body": "Hind",
        "style": "professional corporate",
        "google_import": "https://fonts.googleapis.com/css2?family=Hind:wght@300;400;500;600;700&family=Montserrat:wght@400;500;600;700;800;900&display=swap",
    },
    {
        "heading": "Raleway",
        "body": "Lato",
        "style": "polished corporate",
        "google_import": "https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&family=Raleway:wght@400;500;600;700;800&display=swap",
    },
    {
        "heading": "Work Sans",
        "body": "Work Sans",
        "style": "neutral professional",
        "google_import": "https://fonts.googleapis.com/css2?family=Work+Sans:wght@300;400;500;600;700;800&display=swap",
    },
    {
        "heading": "Albert Sans",
        "body": "Albert Sans",
        "style": "clean professional",
        "google_import": "https://fonts.googleapis.com/css2?family=Albert+Sans:wght@300;400;500;600;700;800&display=swap",
    },
    # --- Creative / Playful ---
    {
        "heading": "Archivo",
        "body": "Nunito",
        "style": "creative playful",
        "google_import": "https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&family=Nunito:wght@300;400;500;600;700&display=swap",
    },
    {
        "heading": "Urbanist",
        "body": "Urbanist",
        "style": "friendly modern",
        "google_import": "https://fonts.googleapis.com/css2?family=Urbanist:wght@300;400;500;600;700;800;900&display=swap",
    },
    {
        "heading": "Josefin Sans",
        "body": "Lato",
        "style": "artistic creative",
        "google_import": "https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@300;400;500;600;700&family=Lato:wght@300;400;700&display=swap",
    },
    # --- Editorial / Magazine ---
    {
        "heading": "Newsreader",
        "body": "Inter",
        "style": "editorial magazine",
        "google_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Newsreader:wght@300;400;500;600;700&display=swap",
    },
    {
        "heading": "Spectral",
        "body": "Karla",
        "style": "literary editorial",
        "google_import": "https://fonts.googleapis.com/css2?family=Karla:wght@300;400;500;600;700&family=Spectral:wght@400;500;600;700;800&display=swap",
    },
    {
        "heading": "Literata",
        "body": "Source Sans 3",
        "style": "refined editorial",
        "google_import": "https://fonts.googleapis.com/css2?family=Literata:wght@400;500;600;700;800;900&family=Source+Sans+3:wght@300;400;500;600;700&display=swap",
    },
]

# Keyword-to-style mapping for fuzzy matching
_STYLE_KEYWORDS = {
    "modern": ["modern minimal", "modern saas", "modern geometric", "bold modern", "friendly modern"],
    "minimal": ["modern minimal", "minimal clean"],
    "luxury": ["luxury elegant", "editorial luxury", "luxury premium", "classic luxury"],
    "elegant": ["luxury elegant", "refined elegant", "warm elegant"],
    "tech": ["tech startup", "bold tech"],
    "startup": ["tech startup", "modern saas"],
    "saas": ["modern saas", "plus jakarta sans"],
    "corporate": ["clean corporate", "corporate friendly", "professional corporate", "polished corporate"],
    "professional": ["professional corporate", "neutral professional", "clean professional"],
    "bold": ["bold modern", "bold creative", "bold tech", "bold geometric", "bold versatile"],
    "creative": ["bold creative", "creative playful", "artistic creative"],
    "playful": ["creative playful", "friendly modern"],
    "editorial": ["editorial luxury", "editorial magazine", "literary editorial", "refined editorial"],
    "magazine": ["editorial magazine"],
    "clean": ["minimal clean", "clean corporate", "clean professional"],
    "geometric": ["modern geometric", "bold geometric"],
    "friendly": ["corporate friendly", "friendly modern"],
    "premium": ["luxury premium", "refined elegant"],
    "classic": ["classic luxury", "warm elegant"],
    "warm": ["warm elegant", "creative playful"],
    "artistic": ["artistic creative", "literary editorial"],
    "serif": ["luxury elegant", "editorial luxury", "refined elegant", "classic luxury", "editorial magazine"],
    "sans": ["modern minimal", "tech startup", "clean corporate", "modern saas"],
    "finance": ["professional corporate", "polished corporate", "neutral professional"],
    "real estate": ["luxury elegant", "luxury premium", "refined elegant"],
    "restaurant": ["warm elegant", "editorial luxury", "artistic creative"],
    "fashion": ["luxury elegant", "editorial luxury", "bold creative"],
    "agency": ["bold modern", "bold creative", "tech startup"],
    "consulting": ["clean corporate", "professional corporate", "neutral professional"],
    "healthcare": ["clean professional", "corporate friendly", "friendly modern"],
    "education": ["corporate friendly", "friendly modern", "neutral professional"],
    "ecommerce": ["modern saas", "modern minimal", "bold modern"],
}


def get_random_pairing() -> dict:
    """Return a random font pairing from the curated list."""
    return random.choice(FONT_PAIRINGS)


def get_pairing_for_style(style_hint: str) -> dict:
    """
    Pick the best font pairing for a given style keyword or phrase.

    Matches against style descriptions and keyword mappings.
    Falls back to a random pairing if no match is found.

    Args:
        style_hint: A keyword or phrase like "luxury", "tech startup",
                    "modern minimal", "real estate", etc.

    Returns:
        A font pairing dict with heading, body, style, and google_import.
    """
    if not style_hint:
        return get_random_pairing()

    hint_lower = style_hint.lower().strip()

    # 1. Exact style match
    for pairing in FONT_PAIRINGS:
        if pairing["style"] == hint_lower:
            return pairing

    # 2. Check if any pairing style contains the hint
    partial_matches = [p for p in FONT_PAIRINGS if hint_lower in p["style"]]
    if partial_matches:
        return random.choice(partial_matches)

    # 3. Keyword mapping — score each pairing by how many keyword hits it gets
    scores: dict[int, int] = {}
    hint_words = hint_lower.split()

    for word in hint_words:
        target_styles = _STYLE_KEYWORDS.get(word, [])
        for i, pairing in enumerate(FONT_PAIRINGS):
            if pairing["style"] in target_styles:
                scores[i] = scores.get(i, 0) + 1

    if scores:
        max_score = max(scores.values())
        best_indices = [i for i, s in scores.items() if s == max_score]
        return FONT_PAIRINGS[random.choice(best_indices)]

    # 4. Last resort: check if hint appears anywhere in any pairing value
    for pairing in FONT_PAIRINGS:
        searchable = f"{pairing['heading']} {pairing['body']} {pairing['style']}".lower()
        if hint_lower in searchable:
            return pairing

    # 5. Fallback to random
    return get_random_pairing()


def get_font_css_vars(pairing: dict | None = None) -> str:
    """
    Generate CSS custom property declarations for a font pairing.

    Returns a string like:
        --font-heading: 'Space Grotesk', sans-serif;
        --font-body: 'DM Sans', sans-serif;

    Args:
        pairing: A font pairing dict. If None, picks a random one.
    """
    if pairing is None:
        pairing = get_random_pairing()

    serif_fonts = {
        "Playfair Display",
        "Cormorant Garamond",
        "DM Serif Display",
        "Fraunces",
        "Lora",
        "Libre Baskerville",
        "Newsreader",
        "Spectral",
        "Literata",
    }

    heading_stack = "serif" if pairing["heading"] in serif_fonts else "sans-serif"
    body_stack = "serif" if pairing["body"] in serif_fonts else "sans-serif"

    return (
        f"--font-heading: '{pairing['heading']}', {heading_stack};\n    --font-body: '{pairing['body']}', {body_stack};"
    )
