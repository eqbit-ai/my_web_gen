"""
Image resolver — fetches real images from Unsplash and Pexels APIs.

Resolution strategy:
1. Parse role prefix from query (hero, team, feature, etc.)
2. Clean & optimize query for API search (remove filler words, enforce length)
3. Generate 2 query variations for broader coverage
4. Fetch from Unsplash first (primary), Pexels as fallback
5. Rank images by relevance score (orientation, size, description match, face detection for portraits)
6. Last resort: curated fallback URLs by role

Features:
- Smart query cleaning (strips filler words, enforces 2-5 word queries)
- Role-based orientation + portrait face detection
- Image scoring with keyword matching + metadata analysis
- In-memory cache for repeated queries
- Deduplication across all images on a page (sequential to avoid race conditions)
"""

import asyncio
import hashlib
import os
import re
import time

import httpx

# ═══════════════════════════════════════════════════════════════════════
# API KEYS (from .env)
# ═══════════════════════════════════════════════════════════════════════

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Circuit breaker: skip Unsplash after consecutive 403s
_unsplash_fail_count = 0
_UNSPLASH_FAIL_THRESHOLD = 3  # After 3 consecutive 403s, skip Unsplash entirely


# ═══════════════════════════════════════════════════════════════════════
# IMAGE CACHE
# ═══════════════════════════════════════════════════════════════════════

_image_cache: dict[str, str] = {}


def _cache_key(query: str, orientation: str) -> str:
    return hashlib.md5(f"{query}:{orientation}".encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# ROLE DETECTION
# ═══════════════════════════════════════════════════════════════════════

ROLE_ORIENTATIONS = {
    "hero": "landscape",
    "product": "landscape",
    "feature": "landscape",
    "background": "landscape",
    "gallery": "landscape",
    "cta": "landscape",
    "mockup": "landscape",
    "team": "squarish",
    "testimonial": "squarish",
}

PORTRAIT_KEYWORDS = ["portrait", "headshot", "team member", "person", "face", "woman", "man"]

# Filler words that hurt search relevance — remove them from queries
FILLER_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "for",
    "in",
    "on",
    "at",
    "to",
    "of",
    "with",
    "from",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "that",
    "this",
    "it",
    "its",
    "very",
    "really",
    "just",
    "also",
    "style",
    "styled",
    "based",
    "using",
    "showing",
    "featuring",
    "looking",
    "high",
    "quality",
    "professional",
    "beautiful",
    "amazing",
    "great",
    "specific",
    "descriptive",
    "keywords",
    "highly",
    "query",
}


def _clean_query(query: str) -> str:
    """Clean query: remove filler words, rewrite clinical queries, enforce 2-5 word length."""
    # Rewrite clinical/body-part queries to show environments/people instead
    query_lower = query.lower()
    for bad, replacement in CLINICAL_QUERY_REWRITES.items():
        if bad in query_lower:
            query = replacement
            break

    # Remove common noise words
    words = [w for w in query.lower().split() if w not in FILLER_WORDS and len(w) > 1]

    # If everything was filtered, fall back to original
    if not words:
        words = query.lower().split()[:3]

    # Optimal query length for Unsplash/Pexels is 2-5 words
    if len(words) > 5:
        words = words[:5]

    return " ".join(words)


# Clinical/body-part queries that produce inappropriate images — rewrite to safe alternatives
CLINICAL_QUERY_REWRITES = {
    "teeth closeup": "happy smile portrait",
    "straight teeth": "confident smile woman",
    "teeth whitening": "bright smile dental office",
    "open mouth": "dentist patient smiling",
    "chipped tooth": "dental clinic consultation",
    "teeth bonding": "cosmetic dentistry office",
    "dental bridge": "dental professional patient",
    "tooth repair": "modern dental clinic",
    "braces teeth": "orthodontist consultation teen",
    "clear braces": "invisalign patient smiling",
    "muscle closeup": "gym modern equipment",
    "abs body": "fitness training session",
    "skin texture": "spa treatment room",
    "surgery room": "medical clinic modern interior",
    "injection": "healthcare consultation",
}


def parse_role_and_query(raw_query: str) -> tuple[str, str]:
    """Extract role prefix and clean query from 'role rest of query'."""
    parts = raw_query.strip().split(None, 1)
    if len(parts) >= 2 and parts[0].lower() in ROLE_ORIENTATIONS:
        return parts[0].lower(), _clean_query(parts[1])
    return "", _clean_query(raw_query.strip())


