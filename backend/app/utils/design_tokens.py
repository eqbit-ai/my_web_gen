"""
Curated design token sets inspired by top-tier websites.
Each set is a complete design system with colors, radius, spacing, and shadows.
"""

import random

DESIGN_TOKEN_SETS = [
    # ─────────────────────────────────────────────
    # 1-10: TECH / SAAS
    # ─────────────────────────────────────────────
    {
        "name": "stripe",
        "style": "clean fintech",
        "niche": ["fintech", "saas", "corporate", "payments"],
        "colors": {
            "primary": "#635bff",
            "secondary": "#0a2540",
            "accent": "#00d4aa",
            "background": "#ffffff",
            "surface": "#f6f9fc",
            "text": "#0a2540",
            "text_muted": "#425466",
        },
        "radius": {"button": "9999px", "card": "12px", "input": "8px"},
        "spacing": {"section": "120px", "container": "1200px"},
        "shadows": {
            "card": "0 2px 8px rgba(0,0,0,0.08)",
            "elevated": "0 12px 40px rgba(0,0,0,0.12)",
        },
    },
    {
        "name": "apple",
        "style": "minimal elegant",
        "niche": ["technology", "product", "premium", "electronics"],
        "colors": {
            "primary": "#0071e3",
            "secondary": "#1d1d1f",
            "accent": "#2997ff",
            "background": "#ffffff",
            "surface": "#f5f5f7",
            "text": "#1d1d1f",
            "text_muted": "#6e6e73",
        },
        "radius": {"button": "980px", "card": "18px", "input": "12px"},
        "spacing": {"section": "100px", "container": "980px"},
        "shadows": {
            "card": "0 4px 16px rgba(0,0,0,0.06)",
            "elevated": "0 20px 60px rgba(0,0,0,0.1)",
        },
    },
    {
        "name": "linear",
        "style": "dark modern",
        "niche": ["developer", "saas", "tools", "startup"],
        "colors": {
            "primary": "#5e6ad2",
            "secondary": "#e8ecf0",
            "accent": "#8a7cff",
            "background": "#111111",
            "surface": "#1a1a1a",
            "text": "#e8ecf0",
            "text_muted": "#8a8f98",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "140px", "container": "1100px"},
        "shadows": {
            "card": "0 2px 8px rgba(0,0,0,0.3)",
            "elevated": "0 16px 48px rgba(0,0,0,0.4)",
        },
    },
    {
        "name": "vercel",
        "style": "monochrome developer",
        "niche": ["developer", "infrastructure", "tools", "hosting"],
        "colors": {
            "primary": "#000000",
            "secondary": "#171717",
            "accent": "#0070f3",
            "background": "#000000",
            "surface": "#111111",
            "text": "#ededed",
            "text_muted": "#888888",
        },
        "radius": {"button": "6px", "card": "8px", "input": "6px"},
        "spacing": {"section": "100px", "container": "1100px"},
        "shadows": {
            "card": "0 0 0 1px rgba(255,255,255,0.08)",
            "elevated": "0 8px 30px rgba(0,0,0,0.6)",
        },
    },
    {
        "name": "notion",
        "style": "warm minimal",
        "niche": ["productivity", "saas", "education", "notes"],
        "colors": {
            "primary": "#000000",
            "secondary": "#37352f",
            "accent": "#eb5757",
            "background": "#ffffff",
            "surface": "#f7f6f3",
            "text": "#37352f",
            "text_muted": "#9b9a97",
        },
        "radius": {"button": "4px", "card": "4px", "input": "4px"},
        "spacing": {"section": "80px", "container": "900px"},
        "shadows": {
            "card": "0 1px 3px rgba(0,0,0,0.08)",
            "elevated": "0 8px 24px rgba(0,0,0,0.12)",
        },
    },
    {
        "name": "figma",
        "style": "colorful creative",
        "niche": ["design", "creative", "tools", "collaboration"],
        "colors": {
            "primary": "#a259ff",
            "secondary": "#1e1e1e",
            "accent": "#0acf83",
            "background": "#ffffff",
            "surface": "#f5f5f5",
            "text": "#1e1e1e",
            "text_muted": "#7c7c7c",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "120px", "container": "1200px"},
        "shadows": {
            "card": "0 2px 12px rgba(0,0,0,0.06)",
            "elevated": "0 12px 36px rgba(0,0,0,0.12)",
        },
    },
    {
        "name": "airbnb",
        "style": "warm hospitality",
        "niche": ["travel", "hospitality", "booking", "rental"],
        "colors": {
            "primary": "#ff385c",
            "secondary": "#222222",
            "accent": "#008489",
            "background": "#ffffff",
            "surface": "#f7f7f7",
            "text": "#222222",
            "text_muted": "#717171",
        },
        "radius": {"button": "12px", "card": "16px", "input": "12px"},
        "spacing": {"section": "80px", "container": "1120px"},
        "shadows": {
            "card": "0 6px 20px rgba(0,0,0,0.08)",
            "elevated": "0 16px 40px rgba(0,0,0,0.12)",
        },
    },
    {
        "name": "spotify",
        "style": "dark bold",
        "niche": ["music", "entertainment", "streaming", "media"],
        "colors": {
            "primary": "#1db954",
            "secondary": "#191414",
            "accent": "#1ed760",
            "background": "#121212",
            "surface": "#1e1e1e",
            "text": "#ffffff",
            "text_muted": "#a7a7a7",
        },
        "radius": {"button": "9999px", "card": "8px", "input": "8px"},
        "spacing": {"section": "100px", "container": "1180px"},
        "shadows": {
            "card": "0 4px 12px rgba(0,0,0,0.3)",
            "elevated": "0 16px 48px rgba(0,0,0,0.5)",
        },
    },
    {
        "name": "shopify",
        "style": "green commerce",
        "niche": ["ecommerce", "retail", "commerce", "business"],
        "colors": {
            "primary": "#008060",
            "secondary": "#004c3f",
            "accent": "#5c6ac4",
            "background": "#ffffff",
            "surface": "#f6f6f7",
            "text": "#202223",
            "text_muted": "#6d7175",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "100px", "container": "1200px"},
        "shadows": {
            "card": "0 1px 6px rgba(0,0,0,0.08)",
            "elevated": "0 12px 32px rgba(0,0,0,0.1)",
        },
    },
    {
        "name": "slack",
        "style": "purple collaboration",
        "niche": ["communication", "collaboration", "saas", "team"],
        "colors": {
            "primary": "#4a154b",
            "secondary": "#1d1c1d",
            "accent": "#36c5f0",
            "background": "#ffffff",
            "surface": "#f8f8f8",
            "text": "#1d1c1d",
            "text_muted": "#616061",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "100px", "container": "1140px"},
        "shadows": {
            "card": "0 2px 8px rgba(0,0,0,0.08)",
            "elevated": "0 12px 36px rgba(0,0,0,0.14)",
        },
    },
    # ─────────────────────────────────────────────
    # 11-20: LUXURY / PREMIUM
    # ─────────────────────────────────────────────
    {
        "name": "gold_noir",
        "style": "luxury gold dark",
        "niche": ["luxury", "jewelry", "watches", "fashion"],
        "colors": {
            "primary": "#c9a84c",
            "secondary": "#1a1a1a",
            "accent": "#e8d5a3",
            "background": "#0d0d0d",
            "surface": "#1a1a1a",
            "text": "#f4f0e6",
            "text_muted": "#8a8578",
        },
        "radius": {"button": "0px", "card": "0px", "input": "0px"},
        "spacing": {"section": "140px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 20px rgba(0,0,0,0.4)",
            "elevated": "0 20px 60px rgba(0,0,0,0.6)",
        },
    },
    {
        "name": "cream_serif",
        "style": "editorial cream serif",
        "niche": ["luxury", "fashion", "editorial", "magazine"],
        "colors": {
            "primary": "#2c2c2c",
            "secondary": "#8b7355",
            "accent": "#c4a265",
            "background": "#faf7f2",
            "surface": "#f0ebe3",
            "text": "#2c2c2c",
            "text_muted": "#7a7267",
        },
        "radius": {"button": "0px", "card": "2px", "input": "2px"},
        "spacing": {"section": "120px", "container": "1060px"},
        "shadows": {
            "card": "0 2px 12px rgba(0,0,0,0.06)",
            "elevated": "0 16px 40px rgba(0,0,0,0.08)",
        },
    },
    {
        "name": "emerald_white",
        "style": "emerald luxury",
        "niche": ["luxury", "real_estate", "premium", "spa"],
        "colors": {
            "primary": "#006b5a",
            "secondary": "#00382e",
            "accent": "#72b49b",
            "background": "#ffffff",
            "surface": "#f5f9f7",
            "text": "#1a2e2a",
            "text_muted": "#5a7a72",
        },
        "radius": {"button": "4px", "card": "8px", "input": "4px"},
        "spacing": {"section": "120px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 16px rgba(0,107,90,0.08)",
            "elevated": "0 16px 48px rgba(0,107,90,0.12)",
        },
    },
    {
        "name": "navy_gold",
        "style": "navy gold classic",
        "niche": ["finance", "law", "consulting", "corporate"],
        "colors": {
            "primary": "#1b2a4a",
            "secondary": "#0f1c33",
            "accent": "#c8a951",
            "background": "#ffffff",
            "surface": "#f4f5f7",
            "text": "#1b2a4a",
            "text_muted": "#5e6d8a",
        },
        "radius": {"button": "4px", "card": "8px", "input": "4px"},
        "spacing": {"section": "100px", "container": "1140px"},
        "shadows": {
            "card": "0 2px 12px rgba(27,42,74,0.08)",
            "elevated": "0 12px 36px rgba(27,42,74,0.14)",
        },
    },
    {
        "name": "rose_luxe",
        "style": "rose gold feminine luxury",
        "niche": ["beauty", "cosmetics", "fashion", "bridal"],
        "colors": {
            "primary": "#b76e79",
            "secondary": "#2d2226",
            "accent": "#e8c4b8",
            "background": "#fffbf9",
            "surface": "#f9f0ec",
            "text": "#2d2226",
            "text_muted": "#8a7178",
        },
        "radius": {"button": "9999px", "card": "16px", "input": "12px"},
        "spacing": {"section": "110px", "container": "1080px"},
        "shadows": {
            "card": "0 4px 16px rgba(183,110,121,0.08)",
            "elevated": "0 16px 48px rgba(183,110,121,0.12)",
        },
    },
    {
        "name": "midnight_platinum",
        "style": "dark platinum premium",
        "niche": ["automotive", "luxury", "watches", "tech"],
        "colors": {
            "primary": "#a0a0a0",
            "secondary": "#e0e0e0",
            "accent": "#c0c0c0",
            "background": "#0a0a0a",
            "surface": "#151515",
            "text": "#e8e8e8",
            "text_muted": "#707070",
        },
        "radius": {"button": "2px", "card": "4px", "input": "2px"},
        "spacing": {"section": "140px", "container": "1200px"},
        "shadows": {
            "card": "0 4px 20px rgba(0,0,0,0.4)",
            "elevated": "0 24px 64px rgba(0,0,0,0.6)",
        },
    },
    {
        "name": "ivory_charcoal",
        "style": "ivory minimalist luxury",
        "niche": ["architecture", "interior_design", "gallery", "luxury"],
        "colors": {
            "primary": "#3a3a3a",
            "secondary": "#1f1f1f",
            "accent": "#9b8b6e",
            "background": "#f9f7f4",
            "surface": "#efece6",
            "text": "#1f1f1f",
            "text_muted": "#7c7c7c",
        },
        "radius": {"button": "0px", "card": "0px", "input": "0px"},
        "spacing": {"section": "130px", "container": "1100px"},
        "shadows": {
            "card": "0 2px 8px rgba(0,0,0,0.04)",
            "elevated": "0 12px 40px rgba(0,0,0,0.08)",
        },
    },
    {
        "name": "champagne_velvet",
        "style": "champagne velvet opulent",
        "niche": ["events", "wedding", "luxury", "hospitality"],
        "colors": {
            "primary": "#8b6914",
            "secondary": "#2a1f0e",
            "accent": "#d4a843",
            "background": "#fdfbf6",
            "surface": "#f5efe3",
            "text": "#2a1f0e",
            "text_muted": "#8a7d6a",
        },
        "radius": {"button": "6px", "card": "12px", "input": "6px"},
        "spacing": {"section": "120px", "container": "1060px"},
        "shadows": {
            "card": "0 4px 16px rgba(139,105,20,0.06)",
            "elevated": "0 16px 48px rgba(139,105,20,0.1)",
        },
    },
    {
        "name": "obsidian_ruby",
        "style": "dark ruby dramatic",
        "niche": ["nightlife", "entertainment", "luxury", "wine"],
        "colors": {
            "primary": "#9b1b30",
            "secondary": "#f0e6e8",
            "accent": "#d4475a",
            "background": "#0e0a0b",
            "surface": "#1a1315",
            "text": "#f0e6e8",
            "text_muted": "#8a7d80",
        },
        "radius": {"button": "4px", "card": "8px", "input": "4px"},
        "spacing": {"section": "120px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 20px rgba(155,27,48,0.15)",
            "elevated": "0 20px 60px rgba(155,27,48,0.2)",
        },
    },
    {
        "name": "pearl_sapphire",
        "style": "pearl sapphire refined",
        "niche": ["jewelry", "luxury", "premium", "finance"],
        "colors": {
            "primary": "#1a3a6a",
            "secondary": "#0d1f3c",
            "accent": "#5a8aba",
            "background": "#fefefe",
            "surface": "#f0f2f6",
            "text": "#0d1f3c",
            "text_muted": "#5a6478",
        },
        "radius": {"button": "6px", "card": "10px", "input": "6px"},
        "spacing": {"section": "110px", "container": "1120px"},
        "shadows": {
            "card": "0 2px 12px rgba(26,58,106,0.08)",
            "elevated": "0 16px 48px rgba(26,58,106,0.14)",
        },
    },
    # ─────────────────────────────────────────────
    # 21-30: FOOD / RESTAURANT
    # ─────────────────────────────────────────────
    {
        "name": "warm_earth",
        "style": "warm earthy organic",
        "niche": ["restaurant", "organic", "farm", "bakery"],
        "colors": {
            "primary": "#a0522d",
            "secondary": "#3e2212",
            "accent": "#d4883a",
            "background": "#fdf8f0",
            "surface": "#f0e6d4",
            "text": "#3e2212",
            "text_muted": "#7a6450",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "100px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 16px rgba(62,34,18,0.06)",
            "elevated": "0 12px 36px rgba(62,34,18,0.1)",
        },
    },
    {
        "name": "fresh_garden",
        "style": "fresh green natural",
        "niche": ["vegan", "salad", "healthy", "organic"],
        "colors": {
            "primary": "#2d8a4e",
            "secondary": "#1a3c2a",
            "accent": "#8bc34a",
            "background": "#ffffff",
            "surface": "#f2f8f0",
            "text": "#1a3c2a",
            "text_muted": "#5a7a5e",
        },
        "radius": {"button": "9999px", "card": "16px", "input": "12px"},
        "spacing": {"section": "90px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 14px rgba(45,138,78,0.06)",
            "elevated": "0 12px 36px rgba(45,138,78,0.1)",
        },
    },
    {
        "name": "dark_moody_kitchen",
        "style": "dark moody culinary",
        "niche": ["fine_dining", "restaurant", "steakhouse", "bar"],
        "colors": {
            "primary": "#d4a64a",
            "secondary": "#f5ecd7",
            "accent": "#e8c86a",
            "background": "#1a1612",
            "surface": "#252018",
            "text": "#f5ecd7",
            "text_muted": "#9a9080",
        },
        "radius": {"button": "0px", "card": "4px", "input": "2px"},
        "spacing": {"section": "120px", "container": "1080px"},
        "shadows": {
            "card": "0 4px 20px rgba(0,0,0,0.4)",
            "elevated": "0 20px 60px rgba(0,0,0,0.5)",
        },
    },
    {
        "name": "bistro_classic",
        "style": "french bistro classic",
        "niche": ["bistro", "french", "restaurant", "cafe"],
        "colors": {
            "primary": "#2b4c3f",
            "secondary": "#1a2e26",
            "accent": "#c49a6c",
            "background": "#faf6ef",
            "surface": "#ede5d8",
            "text": "#1a2e26",
            "text_muted": "#6a7a6e",
        },
        "radius": {"button": "2px", "card": "4px", "input": "2px"},
        "spacing": {"section": "100px", "container": "1040px"},
        "shadows": {
            "card": "0 2px 10px rgba(0,0,0,0.06)",
            "elevated": "0 12px 32px rgba(0,0,0,0.1)",
        },
    },
    {
        "name": "cafe_latte",
        "style": "warm cafe cozy",
        "niche": ["cafe", "coffee", "bakery", "brunch"],
        "colors": {
            "primary": "#6f4e37",
            "secondary": "#3a2718",
            "accent": "#c89b7b",
            "background": "#fdfaf5",
            "surface": "#f0e8da",
            "text": "#3a2718",
            "text_muted": "#8a7560",
        },
        "radius": {"button": "9999px", "card": "12px", "input": "8px"},
        "spacing": {"section": "90px", "container": "1060px"},
        "shadows": {
            "card": "0 2px 12px rgba(111,78,55,0.06)",
            "elevated": "0 12px 32px rgba(111,78,55,0.1)",
        },
    },
    {
        "name": "sushi_zen",
        "style": "japanese minimal zen",
        "niche": ["japanese", "sushi", "asian", "restaurant"],
        "colors": {
            "primary": "#c0392b",
            "secondary": "#2c2c2c",
            "accent": "#e8d5b7",
            "background": "#faf8f5",
            "surface": "#f0ece4",
            "text": "#2c2c2c",
            "text_muted": "#787878",
        },
        "radius": {"button": "2px", "card": "4px", "input": "2px"},
        "spacing": {"section": "110px", "container": "1000px"},
        "shadows": {
            "card": "0 2px 8px rgba(0,0,0,0.05)",
            "elevated": "0 8px 28px rgba(0,0,0,0.08)",
        },
    },
    {
        "name": "mediterranean",
        "style": "mediterranean warm coastal",
        "niche": ["mediterranean", "seafood", "greek", "restaurant"],
        "colors": {
            "primary": "#1a6b8a",
            "secondary": "#0e3d50",
            "accent": "#e8a832",
            "background": "#fffef9",
            "surface": "#f0ece0",
            "text": "#1a2a2e",
            "text_muted": "#5a7a7e",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "100px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 14px rgba(26,107,138,0.06)",
            "elevated": "0 12px 36px rgba(26,107,138,0.1)",
        },
    },
    {
        "name": "spice_market",
        "style": "vibrant spicy exotic",
        "niche": ["indian", "mexican", "thai", "street_food"],
        "colors": {
            "primary": "#d4532a",
            "secondary": "#2a1a0e",
            "accent": "#f5a623",
            "background": "#fffdf8",
            "surface": "#f8ede0",
            "text": "#2a1a0e",
            "text_muted": "#7a6a56",
        },
        "radius": {"button": "8px", "card": "10px", "input": "6px"},
        "spacing": {"section": "90px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 14px rgba(212,83,42,0.06)",
            "elevated": "0 12px 36px rgba(212,83,42,0.1)",
        },
    },
    {
        "name": "vineyard",
        "style": "wine vineyard rustic",
        "niche": ["winery", "wine", "vineyard", "fine_dining"],
        "colors": {
            "primary": "#722f37",
            "secondary": "#3a1820",
            "accent": "#c4956a",
            "background": "#faf6f1",
            "surface": "#efe6da",
            "text": "#3a1820",
            "text_muted": "#7a6a68",
        },
        "radius": {"button": "2px", "card": "6px", "input": "4px"},
        "spacing": {"section": "110px", "container": "1060px"},
        "shadows": {
            "card": "0 2px 10px rgba(114,47,55,0.06)",
            "elevated": "0 12px 36px rgba(114,47,55,0.1)",
        },
    },
    {
        "name": "patisserie",
        "style": "pastel sweet elegant",
        "niche": ["dessert", "patisserie", "bakery", "ice_cream"],
        "colors": {
            "primary": "#d4678a",
            "secondary": "#2e2028",
            "accent": "#f5c6a8",
            "background": "#fffbf8",
            "surface": "#fef0ea",
            "text": "#2e2028",
            "text_muted": "#8a7078",
        },
        "radius": {"button": "9999px", "card": "20px", "input": "12px"},
        "spacing": {"section": "90px", "container": "1060px"},
        "shadows": {
            "card": "0 4px 16px rgba(212,103,138,0.06)",
            "elevated": "0 12px 36px rgba(212,103,138,0.1)",
        },
    },
    # ─────────────────────────────────────────────
    # 31-40: HEALTH / WELLNESS
    # ─────────────────────────────────────────────
    {
        "name": "sage_wellness",
        "style": "sage green calm wellness",
        "niche": ["wellness", "yoga", "meditation", "spa"],
        "colors": {
            "primary": "#6b8f71",
            "secondary": "#2e4033",
            "accent": "#a3c4a8",
            "background": "#fafdf7",
            "surface": "#eef5ec",
            "text": "#2e4033",
            "text_muted": "#6a8070",
        },
        "radius": {"button": "9999px", "card": "16px", "input": "12px"},
        "spacing": {"section": "100px", "container": "1060px"},
        "shadows": {
            "card": "0 4px 14px rgba(107,143,113,0.06)",
            "elevated": "0 12px 36px rgba(107,143,113,0.1)",
        },
    },
    {
        "name": "ocean_health",
        "style": "ocean blue fresh health",
        "niche": ["healthcare", "dental", "clinic", "medical"],
        "colors": {
            "primary": "#1a7baa",
            "secondary": "#0a3a5a",
            "accent": "#4ac4d4",
            "background": "#ffffff",
            "surface": "#f0f7fa",
            "text": "#0a3a5a",
            "text_muted": "#5a7a8a",
        },
        "radius": {"button": "12px", "card": "16px", "input": "10px"},
        "spacing": {"section": "100px", "container": "1140px"},
        "shadows": {
            "card": "0 4px 16px rgba(26,123,170,0.06)",
            "elevated": "0 14px 40px rgba(26,123,170,0.1)",
        },
    },
    {
        "name": "sunrise_warm",
        "style": "sunrise warm energetic",
        "niche": ["fitness", "gym", "sport", "nutrition"],
        "colors": {
            "primary": "#e8652a",
            "secondary": "#2a1a10",
            "accent": "#f5a623",
            "background": "#fffcf7",
            "surface": "#fef0e4",
            "text": "#2a1a10",
            "text_muted": "#7a6a56",
        },
        "radius": {"button": "10px", "card": "14px", "input": "10px"},
        "spacing": {"section": "100px", "container": "1120px"},
        "shadows": {
            "card": "0 4px 14px rgba(232,101,42,0.06)",
            "elevated": "0 12px 36px rgba(232,101,42,0.1)",
        },
    },
    {
        "name": "zen_neutral",
        "style": "zen neutral grounding",
        "niche": ["mindfulness", "therapy", "counseling", "retreat"],
        "colors": {
            "primary": "#6a6152",
            "secondary": "#3a352a",
            "accent": "#b8a88a",
            "background": "#faf8f4",
            "surface": "#efebe4",
            "text": "#3a352a",
            "text_muted": "#8a8478",
        },
        "radius": {"button": "6px", "card": "8px", "input": "6px"},
        "spacing": {"section": "110px", "container": "960px"},
        "shadows": {
            "card": "0 2px 10px rgba(0,0,0,0.04)",
            "elevated": "0 10px 30px rgba(0,0,0,0.06)",
        },
    },
    {
        "name": "lavender_serenity",
        "style": "lavender serene calming",
        "niche": ["spa", "aromatherapy", "skincare", "wellness"],
        "colors": {
            "primary": "#7b6fa6",
            "secondary": "#3a2e52",
            "accent": "#c4b8e0",
            "background": "#fdfcff",
            "surface": "#f4f0fa",
            "text": "#2e2640",
            "text_muted": "#7a7290",
        },
        "radius": {"button": "9999px", "card": "20px", "input": "12px"},
        "spacing": {"section": "100px", "container": "1060px"},
        "shadows": {
            "card": "0 4px 16px rgba(123,111,166,0.06)",
            "elevated": "0 14px 40px rgba(123,111,166,0.1)",
        },
    },
    {
        "name": "clinical_modern",
        "style": "modern clinical professional",
        "niche": ["hospital", "pharmacy", "biotech", "healthcare"],
        "colors": {
            "primary": "#0066cc",
            "secondary": "#003366",
            "accent": "#00aacc",
            "background": "#ffffff",
            "surface": "#f0f4f8",
            "text": "#1a2a3a",
            "text_muted": "#5a6a7a",
        },
        "radius": {"button": "6px", "card": "8px", "input": "6px"},
        "spacing": {"section": "90px", "container": "1160px"},
        "shadows": {
            "card": "0 2px 10px rgba(0,102,204,0.06)",
            "elevated": "0 10px 32px rgba(0,102,204,0.1)",
        },
    },
    {
        "name": "herbal_apothecary",
        "style": "herbal natural apothecary",
        "niche": ["herbal", "natural", "supplement", "organic"],
        "colors": {
            "primary": "#4a6741",
            "secondary": "#2a3a22",
            "accent": "#8aad68",
            "background": "#faf9f4",
            "surface": "#eee9dc",
            "text": "#2a3a22",
            "text_muted": "#6a7a5e",
        },
        "radius": {"button": "4px", "card": "8px", "input": "4px"},
        "spacing": {"section": "100px", "container": "1060px"},
        "shadows": {
            "card": "0 2px 10px rgba(74,103,65,0.06)",
            "elevated": "0 10px 30px rgba(74,103,65,0.1)",
        },
    },
    {
        "name": "aqua_vitality",
        "style": "aqua vibrant active",
        "niche": ["swimming", "water_sport", "fitness", "athletic"],
        "colors": {
            "primary": "#00a8b5",
            "secondary": "#004d54",
            "accent": "#40e0d0",
            "background": "#ffffff",
            "surface": "#eaf8f9",
            "text": "#0a2a2e",
            "text_muted": "#4a7a7e",
        },
        "radius": {"button": "12px", "card": "16px", "input": "10px"},
        "spacing": {"section": "100px", "container": "1140px"},
        "shadows": {
            "card": "0 4px 14px rgba(0,168,181,0.06)",
            "elevated": "0 14px 40px rgba(0,168,181,0.1)",
        },
    },
    {
        "name": "blush_wellness",
        "style": "blush soft feminine wellness",
        "niche": ["pilates", "womens_health", "prenatal", "wellness"],
        "colors": {
            "primary": "#c47d8a",
            "secondary": "#4a2a32",
            "accent": "#e8b4b8",
            "background": "#fffbfb",
            "surface": "#faf0f0",
            "text": "#3a2028",
            "text_muted": "#8a6a72",
        },
        "radius": {"button": "9999px", "card": "20px", "input": "14px"},
        "spacing": {"section": "100px", "container": "1040px"},
        "shadows": {
            "card": "0 4px 16px rgba(196,125,138,0.06)",
            "elevated": "0 14px 40px rgba(196,125,138,0.1)",
        },
    },
    {
        "name": "forest_retreat",
        "style": "forest deep natural retreat",
        "niche": ["retreat", "camping", "eco", "nature"],
        "colors": {
            "primary": "#2d5a27",
            "secondary": "#1a3218",
            "accent": "#7ab648",
            "background": "#f8faf5",
            "surface": "#e8f0e0",
            "text": "#1a2e18",
            "text_muted": "#5a7050",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "110px", "container": "1080px"},
        "shadows": {
            "card": "0 4px 14px rgba(45,90,39,0.06)",
            "elevated": "0 12px 36px rgba(45,90,39,0.1)",
        },
    },
    # ─────────────────────────────────────────────
    # 41-50: CREATIVE / PORTFOLIO
    # ─────────────────────────────────────────────
    {
        "name": "neon_cyber",
        "style": "neon cyberpunk electric",
        "niche": ["gaming", "esports", "tech", "creative"],
        "colors": {
            "primary": "#00ff87",
            "secondary": "#e0e0e0",
            "accent": "#ff00e5",
            "background": "#0a0a0f",
            "surface": "#14141f",
            "text": "#e0e0e0",
            "text_muted": "#6a6a8a",
        },
        "radius": {"button": "4px", "card": "8px", "input": "4px"},
        "spacing": {"section": "120px", "container": "1200px"},
        "shadows": {
            "card": "0 0 20px rgba(0,255,135,0.06)",
            "elevated": "0 0 60px rgba(0,255,135,0.12)",
        },
    },
    {
        "name": "mono_portfolio",
        "style": "monochrome minimal portfolio",
        "niche": ["photography", "portfolio", "designer", "artist"],
        "colors": {
            "primary": "#222222",
            "secondary": "#111111",
            "accent": "#555555",
            "background": "#ffffff",
            "surface": "#f5f5f5",
            "text": "#111111",
            "text_muted": "#777777",
        },
        "radius": {"button": "0px", "card": "0px", "input": "0px"},
        "spacing": {"section": "100px", "container": "1200px"},
        "shadows": {
            "card": "none",
            "elevated": "0 8px 30px rgba(0,0,0,0.08)",
        },
    },
    {
        "name": "brutalist",
        "style": "brutalist raw bold",
        "niche": ["art", "experimental", "agency", "creative"],
        "colors": {
            "primary": "#000000",
            "secondary": "#ff0000",
            "accent": "#ffff00",
            "background": "#ffffff",
            "surface": "#f0f0f0",
            "text": "#000000",
            "text_muted": "#666666",
        },
        "radius": {"button": "0px", "card": "0px", "input": "0px"},
        "spacing": {"section": "60px", "container": "1400px"},
        "shadows": {
            "card": "4px 4px 0 #000000",
            "elevated": "8px 8px 0 #000000",
        },
    },
    {
        "name": "editorial_modern",
        "style": "editorial typographic magazine",
        "niche": ["magazine", "editorial", "blog", "publishing"],
        "colors": {
            "primary": "#1a1a1a",
            "secondary": "#2a2a2a",
            "accent": "#e63946",
            "background": "#fefefe",
            "surface": "#f8f8f8",
            "text": "#1a1a1a",
            "text_muted": "#6a6a6a",
        },
        "radius": {"button": "0px", "card": "2px", "input": "2px"},
        "spacing": {"section": "80px", "container": "860px"},
        "shadows": {
            "card": "0 1px 4px rgba(0,0,0,0.04)",
            "elevated": "0 6px 24px rgba(0,0,0,0.08)",
        },
    },
    {
        "name": "retro_pop",
        "style": "retro 70s pop colorful",
        "niche": ["music", "vintage", "creative", "brand"],
        "colors": {
            "primary": "#e85d26",
            "secondary": "#2a1a0e",
            "accent": "#f4c430",
            "background": "#fdf5e6",
            "surface": "#f0e0c8",
            "text": "#2a1a0e",
            "text_muted": "#7a6a56",
        },
        "radius": {"button": "9999px", "card": "16px", "input": "12px"},
        "spacing": {"section": "90px", "container": "1100px"},
        "shadows": {
            "card": "6px 6px 0 rgba(42,26,14,0.15)",
            "elevated": "10px 10px 0 rgba(42,26,14,0.2)",
        },
    },
    {
        "name": "gradient_aurora",
        "style": "gradient aurora modern",
        "niche": ["startup", "app", "creative", "tech"],
        "colors": {
            "primary": "#6c5ce7",
            "secondary": "#0c0c1d",
            "accent": "#00cec9",
            "background": "#0c0c1d",
            "surface": "#16162d",
            "text": "#e8e8f0",
            "text_muted": "#7a7a9a",
        },
        "radius": {"button": "12px", "card": "16px", "input": "10px"},
        "spacing": {"section": "120px", "container": "1140px"},
        "shadows": {
            "card": "0 4px 20px rgba(108,92,231,0.12)",
            "elevated": "0 16px 48px rgba(108,92,231,0.2)",
        },
    },
    {
        "name": "paper_craft",
        "style": "paper textured craft handmade",
        "niche": ["craft", "handmade", "stationery", "portfolio"],
        "colors": {
            "primary": "#5a4a3a",
            "secondary": "#3a2e22",
            "accent": "#c49a6c",
            "background": "#f5efe6",
            "surface": "#e8ddd0",
            "text": "#3a2e22",
            "text_muted": "#7a6e5e",
        },
        "radius": {"button": "4px", "card": "6px", "input": "4px"},
        "spacing": {"section": "90px", "container": "1000px"},
        "shadows": {
            "card": "0 2px 8px rgba(0,0,0,0.06)",
            "elevated": "0 8px 24px rgba(0,0,0,0.1)",
        },
    },
    {
        "name": "studio_bold",
        "style": "bold agency studio",
        "niche": ["agency", "studio", "branding", "design"],
        "colors": {
            "primary": "#ff3b30",
            "secondary": "#1c1c1e",
            "accent": "#ff9500",
            "background": "#ffffff",
            "surface": "#f2f2f7",
            "text": "#1c1c1e",
            "text_muted": "#8e8e93",
        },
        "radius": {"button": "10px", "card": "14px", "input": "8px"},
        "spacing": {"section": "120px", "container": "1240px"},
        "shadows": {
            "card": "0 4px 16px rgba(0,0,0,0.06)",
            "elevated": "0 16px 48px rgba(0,0,0,0.12)",
        },
    },
    {
        "name": "vaporwave",
        "style": "vaporwave aesthetic nostalgic",
        "niche": ["music", "art", "creative", "fashion"],
        "colors": {
            "primary": "#ff71ce",
            "secondary": "#01cdfe",
            "accent": "#b967ff",
            "background": "#1a0a2e",
            "surface": "#241440",
            "text": "#e8d0f4",
            "text_muted": "#8a6aaa",
        },
        "radius": {"button": "8px", "card": "12px", "input": "8px"},
        "spacing": {"section": "110px", "container": "1100px"},
        "shadows": {
            "card": "0 4px 20px rgba(255,113,206,0.12)",
            "elevated": "0 16px 48px rgba(185,103,255,0.2)",
        },
    },
    {
        "name": "architect",
        "style": "architectural grid precise",
        "niche": ["architecture", "construction", "engineering", "portfolio"],
        "colors": {
            "primary": "#2a2a2a",
            "secondary": "#1a1a1a",
            "accent": "#e74c3c",
            "background": "#ffffff",
            "surface": "#f0f0f0",
            "text": "#1a1a1a",
            "text_muted": "#808080",
        },
        "radius": {"button": "0px", "card": "0px", "input": "0px"},
        "spacing": {"section": "100px", "container": "1280px"},
        "shadows": {
            "card": "0 1px 4px rgba(0,0,0,0.06)",
            "elevated": "0 8px 30px rgba(0,0,0,0.1)",
        },
    },
]


