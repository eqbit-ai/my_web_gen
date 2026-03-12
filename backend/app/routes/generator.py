"""
Generator routes — 3-stage AI website generation pipeline:

  Stage 1: Plan  → GPT-4.1 → JSON structure + content + layout patterns
  Stage 2: HTML  → Claude  → HTML with pure CSS classes + <style> block
  Stage 3: JS    → Claude  → Interactions/animations

CSS is semantic classes in a <style> block (layout, components, responsive).
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.utils.audit_log import log_event_bg
from app.utils.auth import decode_access_token
from app.utils.circuit_breaker import CircuitOpenError, circuit_protected
from app.utils.content_moderation import moderate_prompt
from app.utils.image_resolver import resolve_image_placeholders
from app.utils.input_sanitizer import sanitize_prompt
from app.utils.llm_clients import get_anthropic_client, get_openai_client
from app.utils.metrics import increment as metrics_increment
from app.utils.metrics import observe as metrics_observe
from app.utils.patterns import enforce_pattern_rotation, get_pattern_template, record_used_patterns
from app.utils.plan_validator import validate_and_fix_plan
from app.utils.prompt_pipeline import (
    ADD_PAGE_HTML_PROMPT,
    APPEND_SECTION_PROMPT,
    COMPONENT_EDIT_PROMPT,
    COMPONENT_PATTERNS,
    COMPONENT_ROUTER_PROMPT,
    ITERATION_SYSTEM_PROMPT,
    JS_GEN_SYSTEM_PROMPT,
    PLAN_SHORT_PROMPT_ADDENDUM,
    PROMPT_ENHANCE_SYSTEM,
    STYLE_EDIT_PROMPT,
    build_html_prompt,
    build_page_html_prompt,
    build_plan_prompt,
    detect_add_page_request,
    extract_section_types,
    get_design_seed,
    is_multipage_request,
    parse_code_blocks,
    parse_json_response,
    parse_single_code_block,
    summarize_html,
)
from app.utils.section_parser import inject_section_ids, parse_sections, replace_section_html
from app.utils.session_store import (
    delete_session as redis_delete_session,
)
from app.utils.session_store import (
    get_session as redis_get_session,
)
from app.utils.session_store import (
    save_session as redis_save_session,
)
from app.utils.session_store import (
    session_exists as redis_session_exists,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_session_ownership(session: dict, user: dict) -> None:
    """Verify that the session belongs to the authenticated user."""
    session_user = session.get("user_id")
    if session_user and str(session_user) != str(user.get("user_id")):
        raise HTTPException(status_code=403, detail="Forbidden — session belongs to another user")


security = HTTPBearer()

# Debug output directory — use /tmp to avoid triggering uvicorn --reload
DEBUG_DIR = os.path.join(
    os.environ.get("DEBUG_OUTPUT_DIR", "/tmp/meydan_debug"),
)


# ═══════════════════════════════════════════════════════════════════════
# AUTO-MATCH REFERENCE TEMPLATE BY NICHE
# ═══════════════════════════════════════════════════════════════════════


def _find_best_reference_template(niche_key: str) -> str | None:
    """Find the closest matching template for a detected niche.
    Returns the template HTML+CSS string, or None if no match."""
    from app.routes.templates import _load_template_file, TEMPLATE_CATALOG

    # Direct match: niche_key matches a template ID
    template_ids = [t["id"] for t in TEMPLATE_CATALOG]
    if niche_key in template_ids:
        try:
            html, css = _load_template_file(niche_key)
            return f"<style>{css}</style>\n{html}"
        except Exception:
            pass

    # Niche-to-template mapping for indirect matches
    NICHE_TEMPLATE_MAP = {
        "pharmacy": "dentist",
        "clinic": "dentist",
        "hospital": "dentist",
        "medical": "dentist",
        "veterinary": "pet_shop",
        "spa": "beauty_salon",
        "barbershop": "beauty_salon",
        "gym": "fitness",
        "personal_trainer": "fitness",
        "martial_arts": "fitness",
        "cafe": "coffee_shop",
        "catering": "restaurant",
        "food_truck": "restaurant",
        "bar": "restaurant",
        "juice_bar": "coffee_shop",
        "construction": "architecture",
        "plumber": "cleaning_service",
        "electrician": "cleaning_service",
        "hvac": "cleaning_service",
        "roofing": "cleaning_service",
        "landscaping": "cleaning_service",
        "insurance": "consulting",
        "financial_advisor": "accounting",
        "recruitment": "consulting",
        "marketing_agency": "consulting",
        "web_agency": "tech_startup",
        "saas": "tech_startup",
        "software": "tech_startup",
        "ai_startup": "tech_startup",
        "blockchain": "tech_startup",
        "cybersecurity": "tech_startup",
        "iot": "tech_startup",
        "it_services": "tech_startup",
        "gaming": "tech_startup",
        "gallery": "photography",
        "videography": "photography",
        "graphic_design": "portfolio",
        "freelancer": "portfolio",
        "artist": "music_artist",
        "band": "music_artist",
        "dj": "music_artist",
        "tutoring": "coding_bootcamp",
        "language_school": "coding_bootcamp",
        "music_school": "coding_bootcamp",
        "daycare": "coding_bootcamp",
        "driving_school": "coding_bootcamp",
        "church": "charity",
        "community_center": "charity",
        "nonprofit": "charity",
        "bridal": "wedding_planner",
        "florist": "flower_shop",
        "jewelry": "beauty_salon",
        "fashion": "ecommerce",
        "retail": "ecommerce",
        "furniture": "interior_design",
        "home_decor": "interior_design",
        "auto_repair": "car_dealership",
        "car_rental": "car_dealership",
        "logistics": "moving_company",
        "courier": "moving_company",
        "coworking_space": "real_estate",
    }

    mapped = NICHE_TEMPLATE_MAP.get(niche_key)
    if mapped:
        try:
            html, css = _load_template_file(mapped)
            return f"<style>{css}</style>\n{html}"
        except Exception:
            pass

    return None


# ═══════════════════════════════════════════════════════════════════════
# LOGGING HELPER
# ═══════════════════════════════════════════════════════════════════════


def _fmt_duration(ms: int) -> str:
    """Format milliseconds as human-readable duration."""
    if ms < 1000:
        return f"{ms}ms"
    secs = ms / 1000
    if secs < 60:
        return f"{secs:.1f}s"
    mins = int(secs // 60)
    remaining = secs % 60
    return f"{mins}m {remaining:.0f}s"


def log_stage(stage_name: str, duration_ms: int, response_len: int, success: bool, detail: str = ""):
    """Human-readable stage logging."""
    status = "OK" if success else "FAILED"
    detail_str = f" — {detail}" if detail else ""
    logger.info(f"[{stage_name}] {status} in {_fmt_duration(duration_ms)} ({response_len:,} chars){detail_str}")


def save_debug(session_id: str, stage: str, content: str):
    """Save stage output to debug directory."""
    try:
        debug_dir = os.path.join(DEBUG_DIR, session_id[:8])
        os.makedirs(debug_dir, exist_ok=True)
        ext = {"plan": "json", "html": "html", "css": "css", "js": "js"}.get(stage, "txt")
        with open(os.path.join(debug_dir, f"{stage}.{ext}"), "w") as f:
            f.write(content)
    except Exception:
        pass  # Debug storage is best-effort


# ═══════════════════════════════════════════════════════════════════════
# CSS POLISH
# ═══════════════════════════════════════════════════════════════════════


def polish_css(css: str, theme: str = "light") -> str:
    """Auto-inject premium CSS polish if missing."""
    additions = []

    # Smooth scroll behavior
    if "scroll-behavior" not in css:
        additions.append("html { scroll-behavior: smooth; }")

    # Better image rendering
    if "image-rendering" not in css:
        additions.append("img { image-rendering: -webkit-optimize-contrast; }")

    # Selection color matching brand
    if "::selection" not in css:
        additions.append("::selection { background: var(--primary); color: white; }")

    # Focus visible for accessibility
    if ":focus-visible" not in css:
        additions.append(":focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }")

    # Smooth transitions on all interactive elements
    if "transition" not in css or "a, button" not in css:
        additions.append("a, button { transition: all 0.3s ease; }")

    # Better font rendering
    if "-webkit-font-smoothing" not in css:
        additions.append("body { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility; }")

    # Dark theme specific polish
    if theme == "dark":
        if "scrollbar" not in css:
            additions.append("::-webkit-scrollbar { width: 8px; }")
            additions.append("::-webkit-scrollbar-track { background: var(--bg); }")
            additions.append("::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }")

    if additions:
        polish = "\n/* === Auto-polish === */\n" + "\n".join(additions) + "\n"
        # Insert before closing </style> or append to end
        css = css.rstrip() + "\n" + polish

    return css


# ═══════════════════════════════════════════════════════════════════════
# IMAGE SAFETY
# ═══════════════════════════════════════════════════════════════════════


def _convert_hallucinated_urls_to_placeholders(html: str) -> str:
    """Convert hallucinated Pexels/Unsplash URLs to {{IMG:}} placeholders.

    Claude sometimes ignores the {{IMG:}} instruction and generates fake
    image URLs that return 404. This catches them and converts to placeholders
    using the alt text, so the image resolver can fetch real images.
    """
    import re as _re

    # Pattern: <img with src containing pexels or unsplash URLs
    def _replace_img_src(match: _re.Match) -> str:
        full_tag = match.group(0)
        # Extract alt text to use as image query
        alt_match = _re.search(r'alt=["\']([^"\']+)["\']', full_tag)
        alt_text = alt_match.group(1) if alt_match else "professional business photo"

        # Determine role from context
        role = "feature"
        alt_lower = alt_text.lower()
        if any(w in alt_lower for w in ("hero", "banner", "main")):
            role = "hero"
        elif any(w in alt_lower for w in ("team", "chef", "portrait", "person", "staff")):
            role = "team"
        elif any(w in alt_lower for w in ("testimonial", "review", "client")):
            role = "testimonial"
        elif any(w in alt_lower for w in ("food", "dish", "menu", "cuisine", "restaurant")):
            role = "feature"
        elif any(w in alt_lower for w in ("gallery", "photo")):
            role = "gallery"
        elif any(w in alt_lower for w in ("event", "celebration", "music")):
            role = "feature"

        placeholder = f"{{{{IMG:{role} {alt_text}}}}}"
        # Replace the src value
        new_tag = _re.sub(
            r'src=["\']https?://images\.(pexels|unsplash)\.com/[^"\']+["\']',
            f'src="{placeholder}"',
            full_tag,
        )
        return new_tag

    # Also handle background-image: url(...) with pexels/unsplash
    def _replace_bg_url(match: _re.Match) -> str:
        return match.group(0).replace(
            match.group(1),
            "{{IMG:background professional scene}}",
        )

    # Count before
    hallucinated_count = len(_re.findall(
        r'src=["\']https?://images\.(pexels|unsplash)\.com/photos/[^"\']+["\']',
        html,
    ))

    if hallucinated_count > 0:
        logger.warning(
            f"⚠️ {hallucinated_count} hallucinated image URLs detected — converting to {{IMG:}} placeholders"
        )
        # Replace <img src="https://images.pexels.com/..."> tags
        html = _re.sub(
            r'<img\s[^>]*src=["\']https?://images\.(pexels|unsplash)\.com/photos/[^"\']+["\'][^>]*>',
            _replace_img_src,
            html,
        )
        # Replace background-image: url('https://images.pexels.com/...')
        html = _re.sub(
            r"background-image:\s*url\(['\"]?(https?://images\.(pexels|unsplash)\.com/photos/[^'\")]+)['\"]?\)",
            _replace_bg_url,
            html,
        )

    return html


def _strip_comment_markers(html: str) -> str:
    """Strip SEO_META and FAVICON comment markers so --> doesn't leak into rendered output."""
    html = re.sub(r'<!--\s*SEO_META\s*-->\s*', '', html)
    html = re.sub(r'<!--\s*END_SEO_META\s*-->\s*', '', html)
    html = re.sub(r'<!--\s*FAVICON\s*-->\s*', '', html)
    html = re.sub(r'<!--\s*END_FAVICON\s*-->\s*', '', html)
    return html


async def _resolve_images_safe(html: str, niche_key: str = None) -> str:
    """Resolve image placeholders with safety cleanup for any unresolved ones."""
    # First: convert any hallucinated Pexels/Unsplash URLs to {{IMG:}} placeholders
    html = _convert_hallucinated_urls_to_placeholders(html)

    # Then resolve placeholders to real image URLs
    html = await resolve_image_placeholders(html, niche_key=niche_key)

    # Safety: replace any unresolved {{IMG:...}} placeholders with a fallback
    unresolved = re.findall(r'\{\{IMG:[^}]+\}\}', html)
    if unresolved:
        logger.warning(f"⚠️ {len(unresolved)} unresolved image placeholders — using fallback")
        html = re.sub(
            r'\{\{IMG:[^}]+\}\}',
            'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=600&fit=crop',
            html,
        )

    # Strip comment markers that leak into rendered output
    html = _strip_comment_markers(html)

    return html


# ═══════════════════════════════════════════════════════════════════════
# OUTPUT VALIDATORS
# ═══════════════════════════════════════════════════════════════════════


def validate_html(html: str) -> str:
    """Validate HTML output meets minimum quality."""
    # Strip any code fence markers the LLM may have left
    html = re.sub(r"^```\w*\s*\n?", "", html.strip())
    html = re.sub(r"\n?```\s*$", "", html.strip())

    if not html or len(html) < 200:
        raise ValueError(f"HTML too short ({len(html)} chars) — generation likely failed")
    if len(html) > 150000:
        raise ValueError(f"HTML too large ({len(html)} chars) — may be truncated or malformed")
    if "data-section-type" not in html:
        raise ValueError("HTML missing data-section-type attributes")

    # Ensure every section with data-section-type is wrapped in a <section> tag
    # Fix cases where AI uses <div> instead of <section>
    html = re.sub(
        r'<div(\s+[^>]*data-section-type="[^"]*")',
        r"<section\1",
        html,
    )
    html = re.sub(
        r"</div>(\s*<!--\s*end\s+section)",
        r"</section>\1",
        html,
    )

    # Strip Font Awesome kit/CDN script and link tags (AI adds placeholder kit URLs)
    html = re.sub(
        r"<script[^>]*(?:kit\.fontawesome\.com|fontawesome)[^>]*>.*?</script>\s*",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r"<link[^>]*(?:fontawesome|font-awesome)[^>]*/?\s*>\s*",
        "",
        html,
        flags=re.IGNORECASE,
    )

    # Strip X-Frame-Options meta tag (must be HTTP header, not meta)
    html = re.sub(
        r"<meta[^>]*X-Frame-Options[^>]*/?>\s*",
        "",
        html,
        flags=re.IGNORECASE,
    )

    # Ensure footer has dark background (LLM sometimes forgets)
    footer_match = re.search(r'<section([^>]*data-section-type="footer"[^>]*)>', html)
    if footer_match:
        attrs = footer_match.group(1)
        # Check if footer section tag itself already has a dark bg
        section_has_bg = (
            "background" in attrs
            or "bg-[#" in attrs
            or "bg-gray-9" in attrs
            or "bg-black" in attrs
            or "bg-slate-9" in attrs
        )
        # Also check if an inner div right after the section tag has a dark bg class
        inner_div_match = re.search(
            r'<section[^>]*data-section-type="footer"[^>]*>\s*<div([^>]*)>',
            html,
        )
        inner_has_bg = False
        if inner_div_match:
            inner_attrs = inner_div_match.group(1)
            inner_has_bg = bool(re.search(r'bg-(gray-[89]\d*|slate-[89]\d*|black|zinc-[89]\d*|\[#)', inner_attrs))

        if not section_has_bg and not inner_has_bg:
            # Add dark background inline style
            if 'style="' in attrs:
                html = html.replace(
                    footer_match.group(0),
                    footer_match.group(0).replace('style="', 'style="background:#1a1a2e;'),
                )
            else:
                html = html.replace(
                    footer_match.group(0),
                    f'<section{attrs} style="background:#1a1a2e">',
                )
            logger.info("🔧 Footer Fix → Added dark background to footer section")

    return html