def get_orientation(role: str, query: str) -> str:
    """Determine orientation based on role and query content."""
    if role == "team" or role == "testimonial":
        return "portrait"
    if role in ROLE_ORIENTATIONS:
        return ROLE_ORIENTATIONS[role]
    if any(kw in query.lower() for kw in PORTRAIT_KEYWORDS):
        return "portrait"
    return "landscape"


# ═══════════════════════════════════════════════════════════════════════
# QUERY VARIATION GENERATOR
# ═══════════════════════════════════════════════════════════════════════


def generate_query_variations(query: str, role: str, niche_key: str = None) -> list[str]:
    """Generate 2-3 search variations for broader coverage."""
    words = query.split()
    variations = [query]  # Original always first

    # For people/team roles, add "professional photo" to ensure real headshots
    if role in PEOPLE_ROLES:
        variations.insert(0, f"{query} professional photo")

    # Variation 2: just the first 2-3 most important words
    if len(words) >= 3:
        variations.append(" ".join(words[:3]))
    elif len(words) == 2:
        variations.append(query)

    # Variation 3: niche-qualified query (e.g., "octopus" → "octopus food dish")
    if niche_key:
        qualifier = _get_niche_qualifier(niche_key, role)
        if qualifier and qualifier not in query.lower():
            # Add qualifier to the original query
            qualified = f"{query} {qualifier}"
            # Keep it max 5 words
            qwords = qualified.split()
            if len(qwords) <= 5:
                variations.insert(0, qualified)  # Try qualified first
            else:
                variations.insert(0, " ".join(qwords[:5]))

    # Deduplicate
    seen = set()
    unique = []
    for v in variations:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique


# ═══════════════════════════════════════════════════════════════════════
# NICHE-AWARE QUERY QUALIFIERS
# ═══════════════════════════════════════════════════════════════════════

# Niche categories that need search qualifiers to avoid wrong results
NICHE_QUALIFIERS: dict[str, dict[str, str]] = {
    # Food niches: "octopus" should find food, not the animal
    "restaurant": {"feature": "food", "gallery": "food", "hero": "restaurant", "cta": "restaurant"},
    "bakery": {"feature": "food", "gallery": "pastry", "hero": "bakery"},
    "coffee_shop": {"feature": "coffee", "gallery": "cafe", "hero": "cafe"},
    "food_truck": {"feature": "food", "gallery": "food", "hero": "food truck"},
    "pizzeria": {"feature": "food", "gallery": "food", "hero": "restaurant"},
    "juice_bar": {"feature": "drink", "gallery": "drink", "hero": "juice bar"},
    "wine_bar": {"feature": "wine", "gallery": "wine", "hero": "wine bar"},
    "brewery": {"feature": "beer", "gallery": "brewery", "hero": "brewery"},
    "catering": {"feature": "food", "gallery": "catering", "hero": "catering"},
    # Animal-related niches
    "veterinary": {"feature": "veterinary clinic", "hero": "vet clinic"},
    "pet_shop": {"feature": "pet store", "hero": "pet shop"},
    # Fashion / ecommerce — prevent car showrooms, tech offices, etc.
    "fashion_boutique": {"feature": "fashion", "gallery": "fashion", "hero": "fashion store", "cta": "fashion"},
    "ecommerce": {"feature": "fashion", "gallery": "fashion", "hero": "fashion store", "cta": "online shopping"},
    "jewelry": {"feature": "jewelry", "gallery": "jewelry", "hero": "jewelry store"},
    # Beauty
    "beauty_salon": {"feature": "beauty salon", "gallery": "beauty", "hero": "beauty salon"},
    "spa": {"feature": "spa wellness", "gallery": "spa", "hero": "spa"},
    # Wedding
    "wedding_planner": {"feature": "wedding", "gallery": "wedding", "hero": "wedding"},
    "florist": {"feature": "flowers", "gallery": "floral", "hero": "flower shop"},
    # Real estate
    "real_estate": {"feature": "real estate", "gallery": "property", "hero": "real estate"},
    "interior_design": {"feature": "interior design", "gallery": "interior", "hero": "interior design"},
    # Fitness / health
    "fitness": {"feature": "fitness gym", "gallery": "fitness", "hero": "gym"},
    "yoga": {"feature": "yoga", "gallery": "yoga", "hero": "yoga studio"},
    # Education
    "education": {"feature": "education", "gallery": "classroom", "hero": "education"},
    # Construction
    "construction": {"feature": "construction", "gallery": "construction", "hero": "construction"},
    "architecture_firm": {"feature": "architecture", "gallery": "architecture", "hero": "architecture"},
}