# ─────────────────────────────────────────────
# NICHE → TOKEN SET MAPPING
# ─────────────────────────────────────────────

_NICHE_MAP: dict[str, list[str]] = {}


def _build_niche_map():
    """Build reverse map from niche keywords to token set names."""
    if _NICHE_MAP:
        return
    for token_set in DESIGN_TOKEN_SETS:
        for niche in token_set.get("niche", []):
            _NICHE_MAP.setdefault(niche, []).append(token_set["name"])


def _get_set_by_name(name: str) -> dict | None:
    """Get a token set by its name."""
    for ts in DESIGN_TOKEN_SETS:
        if ts["name"] == name:
            return ts
    return None


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────


def get_random_tokens() -> dict:
    """Return a random design token set."""
    return random.choice(DESIGN_TOKEN_SETS)


def get_tokens_for_niche(niche_key: str) -> dict:
    """
    Return the best matching token set for a given niche keyword.
    Falls back to a random set if no match is found.
    """
    _build_niche_map()
    niche_key = niche_key.lower().strip().replace(" ", "_")

    # Direct match
    if niche_key in _NICHE_MAP:
        name = random.choice(_NICHE_MAP[niche_key])
        return _get_set_by_name(name)

    # Partial match — check if niche_key is a substring of any mapped niche
    partial_matches = []
    for mapped_niche, names in _NICHE_MAP.items():
        if niche_key in mapped_niche or mapped_niche in niche_key:
            partial_matches.extend(names)

    if partial_matches:
        name = random.choice(partial_matches)
        return _get_set_by_name(name)

    # No match — return random
    return get_random_tokens()