def validate_css(css: str) -> str:
    """Validate CSS output meets minimum quality."""
    if not css or len(css) < 200:
        raise ValueError(f"CSS too short ({len(css)} chars) — generation likely failed")
    if len(css) > 80000:
        raise ValueError(f"CSS too large ({len(css)} chars)")
    return css


def _replace_template_literal(match):
    """Convert a JS template literal to string concatenation."""
    content = match.group(1)
    # Split on ${...} expressions
    parts = re.split(r"\$\{([^}]+)\}", content)
    if len(parts) == 1:
        # No interpolations, just a plain string
        return "'" + parts[0].replace("'", "\\'") + "'"
    # Build concatenation: 'text' + (expr) + 'text' + ...
    result_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # String literal part
            if part:
                result_parts.append("'" + part.replace("'", "\\'") + "'")
        else:
            # Expression part
            result_parts.append("(" + part + ")")
    return " + ".join(result_parts) if result_parts else "''"


def validate_js(js: str) -> str:
    """Validate JS output. JS can be empty for simple sites."""
    if not js:
        return ""
    # Strip any leftover markdown code fences
    js = re.sub(r"^```\w*\s*\n?", "", js.strip())
    js = re.sub(r"\n?```\s*$", "", js.strip())
    # NOTE: backtick replacement removed — JS is now injected via
    # doc.createElement('script') + appendChild, not embedded in a template literal,
    # so backticks in generated JS are safe and should be left as-is.
    if len(js) > 50000:
        raise ValueError(f"JS too large ({len(js)} chars)")

    # Fix querySelector('#') crash — bare '#' is invalid CSS selector.
    # Wrap any querySelector/querySelectorAll calls that use a variable href
    # by injecting a guard at the top of the script.
    if "querySelector" in js and "href" in js:
        guard = """// Guard: safe querySelector for anchor links (bare '#' is invalid)
function safeSelect(sel) { try { return sel && sel !== '#' && sel.length > 1 ? document.querySelector(sel) : null; } catch(e) { return null; } }
"""
        if "safeSelect" not in js:
            js = guard + js
            # Replace common patterns: document.querySelector(href) → safeSelect(href)
            # and document.querySelector(link.getAttribute('href')) → safeSelect(link.getAttribute('href'))
            js = re.sub(
                r"document\.querySelector\(([^)]*(?:href|hash|getAttribute\(['\"]href['\"]\))[^)]*)\)",
                r"safeSelect(\1)",
                js,
            )

    return js


# ═══════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return token_data


def format_conversation_history(session: dict, max_entries: int = 5) -> str:
    prompts = session.get("prompts", [])
    if not prompts:
        return "No previous messages."
    return "\n".join(f"Message {i + 1}: {e}" for i, e in enumerate(prompts[-max_entries:]))


# ═══════════════════════════════════════════════════════════════════════
# CLAUDE STREAMING HELPER
# ═══════════════════════════════════════════════════════════════════════


async def _claude_stream(client, model: str, max_tokens: int, system: str, user_msg: str, retries: int = 2, temperature: float = 0.3) -> str:
    """Call Claude with streaming, circuit breaker protection, and retry on failure."""

    @circuit_protected(provider="anthropic")
    async def _inner_call():
        collected = []
        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            async for text in stream.text_stream:
                collected.append(text)
        result = "".join(collected)
        if not result.strip():
            raise ValueError("Empty response from Claude")
        return result

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return await _inner_call()
        except CircuitOpenError:
            raise  # Don't retry if circuit is open
        except Exception as e:
            last_error = e
            if attempt < retries:
                logger.warning(f"[RETRY] Claude attempt {attempt} failed: {e}")
                await asyncio.sleep(1)
            else:
                logger.error(f"[RETRY] Claude exhausted after {retries} attempts: {e}")
    raise last_error


# ═══════════════════════════════════════════════════════════════════════
# STAGE 0: Prompt Enhancement (GPT-4.1-mini → enriched brief)
# ═══════════════════════════════════════════════════════════════════════


async def enhance_prompt(raw_prompt: str) -> str:
    """Expand a brief user prompt into a rich creative brief using GPT-4.1-mini.

    Fast (~2-3s) and cheap. Returns the enhanced prompt, or the original on failure.
    """
    logger.info(f'🟡 Prompt Received → "{raw_prompt[:120]}{"..." if len(raw_prompt) > 120 else ""}"')
    logger.info("🧠 Understanding Intent → Expanding brief user prompt into a rich creative brief")
    logger.info(f"🚀 Executing Step → Sending to GPT-4.1-mini for enhancement ({len(raw_prompt)} chars input)")
    t0 = time.time()
    client = get_openai_client()

    try:
        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.8,
            messages=[
                {"role": "system", "content": PROMPT_ENHANCE_SYSTEM},
                {"role": "user", "content": raw_prompt},
            ],
            max_tokens=800,
        )
        enhanced = response.choices[0].message.content.strip()
        duration = int((time.time() - t0) * 1000)
        log_stage("Enhance", duration, len(enhanced), True, f"{len(raw_prompt)} → {len(enhanced)} chars")
        logger.info(
            f"✅ Enhancement Complete → {len(raw_prompt)} chars expanded to {len(enhanced)} chars in {_fmt_duration(duration)}"
        )
        return enhanced
    except Exception as e:
        duration = int((time.time() - t0) * 1000)
        log_stage("Enhance", duration, 0, False, str(e))
        logger.info(f"❌ Enhancement Failed → {e} — using original prompt as fallback")
        return raw_prompt


# ═══════════════════════════════════════════════════════════════════════
# STAGE 1: Website Plan (GPT-4.1 → JSON)
# ═══════════════════════════════════════════════════════════════════════


async def stage_1_plan(prompt: str, session_id: str = "", niche_key: str = None, multipage: bool = False) -> dict:
    """Analyze prompt → structured website plan with content + layout patterns."""
    logger.info("🚀 Stage 1: PLAN → Analyzing prompt and generating website structure")
    logger.info(f"📦 Plan Input → prompt={len(prompt)} chars, niche={niche_key or 'auto-detect'}")
    t0 = time.time()
    client = get_openai_client()

    # Auto-detect niche if not provided
    if not niche_key:
        from app.utils.niches import detect_niche

        niche_key = detect_niche(prompt)
        if niche_key:
            logger.info(f'🧠 Niche Detected → "{niche_key}" — will use niche-specific design seeds and image queries')

    seed = get_design_seed(niche_key=niche_key)
    logger.info(f"🎨 Design Seed Selected → {seed[:100]}...")
    system = (
        build_plan_prompt(niche_key=niche_key, multipage=multipage)
        + f"\n\nDESIGN DIRECTION FOR THIS GENERATION:\n{seed}\n\nCRITICAL VARIETY RULES:\n- You MUST use the EXACT colors, hero pattern, and section patterns specified above.\n- Do NOT default to hero_split + card_grid + testimonial_cards — use the patterns listed in the seed.\n- Choose DIFFERENT data-aos animations per section (mix fade-up, fade-right, fade-left, zoom-in, flip-up).\n- Each website must feel visually distinct — different layout flow, different color mood, different section order."
    )
    logger.info(f"⚙️ Plan Prompt Built → {len(system):,} chars system prompt, sending to GPT-4.1...")
    if len(prompt.strip()) < 80:
        system += "\n\n" + PLAN_SHORT_PROMPT_ADDENDUM

    # Force pattern variety by randomly assigning patterns to key sections
    import random as _rnd
    _hero_variants = ["hero_split", "hero_center", "hero_full_image", "hero_asymmetric", "hero_video_bg", "hero_minimal"]
    _feature_variants = ["card_grid", "icon_grid", "feature_split", "feature_cards", "feature_stacked"]
    _testimonial_variants = ["testimonial_cards", "testimonial_slider", "testimonial_split"]
    _cta_variants = ["cta_banner", "cta_gradient", "cta_split", "cta_centered"]

    forced = {
        "hero": _rnd.choice(_hero_variants),
        "features": _rnd.choice(_feature_variants),
        "testimonials": _rnd.choice(_testimonial_variants),
        "cta": _rnd.choice(_cta_variants),
    }

    # Append seed hint + forced patterns to user prompt
    user_msg = prompt + f"\n\n[DESIGN HINT: {seed}]"
    user_msg += f"""

MANDATORY PATTERN ASSIGNMENT — use EXACTLY these patterns:
- Hero: {forced['hero']}
- Features/Services: {forced['features']}
- Testimonials: {forced['testimonials']}
- CTA: {forced['cta']}"""

    plan_max_tokens = 8000 if multipage else 4000

    @circuit_protected(provider="openai")
    async def _call_openai_plan():
        response = await client.chat.completions.create(
            model="gpt-4.1",
            temperature=1,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=plan_max_tokens,
        )
        return response.choices[0].message.content

    plan = {}
    raw = ""
    for attempt in range(1, 3):
        try:
            raw = await _call_openai_plan()
            plan = parse_json_response(raw)
            # Multi-page plans have "pages" instead of "sections"
            if plan.get("sections") or (plan.get("multipage") and plan.get("pages")):
                break
            raise ValueError("Plan has no sections or pages")
        except CircuitOpenError:
            raise
        except Exception as e:
            if attempt < 2:
                logger.warning(f"[RETRY] Plan attempt {attempt} failed: {e}")
                await asyncio.sleep(1)

    duration = int((time.time() - t0) * 1000)

    if plan.get("brand"):
        brand_info = plan["brand"]
        logger.info(
            f'📦 Plan Parsed → brand="{brand_info.get("name", "?")}", industry="{brand_info.get("industry", "?")}"'
        )
    if plan.get("multipage") and plan.get("pages"):
        page_slugs = [p.get("slug", "?") for p in plan["pages"]]
        total_sections = sum(len(p.get("sections", [])) for p in plan["pages"])
        logger.info(
            f"📦 Multi-Page Plan → {len(plan['pages'])} pages: {', '.join(page_slugs)}, {total_sections} total sections"
        )
        shared = plan.get("shared_sections", [])
        if shared:
            logger.info(f"📦 Shared Sections → {', '.join(s.get('type', '?') for s in shared)}")
    elif plan.get("sections"):
        section_summary = [f"{s.get('type', '?')}({s.get('pattern', '?')})" for s in plan["sections"]]
        logger.info(f"📦 Sections Planned → {len(plan['sections'])} sections: {', '.join(section_summary)}")
    if plan.get("design"):
        d = plan["design"]
        logger.info(
            f"🎨 Design Tokens → theme={d.get('theme')}, primary={d.get('primary_color')}, font={d.get('heading_font')}"
        )

    # Ensure minimum viable plan
    if not plan.get("brand"):
        plan["brand"] = {"name": "Website", "industry": "general", "tagline": ""}
    if not plan.get("design"):
        plan["design"] = {
            "theme": "light",
            "primary_color": "#6366f1",
            "secondary_color": "#8b5cf6",
            "accent_color": "#f59e0b",
            "background_color": "#ffffff",
            "surface_color": "#f8f9fa",
            "text_color": "#1a1a2e",
            "text_muted": "#6b7280",
            "heading_font": "Inter",
            "body_font": "Inter",
            "style": "modern",
            "card_radius": "12px",
            "button_radius": "50px",
            "shadow_style": "soft",
            "spacing": "normal",
        }
    # Ensure new design tokens have defaults
    design = plan["design"]
    design.setdefault("surface_color", "#f8f9fa")
    design.setdefault("text_muted", "#6b7280")
    design.setdefault("card_radius", "12px")
    design.setdefault("button_radius", "50px")
    design.setdefault("shadow_style", "soft")
    design.setdefault("spacing", "normal")
    if not plan.get("multipage"):
        if not plan.get("sections"):
            plan["sections"] = []
    else:
        # Ensure multipage structure
        if not plan.get("pages"):
            plan["pages"] = []
        if not plan.get("shared_sections"):
            plan["shared_sections"] = []

    # Validate and fix patterns for every section
    VALID_PATTERNS = set(COMPONENT_PATTERNS.keys()) | {"navbar"}
    TYPE_TO_PATTERN = {
        "navbar": "navbar",
        "hero": "hero_split",
        "features": "card_grid",
        "services": "card_grid",
        "stats": "stats_row",
        "testimonials": "testimonial_cards",
        "pricing": "pricing_table",
        "faq": "faq_accordion",
        "cta": "cta_banner",
        "team": "team_grid",
        "gallery": "gallery_grid",
        "about": "feature_split",
        "contact": "contact_split",
        "footer": "footer_columns",
    }
    # Patterns that are obviously wrong for a section type
    PATTERN_BLOCKLIST = {
        "services": {"faq_accordion", "pricing_table", "testimonial_cards", "stats_row"},
        "features": {"faq_accordion", "pricing_table", "testimonial_cards", "stats_row"},
        "pricing": {"faq_accordion", "card_grid", "icon_grid", "testimonial_cards"},
        "faq": {"card_grid", "icon_grid", "pricing_table", "testimonial_cards"},
        "testimonials": {"faq_accordion", "pricing_table", "card_grid", "icon_grid"},
        "stats": {"faq_accordion", "card_grid", "pricing_table"},
        "team": {"faq_accordion", "pricing_table", "icon_grid"},
        "contact": {"faq_accordion", "pricing_table", "card_grid"},
    }

    def _validate_section_patterns(sections_list):
        """Validate and fix patterns for a list of sections."""
        for section in sections_list:
            stype = section.get("type", "")
            pattern = section.get("pattern", "")
            blocked = PATTERN_BLOCKLIST.get(stype, set())
            if pattern not in VALID_PATTERNS or pattern in blocked:
                old = pattern
                section["pattern"] = TYPE_TO_PATTERN.get(stype, "card_grid")
                logger.info(f"[PLAN] fixed invalid pattern: {old} → {section['pattern']} (section: {stype})")

    def _fix_visual_rhythm(sections_list):
        """No more than 2 consecutive grid patterns."""
        GRID_PATTERNS = {
            "card_grid",
            "icon_grid",
            "testimonial_cards",
            "testimonial_slider",
            "team_grid",
            "team_cards",
            "team_masonry",
            "gallery_grid",
            "feature_cards",
            "service_modal",
            "comparison_table",
        }
        WIDE_ALTERNATIVES = [
            "feature_split",
            "feature_stacked",
            "feature_steps",
            "stats_row",
            "logo_cloud",
            "testimonial_split",
            "cta_split",
            "cta_centered",
        ]
        consecutive_grids = 0
        for i in range(len(sections_list)):
            if sections_list[i].get("type") in ("navbar", "footer"):
                consecutive_grids = 0
                continue
            curr_p = sections_list[i].get("pattern", "")
            if curr_p in GRID_PATTERNS:
                consecutive_grids += 1
                if consecutive_grids > 2:
                    old_pattern = curr_p
                    new_pattern = "feature_split"
                    used_patterns = {
                        sections_list[j].get("pattern", "")
                        for j in range(max(0, i - 2), min(len(sections_list), i + 2))
                    }
                    for alt in WIDE_ALTERNATIVES:
                        if alt not in used_patterns:
                            new_pattern = alt
                            break
                    sections_list[i]["pattern"] = new_pattern
                    consecutive_grids = 0
                    logger.info(f"[PLAN] rhythm fix: {old_pattern} → {new_pattern}")
            else:
                consecutive_grids = 0

    def _dedup_sections(sections_list):
        """Deduplicate sections — each type should appear only once."""
        seen_types = set()
        unique = []
        for section in sections_list:
            stype = section.get("type", "")
            if stype not in seen_types:
                seen_types.add(stype)
                unique.append(section)
            else:
                logger.info(f"[PLAN] removed duplicate section: {stype}")
        return unique

    if plan.get("multipage"):
        # Validate shared sections
        _validate_section_patterns(plan.get("shared_sections", []))
        # Validate each page's sections
        for page in plan.get("pages", []):
            page_sections = page.get("sections", [])
            _validate_section_patterns(page_sections)
            _fix_visual_rhythm(page_sections)
            page["sections"] = _dedup_sections(page_sections)
            # Clamp per-page section count
            if len(page["sections"]) > 8:
                logger.info(f"[PLAN] trimmed page '{page.get('slug', '?')}' sections: {len(page['sections'])} → 8")
                page["sections"] = page["sections"][:8]
        # Clamp page count to 8
        if len(plan["pages"]) > 8:
            logger.info(f"[PLAN] trimmed pages: {len(plan['pages'])} → 8")
            plan["pages"] = plan["pages"][:8]

        # ── Plan validation for multipage (hero images, item counts, content fields) ──
        logger.info("⚙️ Running Plan Validator (multipage) → checking hero images, item counts, content fields...")
        plan, validation_fixes = validate_and_fix_plan(plan)
        for fix in validation_fixes:
            logger.info(f"  🔧 {fix}")
        if validation_fixes:
            logger.info(f"✅ Plan Validator Complete → {len(validation_fixes)} auto-fixes applied")
        else:
            logger.info("✅ Plan Validator Complete → no fixes needed")
    else:
        _validate_section_patterns(plan.get("sections", []))
        _fix_visual_rhythm(plan.get("sections", []))

        # ── Plan validation + auto-fix (item counts, content fields, dedup) ──
        logger.info("⚙️ Running Plan Validator → checking item counts, content fields, image dedup...")
        plan, validation_fixes = validate_and_fix_plan(plan)
        for fix in validation_fixes:
            logger.info(f"  🔧 {fix}")
        if validation_fixes:
            logger.info(f"✅ Plan Validator Complete → {len(validation_fixes)} auto-fixes applied")
        else:
            logger.info("✅ Plan Validator Complete → no fixes needed, plan is clean")

        plan["sections"] = _dedup_sections(plan.get("sections", []))

        # Clamp section count: min 5, max 12
        if len(plan["sections"]) > 12:
            logger.info(f"[PLAN] trimmed sections: {len(plan['sections'])} → 12")
            plan["sections"] = plan["sections"][:12]
        if len(plan["sections"]) < 5:
            logger.warning(f"[PLAN] low section count: only {len(plan['sections'])} sections")

    # Enforce pattern rotation — swap overused patterns with fresh alternatives
    plan = enforce_pattern_rotation(plan)

    # Record patterns for rotation memory
    record_used_patterns(plan)

    if plan.get("multipage"):
        n_sections = sum(len(p.get("sections", [])) for p in plan.get("pages", []))
        n_pages = len(plan.get("pages", []))
        brand = plan.get("brand", {}).get("name", "")
        log_stage(
            "Plan",
            duration,
            len(raw),
            bool(plan.get("pages")),
            f"{brand}, {n_pages} pages, {n_sections} total sections",
        )
    else:
        n_sections = len(plan["sections"])
        brand = plan.get("brand", {}).get("name", "")
        log_stage("Plan", duration, len(raw), bool(plan.get("sections")), f"{brand}, {n_sections} sections")

    if plan.get("multipage"):
        logger.info(
            f'✅ Stage 1 Complete → "{brand}" with {n_pages} pages, {n_sections} total sections in {_fmt_duration(duration)}'
        )
    else:
        logger.info(f'✅ Stage 1 Complete → "{brand}" with {n_sections} sections in {_fmt_duration(duration)}')

    save_debug(session_id, "plan", json.dumps(plan, indent=2))
    return plan


