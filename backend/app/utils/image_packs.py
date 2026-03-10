"""
Curated image query packs per niche.

Each pack provides PROVEN search queries that return high-quality, relevant images
from Unsplash/Pexels. These are injected into the planner prompt so the AI
generates better image_query values.

Structure: { niche_key: { role: [query1, query2, ...] } }
Roles: hero, feature, team, testimonial, gallery, cta, background, product
"""

# ═══════════════════════════════════════════════════════════════════════
# CURATED IMAGE PACKS
# ═══════════════════════════════════════════════════════════════════════

IMAGE_PACKS: dict[str, dict[str, list[str]]] = {

    # ── FOOD & BEVERAGE ────────────────────────────────────────────────

    "restaurant": {
        "hero": ["restaurant interior warm lighting", "fine dining table setting", "elegant restaurant evening"],
        "feature": ["gourmet dish plating", "chef preparing food", "fresh ingredients cutting board", "pasta dish closeup", "sushi platter presentation"],
        "team": ["chef portrait kitchen", "sommelier wine cellar", "restaurant manager portrait"],
        "testimonial": ["woman dining portrait", "man restaurant headshot", "couple dinner portrait"],
        "gallery": ["restaurant dish overhead", "cocktail bar drinks", "dessert plating artistic", "steak dinner plate"],
        "cta": ["reserved table candlelight", "restaurant patio evening"],
    },

    "bakery": {
        "hero": ["bakery display case pastries", "fresh bread wooden table", "artisan bakery interior"],
        "feature": ["croissant golden closeup", "decorated cake layers", "bread dough kneading", "pastry cream filling"],
        "team": ["baker portrait flour", "pastry chef decorating"],
        "gallery": ["cupcake display colorful", "sourdough bread loaf", "wedding cake elegant", "danish pastry assortment"],
        "cta": ["bakery morning sunlight", "fresh baked cookies tray"],
    },

    "coffee_shop": {
        "hero": ["coffee shop interior cozy", "barista pouring latte art", "cafe morning sunlight"],
        "feature": ["espresso machine closeup", "latte art rosetta", "coffee beans roasting", "pour over brewing"],
        "team": ["barista portrait smile", "cafe owner portrait"],
        "gallery": ["cappuccino overhead shot", "iced coffee summer", "coffee shop atmosphere", "pastry coffee pairing"],
        "cta": ["friends coffee table", "laptop coffee workspace"],
    },

    "food_truck": {
        "hero": ["food truck street festival", "colorful food truck exterior", "food truck window serving"],
        "feature": ["street tacos closeup", "burger fries basket", "loaded nachos plate", "grilled food outdoor"],
        "gallery": ["food truck lineup festival", "street food cooking flames", "takeaway box colorful"],
        "cta": ["food truck crowd outdoor", "street food happy customer"],
    },

    # ── TECHNOLOGY ─────────────────────────────────────────────────────

    "tech_startup": {
        "hero": ["startup office modern workspace", "developer team collaboration", "tech office open plan"],
        "feature": ["laptop code screen", "mobile app phone hand", "data dashboard monitor", "cloud server room"],
        "team": ["developer portrait office", "tech founder headshot", "engineer woman portrait"],
        "testimonial": ["business professional headshot", "startup founder portrait", "tech executive suit"],
        "cta": ["team celebration office", "laptop coffee modern desk"],
        "product": ["macbook desk minimal clean", "phone app interface hand", "tablet dashboard modern"],
    },

    "ai_startup": {
        "hero": ["futuristic server room blue", "neural network visualization", "AI robot arm technology"],
        "feature": ["machine learning data screen", "chip circuit board macro", "autonomous vehicle sensor", "chatbot interface screen"],
        "team": ["data scientist portrait", "AI researcher woman", "tech engineer portrait"],
        "cta": ["futuristic city technology", "digital transformation office"],
        "product": ["laptop AI dashboard", "phone AI assistant screen"],
    },

    "web_agency": {
        "hero": ["design agency office creative", "web design monitors workspace", "creative team brainstorming"],
        "feature": ["wireframe sketch notebook", "responsive design devices", "UI design colorful screen", "brand identity mockup"],
        "team": ["designer portrait creative", "developer portrait desk", "project manager headshot"],
        "gallery": ["website mockup laptop", "mobile app design showcase", "brand guide layout"],
        "cta": ["agency team meeting", "creative workspace overhead"],
    },

    # ── HEALTHCARE ─────────────────────────────────────────────────────

    "healthcare": {
        "hero": ["modern hospital lobby", "doctor patient consultation", "medical clinic interior"],
        "feature": ["doctor stethoscope portrait", "medical equipment lab", "nurse caring patient", "telehealth video call"],
        "team": ["doctor portrait white coat", "nurse portrait smile", "surgeon portrait scrubs"],
        "testimonial": ["patient smile portrait", "elderly patient happy", "family health portrait"],
        "cta": ["doctor handshake patient", "modern clinic reception"],
    },

    "dentist": {
        "hero": ["dental office modern interior", "dentist patient chair", "bright dental clinic"],
        "feature": ["dental tools closeup", "teeth whitening treatment", "dental xray screen", "orthodontic braces smile"],
        "team": ["dentist portrait smile", "dental hygienist portrait", "orthodontist portrait"],
        "cta": ["confident smile closeup", "dental office reception"],
    },

    # ── PROFESSIONAL SERVICES ──────────────────────────────────────────

    "law_firm": {
        "hero": ["law office library books", "courthouse columns exterior", "legal office conference room"],
        "feature": ["contract signing pen", "legal scales justice", "lawyer reviewing documents", "courtroom interior"],
        "team": ["lawyer portrait suit", "attorney woman portrait", "legal partner headshot"],
        "testimonial": ["business executive headshot", "corporate professional portrait"],
        "cta": ["handshake business agreement", "law office meeting room"],
    },

    "consulting": {
        "hero": ["business meeting conference table", "consulting office skyline view", "strategy session whiteboard"],
        "feature": ["presentation boardroom screen", "analytics charts laptop", "team workshop sticky notes", "business growth chart"],
        "team": ["consultant portrait suit", "business woman executive", "management advisor headshot"],
        "cta": ["handshake partnership deal", "office skyline panorama"],
    },

    "accounting": {
        "hero": ["accounting office desk organized", "financial documents calculator", "modern accounting firm interior"],
        "feature": ["spreadsheet laptop screen", "tax documents folder", "calculator financial report", "audit review meeting"],
        "team": ["accountant portrait professional", "financial advisor headshot", "CPA woman portrait"],
        "cta": ["business growth success", "organized desk financial"],
    },

    "financial_advisor": {
        "hero": ["financial office modern interior", "advisor client meeting desk", "wealth management office"],
        "feature": ["stock market charts screen", "retirement planning documents", "investment portfolio graph", "financial planning meeting"],
        "team": ["financial advisor portrait", "wealth manager headshot", "investment banker portrait"],
        "cta": ["piggy bank savings concept", "financial freedom sunset"],
    },

    "insurance": {
        "hero": ["insurance office professional", "family protection concept", "insurance agent meeting"],
        "feature": ["umbrella protection concept", "house key handover", "car insurance document", "health insurance card"],
        "team": ["insurance agent portrait", "broker professional headshot"],
        "cta": ["family home happy", "shield protection concept"],
    },

    # ── REAL ESTATE & HOSPITALITY ──────────────────────────────────────

    "real_estate": {
        "hero": ["luxury house exterior twilight", "modern apartment skyline", "real estate agent showing home"],
        "feature": ["living room interior modern", "kitchen renovation white", "bedroom cozy modern", "bathroom luxury marble"],
        "team": ["real estate agent portrait", "property manager headshot", "realtor woman portrait"],
        "gallery": ["penthouse view city", "backyard pool house", "townhouse exterior brick", "condo balcony sunset"],
        "cta": ["house keys handover", "sold sign front yard"],
    },

    "hotel": {
        "hero": ["luxury hotel lobby chandelier", "resort pool ocean view", "boutique hotel entrance"],
        "feature": ["hotel room bed elegant", "hotel restaurant dining", "spa treatment room candle", "rooftop bar night"],
        "team": ["hotel concierge portrait", "hotel manager headshot"],
        "gallery": ["hotel suite luxury", "infinity pool resort", "hotel bathroom marble", "hotel lounge fireplace"],
        "cta": ["couple vacation beach resort", "hotel balcony sea view"],
    },

    # ── FITNESS & WELLNESS ─────────────────────────────────────────────

    "fitness": {
        "hero": ["gym interior modern equipment", "athlete training workout", "fitness class group"],
        "feature": ["weightlifting barbell gym", "yoga class stretching", "running treadmill gym", "boxing training ring"],
        "team": ["personal trainer portrait", "fitness coach woman", "gym instructor headshot"],
        "testimonial": ["fit person portrait gym", "athlete woman portrait"],
        "gallery": ["crossfit workout action", "spinning class bikes", "gym equipment weights", "stretching fitness mat"],
        "cta": ["athlete victory pose", "gym motivation sunrise"],
    },

    "beauty_salon": {
        "hero": ["beauty salon interior elegant", "hairstylist salon chair", "luxury spa treatment"],
        "feature": ["hair styling blowout", "manicure nail art", "facial treatment spa", "makeup artist applying"],
        "team": ["hairstylist portrait salon", "esthetician portrait spa", "makeup artist portrait"],
        "gallery": ["hair color transformation", "bridal makeup elegant", "nail art designs", "spa relaxation candle"],
        "cta": ["woman hair blowing beauty", "spa relaxation peaceful"],
    },

    # ── EDUCATION ──────────────────────────────────────────────────────

    "education": {
        "hero": ["university campus building", "students lecture hall", "modern classroom learning"],
        "feature": ["student studying library", "teacher classroom whiteboard", "online learning laptop", "science lab students"],
        "team": ["professor portrait university", "teacher portrait smile", "academic advisor headshot"],
        "gallery": ["campus quad students", "graduation ceremony caps", "library reading room", "student collaboration group"],
        "cta": ["graduation success celebration", "student laptop studying"],
    },

    "online_course": {
        "hero": ["online learning laptop home", "video course filming setup", "student headphones studying"],
        "feature": ["video lesson screen", "certificate achievement", "mobile learning phone", "webinar presentation screen"],
        "team": ["instructor portrait camera", "course creator headshot", "educator woman portrait"],
        "cta": ["student success laptop", "learning achievement certificate"],
    },

    # ── RETAIL & ECOMMERCE ─────────────────────────────────────────────

    "ecommerce": {
        "hero": ["online shopping phone hand", "ecommerce packaging delivery", "fashion product display"],
        "feature": ["product photography white", "shipping box unboxing", "mobile shopping cart", "payment card checkout"],
        "cta": ["happy customer unboxing", "shopping bags colorful"],
    },

    "jewelry_store": {
        "hero": ["jewelry display luxury", "diamond ring velvet", "luxury jewelry store interior"],
        "feature": ["gold necklace closeup", "engagement ring box", "bracelet wrist elegant", "earrings model portrait"],
        "gallery": ["watch luxury leather", "pearl necklace elegant", "gemstone ring collection", "jewelry crafting workshop"],
        "cta": ["woman wearing jewelry elegant", "gift box jewelry ribbon"],
    },

    # ── SERVICES ───────────────────────────────────────────────────────

    "cleaning_service": {
        "hero": ["clean modern living room", "cleaning team professional", "sparkling kitchen interior"],
        "feature": ["cleaning supplies organized", "vacuum cleaning carpet", "window cleaning streak free", "bathroom cleaning spotless"],
        "team": ["cleaning professional portrait", "team cleaning uniforms"],
        "cta": ["happy family clean home", "spotless office space"],
    },

    "plumbing": {
        "hero": ["plumber working pipes", "modern bathroom fixtures", "plumbing tools workshop"],
        "feature": ["pipe wrench repair", "kitchen faucet installation", "water heater tank", "drain cleaning service"],
        "team": ["plumber portrait uniform", "technician portrait tools"],
        "cta": ["modern kitchen faucet", "bathroom renovation new"],
    },

    "electrician": {
        "hero": ["electrician working panel", "electrical wiring installation", "modern electrical panel"],
        "feature": ["circuit breaker panel", "wiring repair hands", "lighting installation ceiling", "electrical outlet work"],
        "team": ["electrician portrait hardhat", "technician portrait uniform"],
        "cta": ["modern home lighting", "smart home automation"],
    },

    "landscaping": {
        "hero": ["beautiful garden landscape", "landscaping team working", "manicured lawn house"],
        "feature": ["garden design planting", "lawn mowing stripes", "tree trimming service", "patio stone installation"],
        "team": ["landscaper portrait garden", "gardener portrait outdoors"],
        "gallery": ["backyard garden design", "flower bed colorful", "patio landscape outdoor", "hedge trimming shaped"],
        "cta": ["beautiful backyard sunset", "lush green garden path"],
    },

    "auto_repair": {
        "hero": ["auto mechanic workshop", "car repair garage interior", "mechanic working engine"],
        "feature": ["engine diagnostic computer", "brake repair service", "oil change maintenance", "tire alignment machine"],
        "team": ["mechanic portrait garage", "auto technician portrait"],
        "cta": ["car keys handover", "restored car showroom"],
    },

    # ── CREATIVE & DESIGN ──────────────────────────────────────────────

    "photography": {
        "hero": ["photographer shooting outdoors", "photography studio setup", "camera lens closeup"],
        "feature": ["portrait session studio", "wedding photography couple", "product photography setup", "landscape photography scenic"],
        "team": ["photographer portrait camera", "videographer portrait"],
        "gallery": ["portrait dramatic lighting", "wedding couple sunset", "architecture photography building", "nature photography wildlife"],
        "cta": ["camera sunset silhouette", "photo album memories"],
    },

    "architecture_firm": {
        "hero": ["modern building facade glass", "architecture firm office", "blueprint drafting table"],
        "feature": ["building rendering 3D", "interior design modern", "construction site progress", "sustainable architecture green"],
        "team": ["architect portrait helmet", "designer portrait studio"],
        "gallery": ["glass skyscraper modern", "residential architecture house", "interior office modern", "museum architecture exterior"],
        "cta": ["architectural model hands", "city skyline sunset"],
    },

    "interior_design": {
        "hero": ["luxury living room interior", "interior designer workspace", "modern apartment design"],
        "feature": ["minimalist bedroom design", "kitchen island marble", "bathroom spa modern", "office interior design"],
        "team": ["interior designer portrait", "decorator fabric samples"],
        "gallery": ["scandinavian living room", "industrial loft interior", "coastal bedroom blue", "mid century modern furniture"],
        "cta": ["design mood board samples", "beautiful home interior"],
    },

    "graphic_design": {
        "hero": ["design studio creative workspace", "graphic designer computer monitor", "creative agency office"],
        "feature": ["brand identity mockup", "typography letterpress", "color palette swatches", "packaging design product"],
        "team": ["designer portrait tablet", "creative director portrait"],
        "gallery": ["poster design colorful", "logo design sketches", "magazine layout design", "business card mockup"],
        "cta": ["creative tools desk", "design thinking whiteboard"],
    },

    # ── ENTERTAINMENT & EVENTS ─────────────────────────────────────────

    "wedding_planner": {
        "hero": ["wedding venue decorated", "elegant wedding table setup", "bride bouquet garden"],
        "feature": ["wedding ceremony arch flowers", "reception table candles", "wedding cake tiered", "bridal party portraits"],
        "team": ["wedding planner portrait", "event coordinator headshot"],
        "gallery": ["outdoor wedding ceremony", "wedding reception ballroom", "bridal details rings", "first dance couple"],
        "cta": ["newlywed couple sunset", "wedding rings flowers"],
    },

    "tour_operator": {
        "hero": ["tropical beach resort", "mountain hiking trail scenic", "ancient ruins tourism"],
        "feature": ["safari jeep wildlife", "cruise ship ocean", "city tour bus", "scuba diving coral reef"],
        "team": ["tour guide portrait outdoors", "travel advisor headshot"],
        "gallery": ["sunset beach paradise", "european village colorful", "jungle waterfall scenic", "desert safari dunes"],
        "cta": ["airplane window clouds", "passport tickets adventure"],
    },

    # ── AUTOMOTIVE ─────────────────────────────────────────────────────

    "car_dealership": {
        "hero": ["luxury car showroom", "dealership lot aerial", "sports car dramatic lighting"],
        "feature": ["car interior leather", "electric vehicle charging", "test drive road", "car financing office"],
        "team": ["car salesman portrait", "dealer manager headshot"],
        "gallery": ["SUV exterior mountain", "sedan highway driving", "convertible coastal road", "electric car city"],
        "cta": ["car keys handover happy", "new car delivery lot"],
    },

    # ── NONPROFIT ──────────────────────────────────────────────────────

    "charity": {
        "hero": ["volunteer team community", "charity event crowd", "helping hands together"],
        "feature": ["community garden volunteers", "food bank donation", "children education program", "environmental cleanup"],
        "team": ["nonprofit director portrait", "volunteer leader headshot"],
        "gallery": ["charity run marathon", "donation drive event", "community building project", "awareness campaign"],
        "cta": ["hands holding heart", "community together sunrise"],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# CATEGORY FALLBACK PACKS (for niches without specific packs)
# ═══════════════════════════════════════════════════════════════════════

CATEGORY_PACKS: dict[str, dict[str, list[str]]] = {
    "Food & Beverage": {
        "hero": ["restaurant interior dining", "food plating overhead", "chef cooking kitchen"],
        "feature": ["gourmet dish closeup", "fresh ingredients table", "food preparation hands"],
        "team": ["chef portrait kitchen", "food professional headshot"],
        "cta": ["dining table friends", "food celebration toast"],
    },
    "Technology": {
        "hero": ["tech office modern workspace", "developer coding screens", "startup team meeting"],
        "feature": ["laptop code screen", "mobile app interface", "server room technology"],
        "team": ["developer portrait office", "tech professional headshot"],
        "cta": ["team success celebration", "innovation technology concept"],
    },
    "Healthcare": {
        "hero": ["medical clinic modern", "doctor consultation patient", "hospital interior lobby"],
        "feature": ["medical equipment modern", "healthcare professional caring", "clinic treatment room"],
        "team": ["doctor portrait white coat", "nurse portrait smile"],
        "cta": ["healthy family outdoors", "patient recovery smile"],
    },
    "Professional Services": {
        "hero": ["corporate office modern", "business meeting conference", "professional workspace downtown"],
        "feature": ["presentation screen meeting", "contract signing desk", "analytics laptop screen"],
        "team": ["professional portrait suit", "executive woman headshot"],
        "cta": ["business handshake deal", "success office skyline"],
    },
    "Real Estate & Hospitality": {
        "hero": ["luxury property exterior", "modern interior living room", "resort scenic view"],
        "feature": ["house interior modern", "property exterior twilight", "room design elegant"],
        "team": ["agent portrait professional", "manager headshot smile"],
        "cta": ["house keys handover", "dream home sunset"],
    },
    "Fitness & Wellness": {
        "hero": ["gym modern interior", "fitness training action", "wellness spa relaxation"],
        "feature": ["workout equipment gym", "yoga class stretching", "spa treatment room"],
        "team": ["trainer portrait fitness", "wellness coach headshot"],
        "cta": ["athlete motivation sunrise", "healthy lifestyle outdoors"],
    },
    "Education": {
        "hero": ["campus university building", "students classroom learning", "library modern interior"],
        "feature": ["student studying laptop", "teacher classroom board", "online course screen"],
        "team": ["professor portrait university", "instructor headshot smile"],
        "cta": ["graduation celebration caps", "student success achievement"],
    },
    "Design & Creative": {
        "hero": ["creative studio workspace", "designer working computer", "art gallery interior"],
        "feature": ["design mockup screen", "creative tools desk", "portfolio showcase"],
        "team": ["designer portrait studio", "creative director headshot"],
        "cta": ["inspiration mood board", "creative workspace organized"],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def get_image_pack(niche_key: str) -> dict[str, list[str]] | None:
    """Get the curated image pack for a niche. Falls back to category pack."""
    if niche_key in IMAGE_PACKS:
        return IMAGE_PACKS[niche_key]

    # Try category fallback
    from app.utils.niches import NICHES
    niche = NICHES.get(niche_key)
    if niche:
        category = niche.get("category", "")
        if category in CATEGORY_PACKS:
            return CATEGORY_PACKS[category]

    return None


def get_curated_urls(niche_key: str, role: str) -> list[str] | None:
    """Get pre-vetted image URLs for a specific niche + role.

    Returns None — this is a hook for future expansion where we store
    actual verified URLs instead of search queries.
    """
    # Future: store actual verified Unsplash/Pexels URLs here
    # For now, we rely on the query packs above to improve search quality
    return None