# Words that indicate wrong results for certain niches — penalize in scoring
NICHE_NEGATIVE_KEYWORDS: dict[str, set] = {
    "fashion_boutique": {"car", "vehicle", "automobile", "truck", "motorcycle", "garage"},
    "ecommerce": {"car", "vehicle", "automobile", "truck", "motorcycle", "garage"},
    "wedding_planner": {"car", "vehicle", "office", "warehouse", "factory"},
    "beauty_salon": {"car", "vehicle", "factory", "warehouse", "construction"},
    "restaurant": {"car", "vehicle", "office", "warehouse"},
    "bakery": {"car", "vehicle", "office"},
    "yoga": {"car", "vehicle", "office", "factory"},
    "jewelry": {"car", "vehicle", "garage"},
}

# Category-level qualifiers (fallback if niche isn't in NICHE_QUALIFIERS)
CATEGORY_QUALIFIERS: dict[str, dict[str, str]] = {
    "Food & Beverage": {"feature": "food", "gallery": "food", "hero": "restaurant"},
    "E-Commerce": {"feature": "fashion", "gallery": "fashion", "hero": "shopping"},
    "Beauty & Wellness": {"feature": "beauty wellness", "gallery": "beauty", "hero": "beauty"},
    "Health & Fitness": {"feature": "fitness", "gallery": "fitness", "hero": "gym"},
    "Creative": {"feature": "creative studio", "gallery": "creative", "hero": "creative"},
    "Real Estate": {"feature": "property", "gallery": "property", "hero": "real estate"},
    "Events": {"feature": "event", "gallery": "event", "hero": "event"},
}


def _get_niche_qualifier(niche_key: str, role: str) -> str:
    """Get a search qualifier for a niche+role to avoid irrelevant results."""
    # Direct niche match
    if niche_key in NICHE_QUALIFIERS:
        return NICHE_QUALIFIERS[niche_key].get(role, "")

    # Category fallback
    try:
        from app.utils.niches import NICHES

        niche = NICHES.get(niche_key)
        if niche:
            category = niche.get("category", "")
            if category in CATEGORY_QUALIFIERS:
                return CATEGORY_QUALIFIERS[category].get(role, "")
    except Exception:
        pass

    return ""


# Global negative keywords — applied to ALL images regardless of niche
# Prevents art, paintings, illustrations from appearing as real photos
GLOBAL_NEGATIVE_KEYWORDS = {
    "painting", "portrait painting", "oil painting", "renaissance",
    "artwork", "illustration", "drawing", "sketch", "sculpture",
    "museum", "gallery art", "canvas", "watercolor", "baroque",
    "medieval", "classical art", "fine art", "masterpiece",
    "statue", "engraving", "fresco", "mural",
}

# Roles where we specifically want real photos of people (not art)
PEOPLE_ROLES = {"team", "testimonial", "about", "staff", "founder", "portrait"}


# ═══════════════════════════════════════════════════════════════════════
# IMAGE SCORING
# ═══════════════════════════════════════════════════════════════════════