# ═══════════════════════════════════════════════════════════════════════
# STAGE 2: HTML Generation (Claude → HTML only)
# ═══════════════════════════════════════════════════════════════════════


async def stage_2_html(plan: dict, session_id: str = "", niche_key: str = None, reference_html: str = None, enhanced_brief: str = None) -> str:
    """Generate semantic HTML from the website plan using component patterns."""
    logger.info("🚀 Stage 2: HTML → Generating page structure with pure CSS")
    t0 = time.time()
    client = get_anthropic_client()

    # Build modular prompt with only the needed pattern templates
    system = build_html_prompt(plan, enhanced_brief=enhanced_brief)
    logger.info(f"⚙️ HTML Prompt Built → {len(system):,} chars (only patterns needed for this plan loaded)")

    # If a reference template is provided, extract just the CSS design system as inspiration
    if reference_html:
        import re as _re
        # Extract only the :root CSS variables block — the useful design system part
        root_match = _re.search(r':root\s*\{[^}]+\}', reference_html)
        if root_match:
            ref_css_vars = root_match.group(0)
            system += f"""

REFERENCE DESIGN SYSTEM (use as quality inspiration — adapt colors/spacing to the plan above):
{ref_css_vars}
Study this reference's design quality: variable naming, spacing values, shadow depths, and transitions. Apply similar polish to the generated HTML.
"""

    text = await _claude_stream(
        client,
        "claude-sonnet-4-20250514",
        16000,
        system,
        "Generate the HTML markup for this website using the specified layout patterns. Return only the html code block.",
    )

    html = parse_single_code_block(text, "html")
    html = validate_html(html)

    html_duration = int((time.time() - t0) * 1000)
    n_sections = html.count("data-section-type")
    log_stage("HTML", html_duration, len(html), True, f"{n_sections} sections")
    logger.info(f"✅ HTML Generated → {len(html):,} chars with {n_sections} sections in {_fmt_duration(html_duration)}")

    # Resolve {{IMG:query}} placeholders to real image URLs (niche-aware, with safety fallback)
    img_count = html.count("{{IMG:")
    logger.info(
        f"🖼️ Resolving Images → {img_count} {{IMG:}} placeholders found, fetching from Unsplash/Pexels (niche={niche_key or 'general'})"
    )
    html = await _resolve_images_safe(html, niche_key=niche_key)
    logger.info("✅ Images Resolved → all placeholders replaced with real URLs")

    save_debug(session_id, "html", html)
    return html


async def stage_2_html_from_template(
    template_html: str, plan: dict, session_id: str = "", niche_key: str = None
) -> str:
    """Generate HTML by customizing an existing template — faster and higher quality.

    Instead of generating from scratch with a 72K prompt, this sends the working
    template HTML (~30K) with a short customization prompt (~5K). Claude modifies
    the proven structure rather than building from zero.
    """
    from app.utils.prompt_pipeline import build_template_customize_prompt

    logger.info("🚀 Stage 2: HTML → Template-first customization (faster path)")
    t0 = time.time()
    client = get_anthropic_client()

    system = build_template_customize_prompt(template_html, plan)
    logger.info(f"⚙️ Template Customize Prompt → {len(system):,} chars (vs ~72K for from-scratch)")

    text = await _claude_stream(
        client,
        "claude-sonnet-4-20250514",
        16000,
        system,
        "Customize this template for the business described in the plan. Return the complete HTML.",
    )

    html = parse_single_code_block(text, "html")
    html = validate_html(html)

    # Ensure data-section-type attributes exist (post-process if Claude missed some)
    html = _ensure_section_types(html)

    html_duration = int((time.time() - t0) * 1000)
    n_sections = html.count("data-section-type")
    log_stage("HTML-TEMPLATE", html_duration, len(html), True, f"{n_sections} sections (template-customized)")
    logger.info(f"✅ HTML Generated (template path) → {len(html):,} chars with {n_sections} sections in {_fmt_duration(html_duration)}")

    # Resolve {{IMG:query}} placeholders to real image URLs (niche-aware)
    img_count = html.count("{{IMG:")
    # Also handle any REPLACE_ME markers that Claude didn't convert
    replace_me_count = html.count('src="REPLACE_ME"')
    if replace_me_count > 0:
        logger.warning(f"⚠️ {replace_me_count} REPLACE_ME markers not converted — removing")
        html = html.replace('src="REPLACE_ME"', 'src="{{IMG:feature placeholder}}"')
        img_count = html.count("{{IMG:")

    logger.info(f"🖼️ Resolving Images → {img_count} {{IMG:}} placeholders found")
    html = await _resolve_images_safe(html, niche_key=niche_key)
    logger.info("✅ Images Resolved → all placeholders replaced with real URLs")

    save_debug(session_id, "html", html)
    return html


def _ensure_section_types(html: str) -> str:
    """Post-process: add data-section-type to <section> tags that lack it."""
    import re

    def _add_section_type(match):
        tag = match.group(0)
        if "data-section-type" in tag:
            return tag  # Already has it

        # Try to infer type from class or id
        id_match = re.search(r'id="[^"]*?-?(\w+)"', tag)
        class_match = re.search(r'class="[^"]*?-(\w+)', tag)

        section_type = "content"
        if id_match:
            name = id_match.group(1).lower()
            for t in ["hero", "about", "menu", "features", "services", "testimonials",
                       "team", "gallery", "contact", "cta", "faq", "stats", "pricing",
                       "footer", "reservation", "special", "portfolio", "blog"]:
                if t in name:
                    section_type = t
                    break
        elif class_match:
            name = class_match.group(1).lower()
            for t in ["hero", "about", "menu", "features", "services", "testimonials",
                       "team", "gallery", "contact", "cta", "faq", "stats", "pricing",
                       "footer", "reservation", "special", "portfolio", "blog"]:
                if t in name:
                    section_type = t
                    break

        return tag.rstrip(">") + f' data-section-type="{section_type}">'

    return re.sub(r"<section[^>]*>", _add_section_type, html)


def extract_style_block(html: str) -> tuple[str, str]:
    """Extract <style> block from HTML, return (css, html_without_style).

    The HTML stage now outputs a <style> block + body content.
    We extract the <style> contents into the css field so the frontend
    can inject it into <head> as before.
    """
    import re

    match = re.search(r"<style[^>]*>(.*?)</style>", html, re.DOTALL)
    if match:
        css = match.group(1).strip()
        html_clean = html[: match.start()] + html[match.end() :]
        html_clean = html_clean.strip()
        return css, html_clean
    return "", html


# ═══════════════════════════════════════════════════════════════════════
# STAGE 3: JS Generation (Claude → JS only)
# ═══════════════════════════════════════════════════════════════════════


async def stage_3_js(html: str, session_id: str = "") -> str:
    """Generate vanilla JavaScript interactions."""
    logger.info("🚀 Stage 3: JS → Generating vanilla JavaScript interactions")
    t0 = time.time()
    client = get_anthropic_client()

    section_types = extract_section_types(html)
    logger.info(f"📦 JS Context → sections on page: {section_types}")
    system = JS_GEN_SYSTEM_PROMPT.format(
        html_summary=summarize_html(html),
        section_types=section_types,
    )
    logger.info(f"⚙️ JS Prompt Built → {len(system):,} chars, sending to Claude Sonnet...")

    text = await _claude_stream(
        client,
        "claude-sonnet-4-20250514",
        4000,
        system,
        "Generate the JavaScript for this website. Return only the js code block.",
    )

    js = parse_single_code_block(text, "js")
    duration = int((time.time() - t0) * 1000)

    js = validate_js(js)
    log_stage("JS", duration, len(js), True, f"sections: {section_types[:60]}")
    logger.info(f"✅ Stage 3 Complete → {len(js):,} chars of JS in {_fmt_duration(duration)}")

    save_debug(session_id, "js", js)
    return js


# ═══════════════════════════════════════════════════════════════════════
# MULTI-PAGE HTML GENERATION
# ═══════════════════════════════════════════════════════════════════════


async def generate_multipage_html(
    plan: dict, session_id: str, niche_key: str = None, reference_html: str = None
) -> dict:
    """Generate HTML for each page in a multi-page plan. Returns {slug: html_string}."""
    pages = plan.get("pages", [])
    shared_sections = plan.get("shared_sections", [])

    if not pages:
        raise ValueError("No pages found in multi-page plan")

    logger.info(f"[MULTIPAGE] Generating {len(pages)} pages in parallel...")

    async def generate_one_page(page: dict) -> tuple:
        slug = page.get("slug", "index")
        title = page.get("title", slug)
        logger.info(f"[MULTIPAGE] Starting page '{title}' (slug: {slug})")
        t0 = time.time()

        prompt = build_page_html_prompt(plan, page, shared_sections)

        # If a reference template is provided, extract just CSS design system
        if reference_html:
            import re as _re
            root_match = _re.search(r':root\s*\{[^}]+\}', reference_html)
            if root_match:
                prompt += f"""

REFERENCE DESIGN SYSTEM (quality inspiration):
{root_match.group(0)}
Apply similar polish, spacing, and shadow quality to this page.
"""

        client = get_anthropic_client()
        text = await _claude_stream(
            client,
            "claude-sonnet-4-20250514",
            16000,
            prompt,
            f"Generate the {title} page HTML. Follow ALL pattern templates exactly.",
        )

        html = parse_single_code_block(text, "html")
        html = validate_html(html)

        # Resolve image placeholders (with hallucination safety + comment stripping)
        html = await _resolve_images_safe(html, niche_key=niche_key)

        duration = int((time.time() - t0) * 1000)
        logger.info(f"[MULTIPAGE] Page '{title}' done → {len(html):,} chars in {_fmt_duration(duration)}")
        save_debug(session_id, f"html_{slug}", html)
        return slug, html

    # Generate all pages in parallel
    tasks = [generate_one_page(page) for page in pages]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    pages_html = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"[MULTIPAGE] Page generation failed: {result}")
            continue
        slug, html = result
        pages_html[slug] = html

    if not pages_html:
        raise ValueError("All page generations failed")

    logger.info(f"[MULTIPAGE] Complete → {len(pages_html)}/{len(pages)} pages generated successfully")
    return pages_html


# ═══════════════════════════════════════════════════════════════════════
# COMPONENT-BASED EDITING
# ═══════════════════════════════════════════════════════════════════════