def get_tokens_for_style(style: str) -> dict:
    """
    Fuzzy match a token set by style description.
    Checks for keyword overlap between the query and each set's style field.
    Falls back to a random set if no match is found.
    """
    style_lower = style.lower().strip()
    style_words = set(style_lower.split())

    best_match = None
    best_score = 0

    for token_set in DESIGN_TOKEN_SETS:
        set_style = token_set["style"].lower()
        set_words = set(set_style.split())

        # Score: number of overlapping words + substring bonus
        score = len(style_words & set_words)
        if style_lower in set_style or set_style in style_lower:
            score += 2

        if score > best_score:
            best_score = score
            best_match = token_set

    return best_match if best_match else get_random_tokens()


def format_tokens_for_prompt(tokens: dict) -> str:
    """
    Format a design token set as CSS custom properties for injection into LLM prompts.

    Returns a string like:
      --color-primary: #635bff;
      --color-secondary: #0a2540;
      ...
    """
    lines = []

    # Colors
    colors = tokens.get("colors", {})
    for key, value in colors.items():
        lines.append(f"  --color-{key.replace('_', '-')}: {value};")

    # Radius
    radius = tokens.get("radius", {})
    for key, value in radius.items():
        lines.append(f"  --radius-{key}: {value};")

    # Spacing
    spacing = tokens.get("spacing", {})
    for key, value in spacing.items():
        lines.append(f"  --spacing-{key}: {value};")

    # Shadows
    shadows = tokens.get("shadows", {})
    for key, value in shadows.items():
        lines.append(f"  --shadow-{key}: {value};")

    header = f"/* Design Tokens: {tokens.get('name', 'custom')} ({tokens.get('style', '')}) */\n:root {{"
    footer = "}"

    return f"{header}\n" + "\n".join(lines) + f"\n{footer}"