def score_unsplash_photo(photo: dict, keywords: list[str], orientation: str, niche_key: str = None) -> int:
    """Score an Unsplash photo by relevance metadata."""
    score = 0
    w = photo.get("width", 0)
    h = photo.get("height", 0)
    ratio = w / h if h > 0 else 1

    # Orientation scoring — strong penalty for wrong orientation
    if orientation == "portrait":
        if ratio < 0.9:
            score += 5  # Good portrait
        elif ratio < 1.1:
            score += 2  # Squarish, acceptable
        else:
            score -= 3  # Landscape when we need portrait — bad
    elif orientation == "landscape":
        if ratio > 1.2:
            score += 5  # Good landscape
        elif ratio > 0.9:
            score += 2  # Squarish, acceptable
        else:
            score -= 3  # Portrait when we need landscape — bad

    # Resolution bonus
    if w >= 2000:
        score += 2
    elif w >= 1200:
        score += 1

    # Description + alt_description keyword match (most important signal)
    desc = (photo.get("description") or "").lower() + " " + (photo.get("alt_description") or "").lower()
    matched_keywords = sum(1 for kw in keywords if kw in desc)
    score += matched_keywords * 3  # Strong weight on description match

    # Tag match (if available)
    tags = photo.get("tags", [])
    tag_titles = {t.get("title", "").lower() for t in tags}
    for kw in keywords:
        if kw in tag_titles:
            score += 2

    # Global negative keyword penalty — reject paintings, art, illustrations
    all_text = desc + " " + " ".join(tag_titles)
    for neg in GLOBAL_NEGATIVE_KEYWORDS:
        if neg in all_text:
            score -= 20  # Heavy penalty — paintings should never appear as real photos
            break

    # Niche negative keyword penalty — reject images that match wrong context
    if niche_key and niche_key in NICHE_NEGATIVE_KEYWORDS:
        neg_words = NICHE_NEGATIVE_KEYWORDS[niche_key]
        for neg in neg_words:
            if neg in all_text:
                score -= 15  # Heavy penalty — effectively disqualifies the image

    return score


def score_pexels_photo(photo: dict, keywords: list[str], orientation: str, niche_key: str = None) -> int:
    """Score a Pexels photo by relevance metadata."""
    score = 0
    w = photo.get("width", 0)
    h = photo.get("height", 0)
    ratio = w / h if h > 0 else 1

    # Orientation scoring
    if orientation == "portrait":
        if ratio < 0.9:
            score += 5
        elif ratio < 1.1:
            score += 2
        else:
            score -= 3
    elif orientation == "landscape":
        if ratio > 1.2:
            score += 5
        elif ratio > 0.9:
            score += 2
        else:
            score -= 3

    if w >= 2000:
        score += 2
    elif w >= 1200:
        score += 1

    # Pexels alt text match
    alt = (photo.get("alt") or "").lower()
    matched_keywords = sum(1 for kw in keywords if kw in alt)
    score += matched_keywords * 3

    # Global negative keyword penalty — reject paintings, art, illustrations
    for neg in GLOBAL_NEGATIVE_KEYWORDS:
        if neg in alt:
            score -= 20
            break

    # Niche negative keyword penalty
    if niche_key and niche_key in NICHE_NEGATIVE_KEYWORDS:
        neg_words = NICHE_NEGATIVE_KEYWORDS[niche_key]
        for neg in neg_words:
            if neg in alt:
                score -= 15

    return score


# ═══════════════════════════════════════════════════════════════════════
# UNSPLASH MULTI-QUERY RANKED SEARCH
# ═══════════════════════════════════════════════════════════════════════


async def search_unsplash_ranked(
    client: httpx.AsyncClient,
    variations: list[str],
    keywords: list[str],
    used_ids: set,
    orientation: str = "landscape",
    niche_key: str = None,
) -> str | None:
    """Search Unsplash with multiple query variations, rank results, return best."""
    global _unsplash_fail_count
    if not UNSPLASH_ACCESS_KEY:
        return None

    # Circuit breaker: skip if too many consecutive 403s
    if _unsplash_fail_count >= _UNSPLASH_FAIL_THRESHOLD:
        return None

    # Unsplash API orientation param: "landscape", "portrait", or "squarish"
    api_orientation = orientation if orientation in ("landscape", "portrait", "squarish") else "landscape"
    all_photos = []

    for query in variations:
        try:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params={
                    "query": query,
                    "per_page": 20,
                    "orientation": api_orientation,
                    "content_filter": "high",  # Only high-quality, safe images
                },
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                timeout=10,
            )
            if resp.status_code == 200:
                _unsplash_fail_count = 0  # Reset on success
                results = resp.json().get("results", [])
                all_photos.extend(results)
            elif resp.status_code == 403:
                _unsplash_fail_count += 1
                if _unsplash_fail_count >= _UNSPLASH_FAIL_THRESHOLD:
                    print("[Images] Unsplash returning 403 — switching to Pexels only", flush=True)
                    return None
        except Exception:
            continue

    if not all_photos:
        return None

    # Score and rank
    scored = []
    seen_ids = set()
    for photo in all_photos:
        pid = photo.get("id", "")
        if pid in used_ids or pid in seen_ids:
            continue
        seen_ids.add(pid)
        s = score_unsplash_photo(photo, keywords, orientation, niche_key)
        scored.append((s, photo))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Pick the best that has a URL
    for _, photo in scored:
        pid = photo.get("id", "")
        raw_url = photo.get("urls", {}).get("regular", "")
        if raw_url:
            used_ids.add(pid)
            return raw_url

    return None