async def route_edit_to_components(prompt: str, session: dict) -> list[str]:
    """Use GPT-4.1-mini to detect which section(s) the user wants to edit.
    Returns list of section IDs, or ['__style__'], ['__append__:type'], or ['__full__'].
    """
    logger.info(f'🟡 Edit Request Received → "{prompt[:100]}{"..." if len(prompt) > 100 else ""}"')
    logger.info("🧠 Understanding Intent → Routing edit request to the correct section(s)")
    t0 = time.time()
    html = session["html"]
    sections = parse_sections(html)

    # Build a concise section list for the router
    sections_desc = []
    for s in sections:
        label = s.get("label", s["type"])
        sections_desc.append(f'  - id="{s["id"]}" type="{s["type"]}" label="{label}"')
    sections_list = "\n".join(sections_desc)
    logger.info(f"📦 Available Sections → {len(sections)} sections on page: {', '.join(s['type'] for s in sections)}")

    # Build conversation context for follow-up detection
    conv_parts = []
    prompts = session.get("prompts", [])
    if prompts:
        recent = prompts[-5:]  # last 5 messages
        conv_parts.append("RECENT CONVERSATION (oldest → newest):")
        for i, p in enumerate(recent, 1):
            conv_parts.append(f"  {i}. {p}")
    last_edited = session.get("last_edited_targets", [])
    if last_edited:
        conv_parts.append(f"LAST EDITED: {last_edited}")
    conversation_context = "\n".join(conv_parts) if conv_parts else ""
    if prompts or last_edited:
        logger.info(f"💬 Router Context → {len(prompts)} previous messages, last edited: {last_edited or 'none'}")

    system = COMPONENT_ROUTER_PROMPT.format(
        sections_list=sections_list,
        prompt=prompt,
        conversation_context=conversation_context,
    )

    logger.info("🚀 Executing Step → Sending to GPT-4.1-mini for intent classification...")
    client = get_openai_client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        raw = response.choices[0].message.content.strip()
        logger.info(f"📦 Router Raw Response → {raw}")
        # Parse JSON array from response
        result = json.loads(raw)
        if isinstance(result, list) and len(result) > 0:
            duration = int((time.time() - t0) * 1000)
            # Explain the decision
            if "__full__" in result:
                logger.info("⚙️ Decision Made → FULL PAGE REWRITE — request requires structural changes")
            elif any(t.startswith("__append__:") for t in result):
                atype = [t.split(":")[1] for t in result if t.startswith("__append__:")][0]
                logger.info(f'⚙️ Decision Made → APPEND NEW SECTION — adding "{atype}" section to existing page')
            elif "__style__" in result:
                logger.info("⚙️ Decision Made → STYLE EDIT — changing global CSS variables/colors/fonts")
            else:
                logger.info(f"⚙️ Decision Made → SECTION EDIT — targeting {result} for modification")
            logger.info(f"✅ Router Complete → targets={result} in {_fmt_duration(duration)}")
            return result
    except Exception as e:
        logger.warning(f"❌ Router Failed → {e} — falling back to full page edit")

    return ["__full__"]


def extract_css_vars(css: str) -> str:
    """Extract just the :root CSS variables block for context."""
    match = re.search(r":root\s*\{([^}]+)\}", css)
    if match:
        return ":root {" + match.group(1) + "}"
    return ""


async def edit_single_component(section_html: str, section_type: str, css_vars: str, prompt: str) -> str:
    """Edit a single section using Claude. Returns updated section HTML."""
    logger.info(f'🔧 Editing Section → type="{section_type}" ({len(section_html):,} chars)')
    logger.info(f'📝 Edit Request → "{prompt[:80]}{"..." if len(prompt) > 80 else ""}"')
    t0 = time.time()
    client = get_anthropic_client()

    system = COMPONENT_EDIT_PROMPT.format(
        css_vars=css_vars,
        section_type=section_type,
        section_html=section_html,
        prompt=prompt,
    )
    logger.info(f"⚙️ Edit Prompt Built → {len(system):,} chars (section HTML + CSS vars + rules), sending to Claude...")

    text = await _claude_stream(
        client,
        "claude-sonnet-4-20250514",
        8000,
        system,
        f"Edit this section: {prompt}",
    )

    updated = parse_single_code_block(text, "html")
    duration = int((time.time() - t0) * 1000)

    if not updated or len(updated) < 20:
        logger.error(
            f"❌ Edit Failed → {section_type} section in {_fmt_duration(duration)} — returning original unchanged"
        )
        return section_html  # Return original on failure

    logger.info(
        f"✅ Edit Complete → {section_type} section in {_fmt_duration(duration)} ({len(section_html):,} → {len(updated):,} chars)"
    )
    return updated


async def edit_style_block(css: str, section_types: str, prompt: str) -> str:
    """Edit the CSS style block for global style changes."""
    t0 = time.time()
    client = get_anthropic_client()

    system = STYLE_EDIT_PROMPT.format(
        css=css,
        section_types=section_types,
        prompt=prompt,
    )

    text = await _claude_stream(
        client,
        "claude-sonnet-4-20250514",
        12000,
        system,
        f"Update the styles: {prompt}",
    )

    updated = parse_single_code_block(text, "css")
    duration = int((time.time() - t0) * 1000)

    if not updated or len(updated) < 50:
        logger.error(f"[EDIT] style block FAILED in {_fmt_duration(duration)}")
        return css
    logger.info(f"[EDIT] style block done in {_fmt_duration(duration)} ({len(css):,} → {len(updated):,} chars)")
    return updated


async def iterate_website(prompt: str, session: dict) -> dict[str, str]:
    """Component-based edit: route → edit targeted section(s) → reassemble.
    Used by the sync endpoint. SSE endpoint calls _execute_component_edit directly.
    """
    targets = await route_edit_to_components(prompt, session)
    return await _execute_component_edit(prompt, session, targets)


async def _execute_component_edit(prompt: str, session: dict, targets: list[str]) -> dict[str, str]:
    """Execute component edit with pre-routed targets (avoids double routing)."""
    # Store targets so session save can persist them for follow-up routing
    session["last_edited_targets"] = targets
    html = session["html"]
    css = session["css"]
    js = session.get("js", "")

    if "__full__" in targets:
        logger.info("🚀 Executing Step → Full page rewrite (all sections regenerated)")
        return await _iterate_full_page(prompt, session)

    # Handle __append__:section_type
    append_targets = [t for t in targets if t.startswith("__append__:")]
    if append_targets:
        section_type = append_targets[0].split(":", 1)[1]
        logger.info(f'🚀 Executing Step → Appending new "{section_type}" section (existing content preserved)')
        return await _append_section(prompt, session, section_type)

    if "__style__" in targets:
        logger.info("🚀 Executing Step → Editing global styles (CSS variables, colors, fonts)")
        section_types = extract_section_types(html)
        updated_css = await edit_style_block(css, section_types, prompt)
        logger.info(f"✅ Style Edit Complete → CSS {len(css):,} → {len(updated_css):,} chars")
        return {"html": html, "css": updated_css, "js": js}

    # Edit targeted sections
    sections = parse_sections(html)
    section_map = {s["id"]: s for s in sections}
    css_vars = extract_css_vars(css)

    edit_tasks = []
    for target_id in targets:
        if target_id in section_map:
            s = section_map[target_id]
            section_html = html[s["start"] : s["end"]]
            edit_tasks.append((target_id, s["type"], section_html))
            logger.info(f'📦 Section Loaded → id="{target_id}" type="{s["type"]}" ({len(section_html):,} chars)')

    if not edit_tasks:
        logger.info(f"⚠️ No matching sections found for targets={targets} — falling back to full page rewrite")
        return await _iterate_full_page(prompt, session)

    # Run edits
    logger.info(
        f"🚀 Executing Step → Editing {len(edit_tasks)} section(s) via Claude Sonnet{'  (parallel)' if len(edit_tasks) > 1 else ''}"
    )
    updated_sections = {}
    if len(edit_tasks) == 1:
        tid, stype, shtml = edit_tasks[0]
        updated_sections[tid] = await edit_single_component(shtml, stype, css_vars, prompt)
    else:
        results = await asyncio.gather(
            *[edit_single_component(shtml, stype, css_vars, prompt) for tid, stype, shtml in edit_tasks]
        )
        for (tid, _, _), result in zip(edit_tasks, results, strict=False):
            updated_sections[tid] = result

    # Reassemble
    updated_html = html
    for target_id, new_section_html in updated_sections.items():
        updated_html = replace_section_html(updated_html, target_id, new_section_html)
        logger.info(f'✅ Section Replaced → id="{target_id}" patched into full HTML')

    # Resolve any {{IMG:}} placeholders Claude may have added (with hallucination safety)
    if "{{IMG:" in updated_html or re.search(r'src=["\']https?://images\.(pexels|unsplash)\.com/', updated_html):
        plan = session.get("plan", {})
        niche_key = plan.get("brand", {}).get("industry", "general") if plan else "general"
        updated_html = await _resolve_images_safe(updated_html, niche_key=niche_key)

    return {"html": updated_html, "css": css, "js": js}


def _build_nav_links(pages_dict: dict, current_slug: str) -> tuple[str, str]:
    """Build nav link HTML for both <ul><li> and <div><a> navbar formats.

    Returns (li_links, a_links) where:
      - li_links: <li><a href="...">Title</a></li> for each page
      - a_links: <a href="...">Title</a> for each page
    """
    li_parts = []
    a_parts = []
    for slug in pages_dict:
        if slug == "index":
            href = "/"
            title = "Home"
        else:
            href = f"/{slug}.html"
            # Derive title from slug: "about-us" → "About Us"
            title = slug.replace("-", " ").replace("_", " ").title()
        li_parts.append(f'<li><a href="{href}">{title}</a></li>')
        a_parts.append(f'<a href="{href}">{title}</a>')
    return "\n      ".join(li_parts), "\n      ".join(a_parts)


def _sync_page_navbar(html: str, pages_dict: dict, current_slug: str) -> str:
    """Replace the nav links in a page's navbar with inter-page navigation links.

    Handles both formats that Claude generates:
      Format A: <ul class="nav-links"><li><a>...</a></li>...</ul>
      Format B: <div class="nav-links"><a>...</a>...</div>

    Preserves CTA buttons (mobile-cta <li> and nav-cta <a>).
    """
    li_links, a_links = _build_nav_links(pages_dict, current_slug)

    # --- Format A: <ul class="nav-links"> with <li> children ---
    ul_pattern = re.compile(
        r'(<ul\s+class="nav-links"[^>]*>)'   # opening <ul>
        r'(.*?)'                               # content (li items)
        r'(</ul>)',                             # closing </ul>
        re.IGNORECASE | re.DOTALL,
    )
    ul_match = ul_pattern.search(html)
    if ul_match:
        old_content = ul_match.group(2)
        # Extract CTA items to preserve (mobile-cta <li>)
        cta_items = re.findall(
            r'<li\s+class="mobile-cta"[^>]*>.*?</li>',
            old_content,
            re.IGNORECASE | re.DOTALL,
        )
        cta_html = "\n      ".join(cta_items)
        # Build new content: page links + preserved CTA
        new_content = f"\n      {li_links}"
        if cta_html:
            new_content += f"\n      {cta_html}"
        new_content += "\n    "
        html = html[:ul_match.start(2)] + new_content + html[ul_match.end(2):]
        return html

    # --- Format B: <div class="nav-links"> with direct <a> children ---
    div_pattern = re.compile(
        r'(<div\s+class="nav-links"[^>]*>)'   # opening <div>
        r'(.*?)'                                # content (a tags)
        r'(</div>)',                            # closing </div>
        re.IGNORECASE | re.DOTALL,
    )
    div_match = div_pattern.search(html)
    if div_match:
        old_content = div_match.group(2)
        # Extract CTA links to preserve (btn-primary class)
        cta_links = re.findall(
            r'<a\s[^>]*class="[^"]*btn-primary[^"]*"[^>]*>.*?</a>',
            old_content,
            re.IGNORECASE | re.DOTALL,
        )
        cta_html = "\n      ".join(cta_links)
        # Build new content: page links + preserved CTA
        new_content = f"\n      {a_links}"
        if cta_html:
            new_content += f"\n      {cta_html}"
        new_content += "\n    "
        html = html[:div_match.start(2)] + new_content + html[div_match.end(2):]
        return html

    logger.warning(f"[NAV SYNC] Could not find nav-links in page '{current_slug}'")
    return html


def _sync_footer_quick_links(html: str, pages_dict: dict) -> str:
    """Update the 'Quick Links' column in the footer with inter-page navigation.

    Identifies the Quick Links block by its heading text (Quick Links, Navigation,
    Pages, Explore, etc.) and replaces its anchor links with page links.
    Only modifies the first matching footer-links block. Leaves other footer
    columns (Products, Services, Contact) untouched.
    """
    li_links, a_links = _build_nav_links(pages_dict, "")

    # Find the footer element
    footer_match = re.search(r'<footer[\s>]', html, re.IGNORECASE)
    if not footer_match:
        return html
    footer_start = footer_match.start()

    # Look for a heading followed by a footer-links block inside the footer
    # Match headings like "Quick Links", "Navigation", "Pages", "Explore", "Menu", "Sitemap"
    quick_link_headings = re.compile(
        r'<h[3-6][^>]*class="footer-heading"[^>]*>\s*'
        r'(Quick\s*Links?|Navigation|Pages|Explore|Site\s*Map|Menu|Links)\s*'
        r'</h[3-6]>',
        re.IGNORECASE,
    )
    heading_match = quick_link_headings.search(html, footer_start)
    if not heading_match:
        return html

    # Find the footer-links block immediately after this heading
    search_start = heading_match.end()

    # Format A: <ul class="footer-links">
    ul_pattern = re.compile(
        r'(<ul\s+class="footer-links"[^>]*>)(.*?)(</ul>)',
        re.IGNORECASE | re.DOTALL,
    )
    ul_match = ul_pattern.search(html, search_start)
    # Only match if it's close to the heading (within 200 chars — same column)
    if ul_match and ul_match.start() - search_start < 200:
        new_content = f"\n          {li_links}\n        "
        return html[:ul_match.start(2)] + new_content + html[ul_match.end(2):]

    # Format B: <div class="footer-links">
    div_pattern = re.compile(
        r'(<div\s+class="footer-links"[^>]*>)(.*?)(</div>)',
        re.IGNORECASE | re.DOTALL,
    )
    div_match = div_pattern.search(html, search_start)
    if div_match and div_match.start() - search_start < 200:
        new_content = f"\n          {a_links}\n        "
        return html[:div_match.start(2)] + new_content + html[div_match.end(2):]

    return html


def _update_all_page_navbars(pages_dict: dict, new_slug: str, new_title: str) -> dict:
    """Sync navbars AND footer quick links in ALL pages for inter-page navigation.

    Replaces anchor-only navbars with inter-page links. Preserves CTA buttons.
    Updates footer Quick Links column with page links.
    Returns the updated pages_dict.
    """
    for slug, page_data in pages_dict.items():
        page_html = page_data.get("html", "")
        if not page_html:
            continue
        updated = _sync_page_navbar(page_html, pages_dict, slug)
        updated = _sync_footer_quick_links(updated, pages_dict)
        if updated != page_html:
            pages_dict[slug] = {**page_data, "html": updated}
            logger.info(f'[NAV SYNC] Updated navbar + footer in "{slug}" page with {len(pages_dict)} page links')
    return pages_dict


async def _add_new_page(prompt: str, session: dict, page_slug: str, page_title: str) -> dict[str, str]:
    """Generate a brand-new page using the existing homepage as a design reference.

    Returns the NEW page's code dict.  The caller is responsible for
    storing it in ``session["pages"]`` and flipping the multipage flag.
    The existing homepage HTML is **never modified**.
    """
    logger.info(f'📄 Add Page → slug="{page_slug}" title="{page_title}"')

    ref_html = session["html"]
    ref_css = session["css"]
    js = session.get("js", "")

    # Extract image URLs from the homepage so the LLM can reuse them
    img_urls = list(
        set(
            re.findall(
                r'(?:src|background-image:\s*url\([\'"]?)([^\'"\)]+\.(?:jpg|jpeg|png|webp|gif|svg))',
                ref_html,
                re.IGNORECASE,
            )
        )
    )
    img_list = (
        "\n".join(f"- {u}" for u in img_urls[:20])
        if img_urls
        else "No existing images found — use relevant Unsplash/Pexels URLs."
    )

    system_prompt = ADD_PAGE_HTML_PROMPT.format(
        reference_html=ref_html[:12000],  # Trim to avoid token overflow
        reference_css=ref_css[:4000],
        page_title=page_title,
        page_slug=page_slug,
        prompt=prompt,
        image_urls=img_list,
    )

    client = get_anthropic_client()
    text = await _claude_stream(
        client,
        "claude-sonnet-4-20250514",
        8000,
        system_prompt,
        f"Generate the {page_title} page HTML. Return only the html code block.",
    )

    page_html = parse_single_code_block(text, "html")
    if not page_html:
        logger.error("[ADD PAGE] Claude returned empty HTML")
        return {"html": "", "css": ref_css, "js": js}

    # Separate CSS and HTML
    page_css, page_html_clean = extract_style_block(page_html)
    # Merge: reference CSS + any new page-specific CSS
    merged_css = ref_css
    if page_css:
        merged_css = ref_css + f"\n\n/* === {page_title} Page Styles === */\n" + page_css

    # Inject section IDs
    page_html_clean = inject_section_ids(page_html_clean)

    logger.info(
        f'✅ Add Page Complete → slug="{page_slug}" HTML={len(page_html_clean):,} CSS={len(merged_css):,} chars'
    )
    return {"html": page_html_clean, "css": merged_css, "js": js}


async def _append_section(prompt: str, session: dict, section_type: str) -> dict[str, str]:
    """Generate a new section and insert it into the existing HTML."""
    logger.info(f'🧩 Append Section → Generating new "{section_type}" section')
    html = session["html"]
    css = session["css"]
    js = session.get("js", "")
    plan = session.get("plan", {})

    # Build context
    css_vars = extract_css_vars(css)
    sections = parse_sections(html)
    existing_sections = ", ".join(s["type"] for s in sections)
    logger.info(f"📦 Existing Page → {len(sections)} sections: {existing_sections}")

    # Get brand context from plan
    brand = plan.get("brand", {})
    brand_context = f"Company: {brand.get('name', 'Business')}. Industry: {brand.get('industry', 'general')}."
    if brand.get("tagline"):
        brand_context += f" Tagline: {brand['tagline']}."
    logger.info(f"🏢 Brand Context → {brand_context}")

    # Map section_type to a default pattern
    _TYPE_TO_PATTERN = {
        "footer": "footer_columns",
        "features": "card_grid",
        "services": "service_modal",
        "stats": "stats_row",
        "testimonials": "testimonial_cards",
        "pricing": "pricing_table",
        "faq": "faq_accordion",
        "cta": "cta_banner",
        "team": "team_grid",
        "gallery": "gallery_grid",
        "about": "feature_split",
        "contact": "contact_split",
        "timeline": "timeline",
        "newsletter": "newsletter_cta",
        "hero": "hero_center",
    }

    pattern_name = _TYPE_TO_PATTERN.get(section_type, "card_grid")
    pattern_template = (
        get_pattern_template(pattern_name) or "Standard section with heading, subheading, and content items."
    )
    logger.info(f'⚙️ Pattern Selected → "{pattern_name}" template ({len(pattern_template)} chars)')

    prompt_text = APPEND_SECTION_PROMPT.format(
        css_vars=css_vars,
        existing_sections=existing_sections,
        brand_context=brand_context,
        section_type=section_type,
        pattern_template=pattern_template,
        prompt=prompt,
    )
    logger.info(
        f"🚀 Executing Step → Sending to Claude Sonnet to generate {section_type} section ({len(prompt_text):,} chars prompt)"
    )

    client = get_anthropic_client()
    t0 = time.time()

    try:
        raw = await _claude_stream(
            client,
            "claude-sonnet-4-20250514",
            4000,
            "",
            prompt_text,
        )
        new_section_html = parse_single_code_block(raw, "html")
        if not new_section_html:
            new_section_html = raw

        duration = time.time() - t0
        logger.info(
            f"✅ Section Generated → {section_type} ({len(new_section_html):,} chars) in {_fmt_duration(duration)}"
        )

        # Resolve image placeholders (with hallucination safety)
        niche_key = brand.get("industry", "general")
        new_section_html = await _resolve_images_safe(new_section_html, niche_key=niche_key)

        # Insert the new section at the right position
        footer_exists = any(s["type"] == "footer" for s in sections)
        if section_type == "footer":
            insert_desc = "after last section (end of page)"
        elif footer_exists:
            insert_desc = "before existing footer"
        else:
            insert_desc = "at end of page (before </body>)"
        logger.info(f"📍 Insert Position → {insert_desc}")
        updated_html = _insert_section(html, new_section_html, section_type, sections)
        logger.info(f"✅ Section Appended → page grew from {len(html):,} to {len(updated_html):,} chars")

        return {"html": updated_html, "css": css, "js": js}

    except Exception as e:
        logger.error(f"❌ Append Failed → {e} — falling back to full page rewrite")
        return await _iterate_full_page(prompt, session)


def _insert_section(html: str, new_section_html: str, section_type: str, sections: list[dict]) -> str:
    """Insert a new section at the appropriate position in the HTML.

    - Footer → after the last section (before </body> or </main>)
    - Other sections → before the footer if one exists, else at the end
    """
    # Find footer section if any
    footer_section = None
    last_section = None
    for s in sections:
        last_section = s
        if s["type"] == "footer":
            footer_section = s

    new_section_html = "\n\n" + new_section_html.strip() + "\n\n"

    if section_type == "footer":
        # Insert footer at the very end — after last section
        if last_section:
            insert_pos = last_section["end"]
            return html[:insert_pos] + new_section_html + html[insert_pos:]
    else:
        # Insert before footer if it exists
        if footer_section:
            insert_pos = footer_section["start"]
            return html[:insert_pos] + new_section_html + html[insert_pos:]

    # Fallback: insert before </body> or </main>, or append at end
    for tag in ["</main>", "</body>"]:
        pos = html.rfind(tag)
        if pos != -1:
            return html[:pos] + new_section_html + html[pos:]

    # Last resort: append at the end
    return html + new_section_html


async def _iterate_full_page(prompt: str, session: dict) -> dict[str, str]:
    """Legacy full-page rewrite for complex edits (add section, rearrange layout)."""
    logger.info("🔄 Full Page Rewrite → regenerating entire page")
    client = get_anthropic_client()

    # Detect if this is a major redesign request — needs more tokens
    redesign_keywords = [
        "redesign",
        "rebuild",
        "redo",
        "start over",
        "from scratch",
        "completely new",
        "whole website",
        "entire website",
        "full redesign",
        "new design",
        "new look",
        "makeover",
        "overhaul",
    ]
    prompt_lower = prompt.lower()
    is_redesign = any(kw in prompt_lower for kw in redesign_keywords)
    max_tokens = 30000 if is_redesign else 16000
    logger.info(f"⚙️ Rewrite Config → {'MAJOR REDESIGN' if is_redesign else 'standard edit'}, max_tokens={max_tokens:,}")
    logger.info(f"📦 Current Page → HTML={len(session['html']):,} chars, CSS={len(session['css']):,} chars")

    system = ITERATION_SYSTEM_PROMPT.format(
        html=session["html"],
        css=session["css"],
        js=session.get("js", ""),
        conversation_history=format_conversation_history(session),
        prompt=prompt,
    )
    logger.info(f"🚀 Executing Step → Sending full page + edit request to Claude Sonnet ({len(system):,} chars prompt)")

    text = await _claude_stream(
        client,
        "claude-sonnet-4-20250514",
        max_tokens,
        system,
        f"Apply these changes: {prompt}",
    )
    blocks = parse_code_blocks(text)
    # Extract <style> from HTML if iteration returned it inline
    if blocks.get("html") and "<style" in blocks["html"]:
        css_extracted, html_clean = extract_style_block(blocks["html"])
        blocks["html"] = html_clean
        if css_extracted:
            blocks["css"] = css_extracted
    logger.info(
        f"✅ Full Rewrite Complete → HTML={len(blocks.get('html', '')):,}, CSS={len(blocks.get('css', '')):,}, JS={len(blocks.get('js', '')):,} chars"
    )
    return blocks


# ═══════════════════════════════════════════════════════════════════════
# ELEMENT EDITING
# ═══════════════════════════════════════════════════════════════════════

ELEMENT_EDIT_PROMPT = """You are an expert web developer. Edit a specific element on a website that uses pure CSS classes (NO Tailwind).

CURRENT FULL HTML (body content with semantic CSS classes):
{html}

CURRENT STYLE BLOCK (CSS variables, layout, components):
{css}

SELECTED ELEMENT (CSS path: {element_path}):
{element_html}

USER'S EDIT REQUEST: {prompt}

Return the COMPLETE updated HTML. Only modify the targeted element.

RULES:
- Return ONE fenced code block: ```html
- HTML = <style> block FIRST + FULL updated body content with semantic CSS classes
- Use CSS classes already defined in the <style> block for styling changes
- Do NOT use Tailwind utility classes. Add new CSS rules to the <style> block if needed.
- Do NOT generate large inline SVGs or decorative clip-path shapes
- Do NOT include any explanation, just the code block

SECTION SIZE CONSTRAINTS:
- Hero: max height 80vh. NEVER taller than viewport.
- All sections: keep the same size as original. No excessive padding.

IMAGE HANDLING:
- "Add background image" = CSS background-image ONLY (no extra <img> tag)
- Background images: background-size: cover; background-position: center; with overlay
- NEVER add BOTH a background-image AND a foreground <img> for the same purpose

JS-DEPENDENT CLASS NAMES (do NOT rename — JS will break):
.nav-links, .nav-toggle, .faq-item, .faq-question, .faq-answer,
.testimonial-slide, .slider-dot, .carousel-container, .carousel-track,
.carousel-slide, .carousel-prev, .carousel-next, .carousel-dot,
#gallery-lightbox, .gallery-item, .modal-trigger, .detail-modal,
.modal-close, .stat-number, #year, #back-to-top"""


# ═══════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════


class GenerateRequest(BaseModel):
    prompt: str
    sessionId: str | None = None
    niche: str | None = None
    designSystem: dict | None = None
    templateId: str | None = None
    currentPage: str = "index"


class EditElementRequest(BaseModel):
    sessionId: str
    elementHtml: str
    elementPath: str
    prompt: str
    currentHtml: str
    currentCss: str
    currentPage: str = "index"


# ═══════════════════════════════════════════════════════════════════════
# RESTORE SESSION (hydrate backend session from saved project)
# ═══════════════════════════════════════════════════════════════════════


class RestoreSessionRequest(BaseModel):
    html: str
    css: str
    js: str = ""
    projectId: str | None = None
    projectName: str | None = None


@router.post("/restore-session")
async def restore_session(req: RestoreSessionRequest, user: dict = Depends(require_auth)):
    """Create a backend session from saved project data.
    This is called when loading a project from the dashboard so that
    all features (chat iteration, sections, design system) work.
    """
    # Validate input size to prevent abuse
    MAX_RESTORE_SIZE = 200_000  # 200KB
    total_size = len(req.html) + len(req.css) + len(req.js)
    if total_size > MAX_RESTORE_SIZE:
        raise HTTPException(status_code=413, detail=f"Payload too large ({total_size} chars, max {MAX_RESTORE_SIZE})")

    session_id = str(uuid.uuid4())

    html = inject_section_ids(req.html)
    sections_list = parse_sections(html)

    await redis_save_session(
        session_id,
        {
            "html": html,
            "css": req.css,
            "js": req.js,
            "plan": {},
            "prompts": [],
            "versions": [],
            "current_version": 1,
            "user_id": user["user_id"],
            "project_id": req.projectId,
        },
    )

    return {
        "sessionId": session_id,
        "sections": sections_list,
    }


class SyncSessionRequest(BaseModel):
    sessionId: str
    html: str
    css: str
    js: str = ""
    currentPage: str = "index"