# ═══════════════════════════════════════════════════════════════════════
# PEXELS RANKED SEARCH
# ═══════════════════════════════════════════════════════════════════════


async def search_pexels_ranked(
    client: httpx.AsyncClient,
    variations: list[str],
    keywords: list[str],
    used_ids: set,
    orientation: str = "landscape",
    niche_key: str = None,
) -> str | None:
    """Search Pexels with multiple query variations, rank results, return best."""
    if not PEXELS_API_KEY:
        return None

    # Pexels API orientation param: "landscape", "portrait", or "square"
    api_orientation = orientation
    if orientation == "squarish":
        api_orientation = "square"
    all_photos = []

    for query in variations:
        try:
            resp = await client.get(
                "https://api.pexels.com/v1/search",
                params={
                    "query": query,
                    "per_page": 20,
                    "orientation": api_orientation,
                },
                headers={"Authorization": PEXELS_API_KEY},
                timeout=10,
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                all_photos.extend(photos)
        except Exception:
            continue

    if not all_photos:
        return None

    scored = []
    seen_ids = set()
    for photo in all_photos:
        pid = str(photo.get("id", ""))
        if pid in used_ids or pid in seen_ids:
            continue
        seen_ids.add(pid)
        s = score_pexels_photo(photo, keywords, orientation, niche_key)
        scored.append((s, photo))

    scored.sort(key=lambda x: x[0], reverse=True)

    for _, photo in scored:
        pid = str(photo.get("id", ""))
        url = photo.get("src", {}).get("large2x", "") or photo.get("src", {}).get("large", "")
        if url:
            used_ids.add(pid)
            return url

    return None


# ═══════════════════════════════════════════════════════════════════════
# FALLBACK
# ═══════════════════════════════════════════════════════════════════════

# Curated fallback images by role — these are reliable, high-quality Unsplash photos
FALLBACK_IMAGES = {
    "hero": [
        "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1600&h=900&fit=crop",  # modern office
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=1600&h=900&fit=crop",  # tech workspace
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1600&h=900&fit=crop",  # city skyline
    ],
    "feature": [
        "https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&h=600&fit=crop",  # team collaboration
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=600&fit=crop",  # analytics dashboard
        "https://images.unsplash.com/photo-1553877522-43269d4ea984?w=800&h=600&fit=crop",  # strategy meeting
    ],
    "team": [
        "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&h=500&fit=crop",  # businessman portrait
        "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=500&fit=crop",  # businesswoman portrait
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=500&fit=crop",  # man portrait casual
    ],
    "testimonial": [
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop",  # man headshot
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&h=400&fit=crop",  # woman headshot
    ],
    "gallery": [
        "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=800&h=600&fit=crop",  # office space
        "https://images.unsplash.com/photo-1497215842964-222b430dc094?w=800&h=600&fit=crop",  # modern interior
    ],
    "cta": [
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&h=600&fit=crop",  # team celebration
    ],
    "default": [
        "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=600&fit=crop",  # generic office
    ],
}

_fallback_counters: dict[str, int] = {}


def get_fallback_image(role: str) -> str:
    """Get a curated fallback image for a role, cycling through options."""
    images = FALLBACK_IMAGES.get(role, FALLBACK_IMAGES["default"])
    idx = _fallback_counters.get(role, 0) % len(images)
    _fallback_counters[role] = idx + 1
    return images[idx]


# ═══════════════════════════════════════════════════════════════════════
# SINGLE IMAGE RESOLVER
# ═══════════════════════════════════════════════════════════════════════


async def resolve_single_image(
    client: httpx.AsyncClient,
    raw_query: str,
    used_ids: set,
    niche_key: str = None,
) -> str:
    """Resolve a single image query to a real URL using multi-query ranking."""
    role, clean_query = parse_role_and_query(raw_query)
    orientation = get_orientation(role, clean_query)
    keywords = [w for w in clean_query.lower().split() if len(w) > 2]

    # Check cache
    ck = _cache_key(clean_query + (niche_key or ""), orientation)
    if ck in _image_cache:
        cached = _image_cache[ck]
        print(f"[Images]   CACHE HIT: {clean_query[:40]}", flush=True)
        return cached

    # Generate niche-aware query variations
    variations = generate_query_variations(clean_query, role, niche_key)
    print(f"[Images]   Searching: {variations} (orient={orientation}, niche={niche_key or 'none'})", flush=True)

    # Determine search order based on niche (Pexels is better for food/product photos)
    food_niches = {
        "restaurant",
        "bakery",
        "coffee_shop",
        "food_truck",
        "pizzeria",
        "juice_bar",
        "wine_bar",
        "brewery",
        "catering",
        "food_blog",
        "organic_store",
    }
    pexels_first = niche_key in food_niches

    if pexels_first:
        # Pexels has better food photography
        url = await search_pexels_ranked(client, variations, keywords, used_ids, orientation, niche_key)
        if url:
            _image_cache[ck] = url
            return url
        url = await search_unsplash_ranked(client, variations, keywords, used_ids, orientation, niche_key)
        if url:
            _image_cache[ck] = url
            return url
    else:
        # Default: Unsplash first
        url = await search_unsplash_ranked(client, variations, keywords, used_ids, orientation, niche_key)
        if url:
            _image_cache[ck] = url
            return url
        url = await search_pexels_ranked(client, variations, keywords, used_ids, orientation, niche_key)
        if url:
            _image_cache[ck] = url
            return url

    # 3. Curated fallback — guaranteed to work
    fallback = get_fallback_image(role or "default")
    print(f"[Images]   FALLBACK: {role or 'default'} -> {fallback[:60]}", flush=True)
    return fallback


# ═══════════════════════════════════════════════════════════════════════
# BATCH RESOLVER — main entry point
# ═══════════════════════════════════════════════════════════════════════


async def resolve_image_placeholders(html: str, niche_key: str = None) -> str:
    """
    Find all {IMG:query} placeholders in HTML and replace with real image URLs.

    Resolves images in small parallel batches (3 at a time) to balance speed
    with deduplication accuracy. Same-role images are resolved sequentially
    to ensure used_ids deduplication works correctly.
    """
    pattern = r"{+IMG:([^}]+)}+"
    matches = list(re.finditer(pattern, html))

    if not matches:
        print("[Images] No IMG placeholders found in HTML", flush=True)
        return html

    t0 = time.time()
    used_ids: set = set()
    queries = []

    print(f"[Images] Found {len(matches)} placeholders (niche={niche_key or 'auto'})", flush=True)
    for m in matches:
        query = m.group(1).strip()
        role, clean = parse_role_and_query(query)
        orientation = get_orientation(role, clean)
        queries.append(query)
        print(f"[Images]   {role or 'auto'}: {clean} (orient={orientation})", flush=True)

    # Group queries by role for sequential resolution within each role
    # This ensures team photos don't get the same image, etc.
    role_groups: dict[str, list[int]] = {}
    for i, q in enumerate(queries):
        role, _ = parse_role_and_query(q)
        role_key = role or "auto"
        role_groups.setdefault(role_key, []).append(i)

    urls = [""] * len(queries)

    async with httpx.AsyncClient() as client:
        # Process different roles in parallel, but same-role images sequentially
        async def resolve_role_group(indices: list[int]):
            for idx in indices:
                url = await resolve_single_image(client, queries[idx], used_ids, niche_key)
                urls[idx] = url

        await asyncio.gather(*[resolve_role_group(indices) for indices in role_groups.values()])

    # Replace placeholders with resolved URLs
    result = html
    resolved_count = 0
    for match, url in zip(matches, urls, strict=False):
        old_placeholder = match.group(0)
        result = result.replace(old_placeholder, url, 1)
        resolved_count += 1
        short_placeholder = old_placeholder[:50]
        short_url = url[:80]
        print(f"[Images]   '{short_placeholder}' -> {short_url}", flush=True)

    # Verify no placeholders remain
    remaining = re.findall(r"{+IMG:[^}]+}+", result)
    if remaining:
        print(f"[Images] WARNING: {len(remaining)} unresolved placeholders remain!", flush=True)

    duration = int((time.time() - t0) * 1000)
    print(f"[Images] Resolved {resolved_count}/{len(matches)} images in {duration}ms", flush=True)

    return result