@router.post("/sync-session")
async def sync_session(req: SyncSessionRequest, user: dict = Depends(require_auth)):
    """Update an existing session's HTML/CSS/JS (used by undo/redo)."""
    session = await redis_get_session(req.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_ownership(session, user)

    html = inject_section_ids(req.html)

    # Multi-page aware: write to the correct page slot
    if session.get("multipage") and req.currentPage:
        if "pages" not in session:
            session["pages"] = {}
        session["pages"][req.currentPage] = {"html": html, "css": req.css}
        if req.currentPage == "index":
            session["html"] = html
            session["css"] = req.css
    else:
        session["html"] = html
        session["css"] = req.css
    session["js"] = req.js

    await redis_save_session(req.sessionId, session)

    sections_list = parse_sections(html)
    return {"success": True, "sections": sections_list}


# ═══════════════════════════════════════════════════════════════════════
# SSE STREAMING ENDPOINT
# ═══════════════════════════════════════════════════════════════════════


@router.post("/generate-stream")
async def generate_website_stream(req: GenerateRequest, user: dict = Depends(require_auth)):
    """SSE streaming — 4-stage pipeline with live updates. CSS+JS run in parallel."""
    logger.info(f"[NEW REQUEST] prompt={len(req.prompt or '')} chars")

    # ── Sanitize & moderate prompt ──────────────────────────────────
    req.prompt = sanitize_prompt(req.prompt)
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    moderation = await moderate_prompt(req.prompt)
    logger.info(f"[MODERATION] {'SAFE' if moderation['safe'] else 'BLOCKED: ' + moderation.get('reason', '')}")
    if not moderation["safe"]:
        raise HTTPException(status_code=400, detail=moderation["reason"])

    is_new = req.sessionId is None or not await redis_session_exists(req.sessionId)
    session_id = req.sessionId if not is_new else str(uuid.uuid4())

    # ── Audit log (fire-and-forget) ─────────────────────────────────
    log_event_bg(
        user_id=str(user["user_id"]),
        action="generate_website" if is_new else "edit_website",
        resource_type="website",
        resource_id=session_id,
        details={"prompt": req.prompt[:500]},
    )

    mode = "NEW GENERATION" if is_new else "EDIT"
    logger.info(
        f'{"🆕" if is_new else "✏️"} [{mode}] session={session_id[:8]}... prompt="{req.prompt[:80]}{"..." if len(req.prompt) > 80 else ""}"'
    )

    async def event_stream():
        def sse(event: str, data: dict):
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        logger.info(f"[STREAM START] session={session_id[:8]}...")
        pipeline_start = time.time()
        metrics_increment("generations_total")
        quality_scores = {}
        is_multipage = False
        pages_dict = None

        try:
            if is_new:
                # ── Stage 0: Prompt Enhancement ───────────────────────
                yield sse(
                    "stage",
                    {"stage": -1, "name": "enhance", "status": "running", "message": "Understanding your vision..."},
                )

                enhanced_prompt = await enhance_prompt(req.prompt)

                yield sse(
                    "stage",
                    {
                        "stage": -1,
                        "name": "enhance",
                        "status": "done",
                        "message": "Brief prepared",
                        "enhanced_prompt": enhanced_prompt,
                    },
                )

                # Save enhanced prompt for debugging
                save_debug(session_id, "enhanced_prompt", enhanced_prompt)

                # ── Detect niche for image quality ─────────────────────
                from app.utils.niches import detect_niche

                niche_key = detect_niche(enhanced_prompt)
                logger.info(f"[NICHE] detected={niche_key or 'generic'}")

                # ── Load reference template if provided ───────────────
                reference_html = None
                if req.templateId:
                    try:
                        from app.routes.templates import _load_template_file

                        ref_html, ref_css = _load_template_file(req.templateId)
                        # Combine CSS + HTML as reference
                        reference_html = f"<style>{ref_css}</style>\n{ref_html}"
                        logger.info(f"[TEMPLATE] loaded '{req.templateId}' ({len(reference_html):,} chars)")
                    except Exception as e:
                        logger.warning(f"[TEMPLATE] failed to load '{req.templateId}': {e}")

                # Auto-match reference template from niche if none was explicitly chosen
                if not reference_html and niche_key:
                    reference_html = _find_best_reference_template(niche_key)
                    if reference_html:
                        logger.info(f"[TEMPLATE] auto-matched niche '{niche_key}' → reference template ({len(reference_html):,} chars)")

                # ── Detect multi-page request (only from user's ORIGINAL prompt, not the enhanced brief) ──
                multipage_requested = is_multipage_request(req.prompt)

                # ── Stage 1: Plan ──────────────────────────────────────
                yield sse(
                    "stage",
                    {
                        "stage": 0,
                        "name": "plan",
                        "status": "running",
                        "message": "Analyzing your request and planning the website...",
                    },
                )

                plan_task = asyncio.create_task(
                    stage_1_plan(enhanced_prompt, session_id, niche_key=niche_key, multipage=multipage_requested)
                )
                while not plan_task.done():
                    await asyncio.sleep(8)
                    if not plan_task.done():
                        yield ": keepalive\n\n"
                plan = plan_task.result()
                is_multipage = plan.get("multipage", False)

                brand = plan.get("brand", {}).get("name", "")
                if is_multipage:
                    n_pages = len(plan.get("pages", []))
                    n_sections = sum(len(p.get("sections", [])) for p in plan.get("pages", []))
                    yield sse(
                        "stage",
                        {
                            "stage": 0,
                            "name": "plan",
                            "status": "done",
                            "message": f"Plan ready: {brand} ({n_pages} pages)"
                            if brand
                            else f"Plan ready ({n_pages} pages)",
                            "detail": f"{n_pages} pages, {n_sections} total sections planned",
                        },
                    )
                else:
                    n_sections = len(plan.get("sections", []))
                    yield sse(
                        "stage",
                        {
                            "stage": 0,
                            "name": "plan",
                            "status": "done",
                            "message": f"Plan ready: {brand}" if brand else "Plan ready",
                            "detail": f"{n_sections} sections planned",
                        },
                    )

                # ── Stage 2: HTML + Image Resolution ──────────────────
                pages_dict = None  # Will hold {slug: {html, css}} for multipage

                if is_multipage:
                    # Multi-page: generate all pages in parallel
                    yield sse(
                        "stage",
                        {
                            "stage": 1,
                            "name": "html",
                            "status": "running",
                            "message": f"Building {n_pages} pages in parallel...",
                        },
                    )

                    html_task = asyncio.create_task(
                        generate_multipage_html(plan, session_id, niche_key=niche_key, reference_html=reference_html)
                    )
                    while not html_task.done():
                        await asyncio.sleep(8)
                        if not html_task.done():
                            yield ": keepalive\n\n"
                    pages_html = html_task.result()  # {slug: html_string}

                    total_html_chars = sum(len(h) for h in pages_html.values())
                    yield sse(
                        "stage",
                        {
                            "stage": 1,
                            "name": "html",
                            "status": "done",
                            "message": f"{len(pages_html)} pages generated ({total_html_chars:,} chars total)",
                        },
                    )

                    # Extract CSS from each page and build pages_dict
                    theme = plan.get("design", {}).get("theme", "light")
                    pages_dict = {}
                    for slug, page_html in pages_html.items():
                        page_css, page_html_clean = extract_style_block(page_html)
                        # Auto-polish CSS
                        page_css = polish_css(page_css, theme)
                        pages_dict[slug] = {"html": page_html_clean, "css": page_css}

                    # Use index page as the main html/css for backward compatibility
                    index_data = pages_dict.get(
                        "index", list(pages_dict.values())[0] if pages_dict else {"html": "", "css": ""}
                    )
                    html = index_data["html"]
                    css = index_data["css"]
                    save_debug(session_id, "css", css)

                    yield sse(
                        "stage",
                        {
                            "stage": 2,
                            "name": "css",
                            "status": "done",
                            "message": f"CSS extracted from {len(pages_dict)} pages",
                        },
                    )
                else:
                    # Single-page: prefer template-first when a reference template is available
                    use_template_path = reference_html is not None
                    if use_template_path:
                        yield sse(
                            "stage",
                            {"stage": 1, "name": "html", "status": "running", "message": "Customizing template for your business..."},
                        )
                        html_task = asyncio.create_task(
                            stage_2_html_from_template(reference_html, plan, session_id, niche_key=niche_key)
                        )
                    else:
                        yield sse(
                            "stage",
                            {"stage": 1, "name": "html", "status": "running", "message": "Building the page structure..."},
                        )
                        html_task = asyncio.create_task(
                            stage_2_html(plan, session_id, niche_key=niche_key, reference_html=None, enhanced_brief=enhanced_prompt)
                        )

                    while not html_task.done():
                        await asyncio.sleep(8)
                        if not html_task.done():
                            yield ": keepalive\n\n"
                    html = html_task.result()

                    yield sse(
                        "stage",
                        {"stage": 1, "name": "html", "status": "done", "message": f"HTML ready ({len(html):,} chars)"},
                    )

                    # ── Extract CSS from HTML <style> block ──────────────
                    css, html = extract_style_block(html)
                    # Auto-polish CSS
                    theme = plan.get("design", {}).get("theme", "light")
                    css = polish_css(css, theme)
                    save_debug(session_id, "css", css)

                    yield sse(
                        "stage",
                        {"stage": 2, "name": "css", "status": "done", "message": f"CSS extracted ({len(css):,} chars)"},
                    )

                # ── Stage 3: JS (shared across all pages) ───────────
                yield sse("stage", {"stage": 2, "name": "js", "status": "running", "message": "Adding interactions..."})

                # For multipage, generate JS based on combined HTML context
                if is_multipage and pages_dict:
                    # Combine all page HTML for JS context (so JS handles all page types)
                    combined_html = "\n".join(pd["html"] for pd in pages_dict.values())
                    js = await stage_3_js(combined_html, session_id)
                else:
                    js = await stage_3_js(html, session_id)

                yield sse(
                    "stage", {"stage": 2, "name": "js", "status": "done", "message": f"JS ready ({len(js):,} chars)"}
                )

                # ── Stage 4: Quality checks + auto-fix ─────────────────
                yield sse(
                    "stage",
                    {
                        "stage": 3,
                        "name": "polish",
                        "status": "running",
                        "message": "Polishing, optimizing images & checking quality...",
                    },
                )

                quality_scores = {}

                # Helper to apply quality fixes to a single html/css pair
                def _apply_quality_fixes(page_html, page_css):
                    """Apply responsive, image, form, SEO, and perf fixes. Returns (html, css)."""
                    try:
                        from app.utils.responsive_check import auto_fix_responsive

                        page_html, page_css = auto_fix_responsive(page_html, page_css)
                    except Exception as e:
                        logger.warning(f"[RESPONSIVE] check failed: {e}")
                    try:
                        from app.utils.image_optimizer import optimize_image_tags

                        page_html = optimize_image_tags(page_html)
                    except Exception as e:
                        logger.warning(f"[IMAGES] optimizer failed: {e}")
                    return page_html, page_css

                try:
                    from app.utils.responsive_check import auto_fix_responsive, check_responsive

                    report = check_responsive(html, css)
                    html, css = auto_fix_responsive(html, css)
                    logger.info(f"[RESPONSIVE] score={report['score']}/100, {report['auto_fixed']} auto-fixed")
                except Exception as e:
                    logger.warning(f"[RESPONSIVE] check failed: {e}")

                # ── Image optimization ────────────────────────────────
                try:
                    from app.utils.image_optimizer import optimize_image_tags

                    html = optimize_image_tags(html)
                except Exception as e:
                    logger.warning(f"[IMAGES] optimizer failed: {e}")

                # ── Form handler injection ────────────────────────────
                try:
                    from app.utils.form_handler import has_contact_form, inject_form_handler

                    if has_contact_form(html):
                        html, js = inject_form_handler(html, js)
                        logger.info("[FORMS] contact form handler injected")
                except Exception as e:
                    logger.warning(f"[FORMS] injection failed: {e}")

                # ── SEO tag generation + injection ────────────────────
                try:
                    from app.utils.seo_checker import check_seo, generate_seo_tags, inject_seo_into_html

                    seo_tags = generate_seo_tags(plan)
                    html = inject_seo_into_html(html, seo_tags)

                    seo_report = check_seo(html, plan)
                    quality_scores["seo_score"] = seo_report["score"]
                    logger.info(
                        f"[SEO] score={seo_report['score']}/100, {len(seo_report['passed'])} passed, {len(seo_report['issues'])} issues"
                    )
                except Exception as e:
                    logger.warning(f"[SEO] check failed: {e}")

                # ── Performance check + auto-fix ──────────────────────
                try:
                    from app.utils.lighthouse_check import auto_fix_performance, check_performance

                    perf_report = check_performance(html, css, js)
                    html, css, js = auto_fix_performance(html, css, js)

                    quality_scores["performance_score"] = perf_report["score"]
                    quality_scores["issues_fixed"] = len(perf_report["auto_fixable"])
                    logger.info(
                        f"[PERF] score={perf_report['score']}/100, {len(perf_report['auto_fixable'])} auto-fixed"
                    )
                except Exception as e:
                    logger.warning(f"[PERF] check failed: {e}")

                # ── Apply quality fixes to all multipage pages ────────
                if is_multipage and pages_dict:
                    for slug in pages_dict:
                        if slug == "index":
                            # Index page already fixed above via main html/css
                            pages_dict[slug]["html"] = html
                            pages_dict[slug]["css"] = css
                        else:
                            p_html, p_css = _apply_quality_fixes(pages_dict[slug]["html"], pages_dict[slug]["css"])
                            pages_dict[slug]["html"] = p_html
                            pages_dict[slug]["css"] = p_css

                # Build summary message
                perf_score = quality_scores.get("performance_score", "—")
                seo_score_val = quality_scores.get("seo_score", "—")
                fixes = quality_scores.get("issues_fixed", 0)
                yield sse(
                    "stage",
                    {
                        "stage": 3,
                        "name": "polish",
                        "status": "done",
                        "message": f"Perf: {perf_score}/100 | SEO: {seo_score_val}/100 | {fixes} auto-fixes",
                    },
                )

                # ── Inject animation CSS + JS ─────────────────────────
                try:
                    from app.utils.animations import get_animation_css, get_animation_js

                    anim_css = get_animation_css()
                    if anim_css and anim_css not in css:
                        css = css + "\n\n/* === Built-in Animations === */\n" + anim_css
                    anim_js = get_animation_js()
                    if anim_js and "image-reveal" not in js:
                        js = js + "\n\n// === Built-in Animation Observers ===\n" + anim_js

                    # Also inject animation CSS into multipage subpages
                    if is_multipage and pages_dict and anim_css:
                        for slug in pages_dict:
                            if slug != "index" and anim_css not in pages_dict[slug]["css"]:
                                pages_dict[slug]["css"] += "\n\n/* === Built-in Animations === */\n" + anim_css
                except Exception:
                    pass

                code = {"html": html, "css": css, "js": js}

                total_ms = int((time.time() - pipeline_start) * 1000)
                if is_multipage:
                    logger.info(
                        f"🏁 Pipeline Complete → Total {_fmt_duration(total_ms)} — {len(pages_dict)} pages, JS {len(js):,} chars"
                    )
                else:
                    logger.info(
                        f"🏁 Pipeline Complete → Total {_fmt_duration(total_ms)} — HTML {len(html):,} + CSS {len(css):,} + JS {len(js):,} chars"
                    )
                logger.info(
                    f"📊 Quality Scores → Perf: {quality_scores.get('performance_score', '?')}/100, SEO: {quality_scores.get('seo_score', '?')}/100, Fixes: {quality_scores.get('issues_fixed', 0)}"
                )

            else:
                # ── Iteration (component-based) ───────────────────────
                session = await redis_get_session(session_id)
                if not session:
                    yield sse("error", {"message": "Session not found"})
                    return

                # ── Check for "add page" request BEFORE normal routing ──
                add_page_info = detect_add_page_request(req.prompt)
                existing_pages = session.get("pages", {})
                # Only treat as add-page if slug doesn't already exist
                if add_page_info and add_page_info["slug"] not in existing_pages and add_page_info["slug"] != "index":
                    page_count = len(existing_pages) if existing_pages else 1  # 1 = current single page
                    if page_count >= 5:
                        yield sse(
                            "error", {"message": "Maximum 5 pages reached. Remove a page before adding a new one."}
                        )
                        return

                    page_slug = add_page_info["slug"]
                    page_title = add_page_info["title"]

                    yield sse(
                        "stage",
                        {"stage": 0, "name": "route", "status": "running", "message": f"Adding {page_title} page..."},
                    )
                    yield sse(
                        "stage",
                        {"stage": 0, "name": "route", "status": "done", "message": f"Target: new {page_title} page"},
                    )

                    yield sse(
                        "stage",
                        {
                            "stage": 1,
                            "name": "edit",
                            "status": "running",
                            "message": f"Generating {page_title} page (matching existing design)...",
                        },
                    )

                    new_page_code = await _add_new_page(req.prompt, session, page_slug, page_title)

                    if not new_page_code.get("html"):
                        yield sse("error", {"message": f"Failed to generate {page_title} page"})
                        return

                    # Build pages dict: keep homepage untouched, add new page
                    if not existing_pages:
                        # Converting single-page → multipage
                        pages_dict = {
                            "index": {"html": session["html"], "css": session["css"]},
                            page_slug: {"html": new_page_code["html"], "css": new_page_code["css"]},
                        }
                    else:
                        pages_dict = {**existing_pages}
                        pages_dict[page_slug] = {"html": new_page_code["html"], "css": new_page_code["css"]}

                    # Update navbars in ALL existing pages to include the new page link
                    pages_dict = _update_all_page_navbars(pages_dict, page_slug, page_title)
                    # Also update session["html"] if index was modified
                    if "index" in pages_dict:
                        session["html"] = pages_dict["index"]["html"]

                    # code dict = the new page (frontend will display it)
                    code = new_page_code
                    plan = session.get("plan") or {}

                    # Save multipage state to session
                    session["multipage"] = True
                    session["pages"] = pages_dict
                    session["_added_page"] = page_slug  # Signal for SSE payload

                    yield sse(
                        "stage", {"stage": 1, "name": "edit", "status": "done", "message": f"{page_title} page created"}
                    )

                else:
                    # ── Normal edit flow (existing logic unchanged) ────

                    # Multi-page aware: swap session html/css to current page's data
                    current_page = req.currentPage or "index"
                    _original_index_html = session.get("html", "")
                    _original_index_css = session.get("css", "")
                    if session.get("multipage") and current_page != "index":
                        page_data = session.get("pages", {}).get(current_page)
                        if page_data:
                            session["html"] = page_data["html"]
                            session["css"] = page_data.get("css", session["css"])

                    # Route to target component(s)
                    yield sse(
                        "stage",
                        {"stage": 0, "name": "route", "status": "running", "message": "Identifying target sections..."},
                    )

                    targets = await route_edit_to_components(req.prompt, session)

                    append_targets = [t for t in targets if t.startswith("__append__:")]
                    if "__full__" in targets:
                        target_desc = "full page rewrite"
                    elif append_targets:
                        append_type = append_targets[0].split(":", 1)[1]
                        target_desc = f"adding {append_type} section"
                    elif "__style__" in targets:
                        target_desc = "global styles"
                    else:
                        sections_meta = parse_sections(session["html"])
                        sid_to_type = {s["id"]: s["type"] for s in sections_meta}
                        target_names = [sid_to_type.get(t, t) for t in targets]
                        target_desc = ", ".join(target_names)

                    yield sse(
                        "stage", {"stage": 0, "name": "route", "status": "done", "message": f"Target: {target_desc}"}
                    )

                    # Edit the component(s)
                    edit_action = "Adding" if append_targets else "Editing"
                    yield sse(
                        "stage",
                        {"stage": 1, "name": "edit", "status": "running", "message": f"{edit_action} {target_desc}..."},
                    )

                    # Call iterate_website which handles routing internally too,
                    # but pass pre-routed targets to avoid double routing
                    code = await _execute_component_edit(req.prompt, session, targets)
                    plan = session.get("plan")

                    if not code.get("html"):
                        yield sse("error", {"message": "Failed to apply changes"})
                        return

                    yield sse("stage", {"stage": 1, "name": "edit", "status": "done", "message": "Changes applied"})

            # ── Finalize ───────────────────────────────────────────
            code["html"] = inject_section_ids(code["html"])
            sections_list = parse_sections(code["html"])

            existing = await redis_get_session(session_id) or {}
            prev_versions = existing.get("versions", [])
            version_number = len(prev_versions) + 1

            if not is_new and existing:
                prev_versions.append(
                    {
                        "version": version_number - 1,
                        "html": existing["html"],
                        "css": existing["css"],
                        "js": existing.get("js", ""),
                        "prompt": existing.get("prompts", [""])[-1] if existing.get("prompts") else "",
                    }
                )
                # Cap version history to prevent Redis OOM
                MAX_VERSIONS = 15
                if len(prev_versions) > MAX_VERSIONS:
                    prev_versions = prev_versions[-MAX_VERSIONS:]

            # Persist last_edited_targets for follow-up routing context
            last_targets = session.get("last_edited_targets", []) if not is_new else []
            session_data = {
                "html": code["html"],
                "css": code["css"],
                "js": code["js"],
                "plan": plan if is_new else existing.get("plan"),
                "prompts": existing.get("prompts", []) + [req.prompt],
                "versions": prev_versions,
                "current_version": version_number,
                "user_id": user["user_id"],
                "last_edited_targets": last_targets,
            }

            # Include multipage data in session
            added_page_slug = session.get("_added_page") if not is_new else None
            if is_new and is_multipage and pages_dict:
                session_data["multipage"] = True
                session_data["pages"] = {
                    slug: {"html": pd["html"], "css": pd["css"]} for slug, pd in pages_dict.items()
                }
            elif added_page_slug:
                # "Add page" operation — session["pages"] was already built in the iteration block
                session_data["multipage"] = True
                session_data["pages"] = session.get("pages", {})
                # session["html"] should always reflect the index page
                index_data = session_data["pages"].get("index")
                if index_data:
                    session_data["html"] = index_data["html"]
                    session_data["css"] = index_data["css"]
            elif not is_new and existing.get("multipage"):
                session_data["multipage"] = existing.get("multipage", False)
                session_data["pages"] = existing.get("pages") or {}
                # Update the correct page slot with edited code
                current_page = getattr(req, "currentPage", "index") or "index"
                session_data["pages"][current_page] = {"html": code["html"], "css": code["css"]}
                # session["html"] should always reflect the index page
                if current_page != "index":
                    index_data = session_data["pages"].get("index")
                    if index_data:
                        session_data["html"] = index_data["html"]
                        session_data["css"] = index_data["css"]

            await redis_save_session(session_id, session_data)

            # Extract SEO metadata from plan
            brand_name = plan.get("brand", {}).get("name", "Website")
            meta_desc = plan.get("brand", {}).get("tagline", "")

            generation_ms = round((time.time() - pipeline_start) * 1000, 2)
            metrics_observe("generation_duration_ms", generation_ms)

            total_chars = len(code.get("html", "")) + len(code.get("css", "")) + len(code.get("js", ""))
            if is_new:
                if is_multipage and pages_dict:
                    logger.info(
                        f"🎉 Generation Complete → session={session_id[:8]}, {len(pages_dict)} pages, {total_chars:,} total chars in {_fmt_duration(generation_ms)}"
                    )
                else:
                    logger.info(
                        f"🎉 Generation Complete → session={session_id[:8]}, {len(sections_list)} sections, {total_chars:,} total chars in {_fmt_duration(generation_ms)}"
                    )
            else:
                logger.info(
                    f"✅ Edit Complete → session={session_id[:8]}, v{version_number}, {total_chars:,} total chars in {_fmt_duration(generation_ms)}"
                )

            complete_payload = {
                "success": True,
                "website": {"html": code["html"], "css": code["css"], "js": code["js"]},
                "sessionId": session_id,
                "isNewDesign": is_new,
                "sections": sections_list,
                "version": version_number,
                "meta": {"title": brand_name, "description": meta_desc},
            }
            if quality_scores:
                complete_payload["quality"] = quality_scores

            # Include multipage data in response
            if is_new and is_multipage and pages_dict:
                complete_payload["isMultipage"] = True
                complete_payload["pages"] = {
                    slug: {"html": pd["html"], "css": pd["css"]} for slug, pd in pages_dict.items()
                }
            elif added_page_slug:
                # New page was added — send full multipage state so frontend can switch to it
                complete_payload["isMultipage"] = True
                complete_payload["pages"] = session_data.get("pages", {})
                complete_payload["addedPage"] = added_page_slug
            elif not is_new and session_data.get("multipage"):
                # Normal edit on a multipage site — include updated pages so frontend stays in sync
                complete_payload["isMultipage"] = True
                complete_payload["pages"] = session_data.get("pages", {})

            yield sse("complete", complete_payload)

        except CircuitOpenError:
            metrics_increment("generation_errors")
            yield sse("error", {"message": "AI service is temporarily unavailable. Please try again in a few minutes."})
        except Exception as e:
            metrics_increment("generation_errors")
            logger.error(f"[STREAM ERROR] {e}", exc_info=True)
            yield sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ═══════════════════════════════════════════════════════════════════════
# SYNC ENDPOINT (fallback)
# ═══════════════════════════════════════════════════════════════════════


@router.post("/generate")
async def generate_website(req: GenerateRequest, user: dict = Depends(require_auth)):
    # ── Sanitize & moderate prompt ──────────────────────────────────
    req.prompt = sanitize_prompt(req.prompt)
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    moderation = await moderate_prompt(req.prompt)
    if not moderation["safe"]:
        raise HTTPException(status_code=400, detail=moderation["reason"])

    is_new = req.sessionId is None or not await redis_session_exists(req.sessionId)
    session_id = req.sessionId if not is_new else str(uuid.uuid4())

    # ── Audit log (fire-and-forget) ─────────────────────────────────
    log_event_bg(
        user_id=str(user["user_id"]),
        action="generate_website" if is_new else "edit_website",
        resource_type="website",
        resource_id=session_id,
        details={"prompt": req.prompt[:500]},
    )

    metrics_increment("generations_total")
    generation_start = time.time()

    try:
        pages_dict = None
        is_multipage_gen = False

        if is_new:
            pipeline_start = time.time()

            from app.utils.niches import detect_niche

            niche_key = detect_niche(req.prompt)
            multipage_requested = is_multipage_request(req.prompt)

            # Load reference template (explicit or auto-matched)
            reference_html = None
            if req.templateId:
                try:
                    from app.routes.templates import _load_template_file

                    ref_html, ref_css = _load_template_file(req.templateId)
                    reference_html = f"<style>{ref_css}</style>\n{ref_html}"
                    logger.info(f"[TEMPLATE] loaded '{req.templateId}' ({len(reference_html):,} chars)")
                except Exception as e:
                    logger.warning(f"[TEMPLATE] failed to load '{req.templateId}': {e}")

            # Auto-match reference template from niche if none was explicitly chosen
            if not reference_html and niche_key:
                reference_html = _find_best_reference_template(niche_key)
                if reference_html:
                    logger.info(f"[TEMPLATE] auto-matched niche '{niche_key}' → reference template ({len(reference_html):,} chars)")

            plan = await stage_1_plan(req.prompt, session_id, niche_key=niche_key, multipage=multipage_requested)
            is_multipage_gen = plan.get("multipage", False)

            theme = plan.get("design", {}).get("theme", "light")

            if is_multipage_gen:
                # Multi-page generation
                pages_html = await generate_multipage_html(plan, session_id, niche_key=niche_key, reference_html=reference_html)
                pages_dict = {}
                for slug, page_html in pages_html.items():
                    page_css, page_html_clean = extract_style_block(page_html)
                    # Auto-polish CSS
                    page_css = polish_css(page_css, theme)
                    pages_dict[slug] = {"html": page_html_clean, "css": page_css}
                # Use index page as main for backward compat
                index_data = pages_dict.get(
                    "index", list(pages_dict.values())[0] if pages_dict else {"html": "", "css": ""}
                )
                html = index_data["html"]
                css = index_data["css"]
                # Generate JS based on combined HTML
                combined_html = "\n".join(pd["html"] for pd in pages_dict.values())
                js = await stage_3_js(combined_html, session_id)
            else:
                if reference_html:
                    html = await stage_2_html_from_template(reference_html, plan, session_id, niche_key=niche_key)
                else:
                    html = await stage_2_html(plan, session_id, niche_key=niche_key, reference_html=None)
                css, html = extract_style_block(html)
                # Auto-polish CSS
                css = polish_css(css, theme)
                js = await stage_3_js(html, session_id)

            # Responsive check + auto-fix
            try:
                from app.utils.responsive_check import auto_fix_responsive

                html, css = auto_fix_responsive(html, css)
            except Exception:
                pass

            # Image optimization
            try:
                from app.utils.image_optimizer import optimize_image_tags

                html = optimize_image_tags(html)
            except Exception:
                pass

            # Form handler injection
            try:
                from app.utils.form_handler import has_contact_form, inject_form_handler

                if has_contact_form(html):
                    html, js = inject_form_handler(html, js)
            except Exception:
                pass

            # SEO tag generation + injection
            try:
                from app.utils.seo_checker import generate_seo_tags, inject_seo_into_html

                seo_tags = generate_seo_tags(plan)
                html = inject_seo_into_html(html, seo_tags)
            except Exception:
                pass

            # Performance auto-fix
            try:
                from app.utils.lighthouse_check import auto_fix_performance

                html, css, js = auto_fix_performance(html, css, js)
            except Exception:
                pass

            # Inject animation CSS + JS
            try:
                from app.utils.animations import get_animation_css, get_animation_js

                anim_css = get_animation_css()
                if anim_css and anim_css not in css:
                    css = css + "\n\n/* === Built-in Animations === */\n" + anim_css
                anim_js = get_animation_js()
                if anim_js and "image-reveal" not in js:
                    js = js + "\n\n// === Built-in Animation Observers ===\n" + anim_js
            except Exception:
                pass

            # Apply quality fixes to multipage subpages
            if is_multipage_gen and pages_dict:
                pages_dict["index"] = {"html": html, "css": css}
                for slug in pages_dict:
                    if slug != "index":
                        try:
                            from app.utils.image_optimizer import optimize_image_tags
                            from app.utils.responsive_check import auto_fix_responsive

                            p_html, p_css = auto_fix_responsive(pages_dict[slug]["html"], pages_dict[slug]["css"])
                            p_html = optimize_image_tags(p_html)
                            pages_dict[slug] = {"html": p_html, "css": p_css}
                        except Exception:
                            pass

            code = {"html": html, "css": css, "js": js}

            total_ms = int((time.time() - pipeline_start) * 1000)
            logger.info(
                f"[DONE] Total {_fmt_duration(total_ms)} — HTML {len(html):,} + CSS {len(css):,} + JS {len(js):,} chars"
            )
        else:
            session = await redis_get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            # Multi-page aware: swap to current page's data for editing
            current_page = req.currentPage or "index"
            if session.get("multipage") and current_page != "index":
                page_data = session.get("pages", {}).get(current_page)
                if page_data:
                    session["html"] = page_data["html"]
                    session["css"] = page_data.get("css", session["css"])
            code = await iterate_website(req.prompt, session)
            plan = session.get("plan")
            if not code["html"]:
                raise HTTPException(status_code=500, detail="Failed to apply changes")

        code["html"] = inject_section_ids(code["html"])
        sections_list = parse_sections(code["html"])

        existing = await redis_get_session(session_id) or {}
        prev_versions = existing.get("versions", [])

        if not is_new and existing:
            prev_versions.append(
                {
                    "version": len(prev_versions),
                    "html": existing["html"],
                    "css": existing["css"],
                    "js": existing.get("js", ""),
                    "prompt": existing.get("prompts", [""])[-1] if existing.get("prompts") else "",
                }
            )
            # Cap version history to prevent Redis OOM
            MAX_VERSIONS = 15
            if len(prev_versions) > MAX_VERSIONS:
                prev_versions = prev_versions[-MAX_VERSIONS:]

        version_number = len(prev_versions) + 1

        last_targets = session.get("last_edited_targets", []) if not is_new else []
        session_data = {
            "html": code["html"],
            "css": code["css"],
            "js": code["js"],
            "plan": plan if is_new else existing.get("plan"),
            "prompts": existing.get("prompts", []) + [req.prompt],
            "versions": prev_versions,
            "current_version": version_number,
            "user_id": user["user_id"],
            "last_edited_targets": last_targets,
        }
        if is_new and is_multipage_gen and pages_dict:
            session_data["multipage"] = True
            session_data["pages"] = {slug: {"html": pd["html"], "css": pd["css"]} for slug, pd in pages_dict.items()}
        elif not is_new and existing.get("multipage"):
            session_data["multipage"] = existing.get("multipage", False)
            session_data["pages"] = existing.get("pages") or {}
            current_page = req.currentPage or "index"
            session_data["pages"][current_page] = {"html": code["html"], "css": code["css"]}
            if current_page != "index":
                index_data = session_data["pages"].get("index")
                if index_data:
                    session_data["html"] = index_data["html"]
                    session_data["css"] = index_data["css"]
        await redis_save_session(session_id, session_data)

        current_plan = plan if is_new else existing.get("plan", {})
        brand_name = (current_plan or {}).get("brand", {}).get("name", "Website")
        meta_desc = (current_plan or {}).get("brand", {}).get("tagline", "")

        generation_ms = round((time.time() - generation_start) * 1000, 2)
        metrics_observe("generation_duration_ms", generation_ms)

        result = {
            "success": True,
            "website": {"html": code["html"], "css": code["css"], "js": code["js"]},
            "sessionId": session_id,
            "isNewDesign": is_new,
            "sections": sections_list,
            "version": version_number,
            "meta": {"title": brand_name, "description": meta_desc},
        }
        if is_new and is_multipage_gen and pages_dict:
            result["isMultipage"] = True
            result["pages"] = {slug: {"html": pd["html"], "css": pd["css"]} for slug, pd in pages_dict.items()}
        return result

    except HTTPException:
        metrics_increment("generation_errors")
        raise
    except CircuitOpenError as e:
        metrics_increment("generation_errors")
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again in a few minutes.",
        ) from e
    except Exception as e:
        metrics_increment("generation_errors")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ═══════════════════════════════════════════════════════════════════════
# ELEMENT EDITING
# ═══════════════════════════════════════════════════════════════════════

ELEMENT_SECTION_EDIT_PROMPT = """You are an expert frontend developer editing a specific element inside a website section.

DESIGN SYSTEM (CSS variables — use these for consistency):
{css_vars}

AVAILABLE CSS CLASSES (pre-defined in the page's <style> block — USE THEM):
Layout: .container, .container-wide, .container-narrow, .container-xs
Grid: .grid-2, .grid-3, .grid-4 (auto-responsive)
Buttons: .btn-primary, .btn-secondary, .btn-group
Cards: .card, .card-title, .card-text, .card-body, .icon-box
Images: .img-cover, .img-wrapper
Section: .section-header, .section-title, .section-subtitle, .text-center, .text-light
Hero: .hero-section, .hero-heading, .hero-subtitle, .hero-split-grid, .hero-ctas, .hero-bg-cover, .hero-overlay
Stats: .stat-item, .stat-number, .stat-label
Forms: .form-input, .contact-form

SECTION CONTAINING THE ELEMENT ({section_type} section):
{section_html}

SELECTED ELEMENT (CSS path: {element_path}):
{element_html}

USER'S EDIT REQUEST: {prompt}

RULES:
- Return ONLY the COMPLETE updated section HTML inside a single ```html code block
- Return the FULL section element (opening tag through closing tag)
- ONLY modify the targeted element — keep everything else unchanged
- Use the CSS classes listed above — NO Tailwind utility classes
- Use CSS variables: var(--accent), var(--bg), var(--radius), etc.
- Keep the same outer section tag and data-section-type / data-section-id attributes
- For images, keep existing src URLs unless user asks to change images
- Do NOT add Font Awesome script tags — icons are already loaded
- Do NOT wrap in extra divs or add <html>/<head>/<body> tags
- Do NOT generate large inline SVGs or decorative clip-path shapes
- Do NOT include any explanation, just the html code block

SECTION SIZE CONSTRAINTS:
- Hero: max height 80vh. NEVER taller than viewport.
- All other sections: keep the same size as original.

IMAGE HANDLING:
- "Add background image" = CSS background-image ONLY (no extra <img> tag)
- NEVER add BOTH a background-image AND a foreground <img> for the same purpose

JS-DEPENDENT CLASS NAMES (do NOT rename — JS will break):
.nav-links, .nav-toggle, .faq-item, .faq-question, .faq-answer,
.testimonial-slide, .slider-dot, .carousel-container, .carousel-track,
.carousel-slide, .carousel-prev, .carousel-next, .carousel-dot,
#gallery-lightbox, .gallery-item, .modal-trigger, .detail-modal,
.modal-close, .stat-number, #year, #back-to-top"""


@router.post("/edit-element")
async def edit_element(req: EditElementRequest, user: dict = Depends(require_auth)):
    logger.info(
        f'🖱️ [ELEMENT EDIT] path="{req.elementPath}" prompt="{req.prompt[:80]}" elementHTML={len(req.elementHtml):,} chars, pageHTML={len(req.currentHtml):,} chars, page={req.currentPage}'
    )

    # ── Sanitize prompt ─────────────────────────────────────────────
    req.prompt = sanitize_prompt(req.prompt)
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # ── Audit log ───────────────────────────────────────────────────
    log_event_bg(
        user_id=str(user["user_id"]),
        action="edit_website",
        resource_type="element",
        resource_id=req.sessionId,
        details={"prompt": req.prompt[:500], "element_path": req.elementPath},
    )

    try:
        full_html = req.currentHtml
        css = req.currentCss
        css_vars = extract_css_vars(css)

        # ── Find which section contains the clicked element ──────
        sections = parse_sections(full_html)
        target_section = None
        for s in sections:
            section_html = full_html[s["start"] : s["end"]]
            if req.elementHtml[:80] in section_html:
                target_section = s
                break

        if not target_section:
            # Fallback: try matching by element path keywords in section types
            for s in sections:
                section_html = full_html[s["start"] : s["end"]]
                # Check if elementPath classes appear in this section
                path_classes = re.findall(r"\.([a-zA-Z][\w-]*)", req.elementPath)
                if any(cls in section_html for cls in path_classes):
                    target_section = s
                    break

        if target_section:
            # ── Section-scoped edit (fast + reliable) ────────────
            section_html = full_html[target_section["start"] : target_section["end"]]
            section_type = target_section["type"]
            section_id = target_section["id"]
            logger.info(
                f'🖱️ [ELEMENT EDIT] Found element in section id="{section_id}" type="{section_type}" ({len(section_html):,} chars)'
            )

            system = ELEMENT_SECTION_EDIT_PROMPT.format(
                css_vars=css_vars,
                section_type=section_type,
                section_html=section_html,
                element_path=req.elementPath,
                element_html=req.elementHtml,
                prompt=req.prompt,
            )
            logger.info(f"🖱️ [ELEMENT EDIT] Prompt: {len(system):,} chars (section-scoped), sending to Claude...")

            client = get_anthropic_client()
            text = await _claude_stream(
                client, "claude-sonnet-4-20250514", 8000, system, f"Edit the element at {req.elementPath}: {req.prompt}"
            )
            logger.info(f"🖱️ [ELEMENT EDIT] Claude response: {len(text):,} chars")

            edited_section = parse_single_code_block(text, "html")
            if not edited_section:
                logger.error(f"🖱️ [ELEMENT EDIT] FAILED — no HTML parsed. Response first 500 chars: {text[:500]}")
                raise HTTPException(status_code=500, detail="Failed to parse edited element")

            logger.info(f"🖱️ [ELEMENT EDIT] Edited section: {len(edited_section):,} chars (was {len(section_html):,})")

            # Patch the edited section back into the full HTML
            result_html = replace_section_html(full_html, section_id, edited_section)
            result_css = css

        else:
            # ── Fallback: full-page edit (for elements outside sections, e.g. nav) ──
            logger.info("🖱️ [ELEMENT EDIT] Element not found in any section — using full-page fallback")

            system = ELEMENT_EDIT_PROMPT.format(
                html=full_html,
                css=css,
                element_path=req.elementPath,
                element_html=req.elementHtml,
                prompt=req.prompt,
            )
            logger.info(f"🖱️ [ELEMENT EDIT] Fallback prompt: {len(system):,} chars, sending to Claude...")

            client = get_anthropic_client()
            text = await _claude_stream(client, "claude-sonnet-4-20250514", 16000, system, req.prompt)
            logger.info(f"🖱️ [ELEMENT EDIT] Claude response: {len(text):,} chars")
            code = parse_code_blocks(text)
            logger.info(f"🖱️ [ELEMENT EDIT] Parsed → html={len(code['html']):,}, css={len(code['css']):,}")

            if not code["html"]:
                logger.error(f"🖱️ [ELEMENT EDIT] FAILED — no HTML parsed. Response first 500 chars: {text[:500]}")
                raise HTTPException(status_code=500, detail="Failed to parse edited code")

            result_html = code["html"]
            result_css = code["css"] if code["css"] else css

            # Extract <style> from HTML if present
            style_match = re.search(r"<style[^>]*>(.*?)</style>", result_html, re.DOTALL)
            if style_match:
                result_css = style_match.group(1).strip()
                result_html = re.sub(r"<style[^>]*>.*?</style>\s*", "", result_html, flags=re.DOTALL).strip()

        # ── Save to session ──────────────────────────────────────
        s = await redis_get_session(req.sessionId) if req.sessionId else None
        if s:
            _verify_session_ownership(s, user)
            versions = s.get("versions", [])
            versions.append(
                {
                    "version": s.get("current_version", 0),
                    "html": s["html"],
                    "css": s["css"],
                    "js": s.get("js", ""),
                    "prompt": f"[Element edit: {req.elementPath}] {req.prompt}",
                }
            )
            # Cap version history
            MAX_VERSIONS = 15
            if len(versions) > MAX_VERSIONS:
                versions = versions[-MAX_VERSIONS:]
            s["versions"] = versions
            s["html"] = result_html
            s["css"] = result_css
            # Multi-page aware: also update the correct page slot
            if s.get("multipage") and req.currentPage:
                if "pages" not in s:
                    s["pages"] = {}
                s["pages"][req.currentPage] = {"html": result_html, "css": result_css}
                if req.currentPage != "index":
                    index_data = s.get("pages", {}).get("index")
                    if index_data:
                        s["html"] = index_data["html"]
                        s["css"] = index_data["css"]
            s["current_version"] = s.get("current_version", 0) + 1
            s["prompts"] = s.get("prompts", []) + [f"[Element: {req.elementPath}] {req.prompt}"]
            await redis_save_session(req.sessionId, s)

        logger.info(f"🖱️ [ELEMENT EDIT] ✅ Done → result_html={len(result_html):,}, result_css={len(result_css):,}")
        return {"success": True, "website": {"html": result_html, "css": result_css}, "manualReplace": False}

    except HTTPException:
        raise
    except CircuitOpenError as e:
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again in a few minutes.",
        ) from e
    except Exception as e:
        logger.error(f"🖱️ [ELEMENT EDIT] Exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ═══════════════════════════════════════════════════════════════════════
# SESSION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.get("/session/{session_id}")
async def get_session_endpoint(session_id: str, user: dict = Depends(require_auth)):
    session = await redis_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_ownership(session, user)
    return {
        "sessionId": session_id,
        "html": session["html"],
        "css": session["css"],
        "js": session.get("js", ""),
        "prompts": session.get("prompts", []),
        "current_version": session.get("current_version", 1),
        "total_versions": len(session.get("versions", [])) + 1,
    }


@router.get("/session/{session_id}/versions")
async def get_session_versions(session_id: str, user: dict = Depends(require_auth)):
    session = await redis_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_ownership(session, user)
    versions = session.get("versions", [])
    all_versions = versions + [
        {
            "version": session.get("current_version", len(versions) + 1),
            "html": session["html"],
            "css": session["css"],
            "js": session.get("js", ""),
            "prompt": session.get("prompts", [""])[-1] if session.get("prompts") else "",
        }
    ]
    return {
        "current_version": session.get("current_version", len(versions) + 1),
        "versions": [{"version": v["version"], "prompt": v.get("prompt", "")} for v in all_versions],
    }


@router.post("/session/{session_id}/rollback/{version}")
async def rollback_session(session_id: str, version: int, user: dict = Depends(require_auth)):
    session = await redis_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_ownership(session, user)
    versions = session.get("versions", [])
    target = next((v for v in versions if v["version"] == version), None)
    if not target:
        raise HTTPException(status_code=404, detail="Version not found")
    versions.append(
        {
            "version": session.get("current_version", 0),
            "html": session["html"],
            "css": session["css"],
            "js": session.get("js", ""),
            "prompt": f"[Before rollback to v{version}]",
        }
    )
    session["html"] = target["html"]
    session["css"] = target["css"]
    session["js"] = target.get("js", "")
    session["current_version"] = version
    await redis_save_session(session_id, session)
    return {
        "success": True,
        "version": version,
        "website": {
            "html": target["html"],
            "css": target["css"],
            "js": target.get("js", ""),
        },
    }


@router.delete("/session/{session_id}")
async def delete_session_endpoint(session_id: str, user: dict = Depends(require_auth)):
    await redis_delete_session(session_id)
    return {"success": True}


@router.get("/niches")
async def get_niches(user: dict = Depends(require_auth)):
    """Return available niche categories."""
    from app.utils.niches import NICHES
    return {
        "niches": [
            {"key": k, "label": k.replace("_", " ").title()}
            for k in NICHES.keys()
        ]
    }


class DesignSystemRequest(BaseModel):
    session_id: str
    updates: dict = {}


@router.post("/design-system")
async def update_design_system(req: DesignSystemRequest, user: dict = Depends(require_auth)):
    """Apply design system changes to session CSS variables."""
    session = await redis_get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_ownership(session, user)

    css = session.get("css", "")
    updates = req.updates or {}

    for var_name, value in updates.get("colors", {}).items():
        css = re.sub(rf"(--{re.escape(var_name)}\s*:)[^;]+;", rf"\1 {value};", css)

    if "heading_font" in updates.get("fonts", {}):
        font = updates["fonts"]["heading_font"]
        css = re.sub(r"(--font-heading\s*:)[^;]+;", f"\\1 '{font}', sans-serif;", css)
    if "body_font" in updates.get("fonts", {}):
        font = updates["fonts"]["body_font"]
        css = re.sub(r"(--font-body\s*:)[^;]+;", f"\\1 '{font}', sans-serif;", css)

    session["css"] = css
    await redis_save_session(req.session_id, session)
    return {"success": True, "css": css}


@router.post("/design-system/generate")
async def generate_design_system(req: DesignSystemRequest, user: dict = Depends(require_auth)):
    """Return current design system from session plan."""
    session = await redis_get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _verify_session_ownership(session, user)
    plan = session.get("plan", {})
    design = plan.get("design", {})
    return {
        "success": True,
        "designSystem": {
            "primary": design.get("primary_color", "#6366f1"),
            "secondary": design.get("secondary_color", "#8b5cf6"),
            "accent": design.get("accent_color", "#a78bfa"),
            "background": design.get("background_color", "#ffffff"),
            "heading_font": design.get("heading_font", "Space Grotesk"),
            "body_font": design.get("body_font", "Inter"),
        }
    }
