"""
Generator routes — 3-stage AI website generation pipeline:

  Stage 1: Plan  → GPT-4.1 → JSON structure + content + layout patterns
  Stage 2: HTML  → LLM    → HTML with pure CSS classes + <style> block
  Stage 3: JS    → LLM    → Interactions/animations

CSS is semantic classes in a <style> block (layout, components, responsive).
"""

import asyncio
import contextvars
import difflib
import json
import logging
import os
import re
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.utils import sanitize_log
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
from app.utils.redis_client import get_redis as get_redis_client
from app.utils.redis_client import update_job
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
from app.utils.token_tracker import check_budget, deduct_tokens

logger = logging.getLogger(__name__)

# Set to prevent premature garbage collection of fire-and-forget tasks
_background_tasks: set = set()

router = APIRouter()

# Context variable to pass user_id into nested functions without changing signatures
_current_user_id: contextvars.ContextVar[int | None] = contextvars.ContextVar("current_user_id", default=None)


async def _track_job(session_id: str, user_id: str, job_type: str = "generate") -> str:
    """Create a lightweight job record for admin visibility (no queue push)."""
    r = await get_redis_client()
    now = time.time()
    job_id = session_id  # Reuse session_id as job_id for easy correlation
    job_data = {
        "id": job_id,
        "type": job_type,
        "status": "processing",
        "payload": "",
        "result": "",
        "error": "",
        "user_id": str(user_id),
        "created_at": now,
        "updated_at": now,
        "progress": 0,
        "progress_message": "Starting...",
    }
    pipe = r.pipeline()
    pipe.hset(f"job:{job_id}", mapping=job_data)
    pipe.expire(f"job:{job_id}", 7200)  # 2h TTL
    await pipe.execute()
    return job_id


async def _update_job_progress(job_id: str, progress: int, message: str):
    """Fire-and-forget job progress update."""
    try:
        await update_job(job_id, progress=progress, progress_message=message, status="processing")
    except Exception:
        pass


async def _complete_job(job_id: str, status: str = "completed", error: str = ""):
    """Mark job as completed or failed."""
    try:
        fields = {"status": status, "progress": 100 if status == "completed" else 0, "progress_message": "Done" if status == "completed" else error}
        if error:
            fields["error"] = error
        await update_job(job_id, **fields)
    except Exception:
        pass


def _deduct_bg(user_id: int, usage: dict, provider: str, model: str, operation: str):
    """Fire-and-forget token deduction."""
    if usage.get("input_tokens") or usage.get("output_tokens"):
        task = asyncio.create_task(deduct_tokens(
            user_id, usage.get("input_tokens", 0), usage.get("output_tokens", 0),
            provider, model, operation
        ))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)


def _log_generation_bg(
    user_id: int,
    prompt: str,
    status: str = "completed",
    session_id: str | None = None,
    html_size: int | None = None,
    duration_ms: int | None = None,
    is_multipage: bool = False,
    page_count: int = 1,
    performance_score: int | None = None,
    seo_score: int | None = None,
    stage_failed: str | None = None,
    error_message: str | None = None,
):
    """Fire-and-forget GenerationLog insert for admin dashboard."""
    import traceback as _tb
    from datetime import UTC as _UTC
    from datetime import datetime as _dt

    from app.database import async_session as _async_session
    from app.models.generation_log import GenerationLog

    async def _insert():
        try:
            from sqlalchemy import update as _update

            from app.models.user import User as _User

            async with _async_session() as session:
                log = GenerationLog(
                    user_id=user_id,
                    session_id=session_id,
                    prompt=prompt[:2000] if prompt else "",
                    status=status,
                    html_size=html_size,
                    duration_ms=duration_ms,
                    is_multipage=is_multipage,
                    page_count=page_count,
                    performance_score=performance_score,
                    seo_score=seo_score,
                    stage_failed=stage_failed,
                    error_message=error_message[:500] if error_message else None,
                    completed_at=_dt.now(_UTC) if status in ("completed", "failed") else None,
                )
                session.add(log)
                # Increment user.generation_count on successful generations
                if status == "completed":
                    await session.execute(
                        _update(_User).where(_User.id == user_id).values(
                            generation_count=_User.generation_count + 1
                        )
                    )
                await session.commit()
        except Exception as e:
            print(f"[GenerationLog] Failed to log ({status}): {e}", flush=True)
            _tb.print_exc()

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_insert())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
    except RuntimeError:
        pass


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
    from app.routes.templates import TEMPLATE_CATALOG, _load_template_file

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
        # Sanitize inputs to prevent path traversal
        safe_session = re.sub(r"[^a-zA-Z0-9_-]", "", session_id[:8])
        safe_stage = re.sub(r"[^a-zA-Z0-9_-]", "", stage)
        debug_dir = os.path.join(DEBUG_DIR, safe_session)
        os.makedirs(debug_dir, exist_ok=True)
        ext = {"plan": "json", "html": "html", "css": "css", "js": "js"}.get(safe_stage, "txt")
        with open(os.path.join(debug_dir, f"{safe_stage}.{ext}"), "w") as f:
            f.write(content)
    except Exception:
        pass  # Debug storage is best-effort


# ═══════════════════════════════════════════════════════════════════════
# CSS POLISH
# ═══════════════════════════════════════════════════════════════════════


def polish_css(css: str, theme: str = "light") -> str:
    """Auto-inject premium CSS polish if missing.

    Covers: scroll behavior, image rendering, selection, focus, transitions,
    font rendering, whitespace enforcement, card hover effects, responsive
    safeguards, section spacing, and image object-fit.
    """
    additions = []

    # ── Core polish ──
    if "scroll-behavior" not in css:
        additions.append("html { scroll-behavior: smooth; }")
    if "image-rendering" not in css:
        additions.append("img { image-rendering: -webkit-optimize-contrast; }")
    if "::selection" not in css:
        additions.append("::selection { background: var(--primary, #3b82f6); color: white; }")
    if ":focus-visible" not in css:
        additions.append(":focus-visible { outline: 2px solid var(--primary, #3b82f6); outline-offset: 2px; }")
    if "-webkit-font-smoothing" not in css:
        additions.append("body { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility; }")

    # ── Quality Improvement 3: CSS post-polish ──

    # Smooth transitions on interactive elements
    if "a, button" not in css:
        additions.append("a, button, input, textarea { transition: all 0.3s ease; }")

    # Quality Improvement 7: Whitespace enforcement — generous section padding
    if "section" not in css or "padding" not in css[:500]:
        additions.append("section { padding: 5rem 0; }")
    # Ensure sections have max-width container
    if "max-width" not in css[:1000]:
        additions.append(".container, .max-w-7xl, .mx-auto { max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }")

    # Quality Improvement 5: Image object-fit enforcement
    if "object-fit" not in css:
        additions.append("img { max-width: 100%; height: auto; }")
    additions.append("img[src*='pexels'], img[src*='unsplash'], img[src*='images.'] { object-fit: cover; }")

    # Card hover effects (if cards exist but no hover)
    if "card" in css.lower() and "card" not in css.split(":hover")[0][-50:] if ":hover" in css else True:
        additions.append("""
[class*="card"]:hover, .card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.12);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}""")

    # Button hover enhancement
    if "btn" in css.lower() and "btn:hover" not in css.lower():
        additions.append("""
[class*="btn"]:hover, button[class]:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}""")

    # ── Quality Improvement 6: Footer colors & links ──
    # Ensure footer text/links are always light (footer always has dark bg)
    additions.append("""
footer, footer[data-section-type], [data-section-type="footer"] {
  color: rgba(255,255,255,0.9) !important;
}
footer h3, footer h4, footer .footer-heading { color: white !important; }
footer p, footer span, footer li { color: rgba(255,255,255,0.7); }
footer a { color: rgba(255,255,255,0.7) !important; transition: color 0.2s, opacity 0.2s; }
footer a:hover { color: white !important; opacity: 1; }
footer .social-links a { color: white !important; }
footer .nav-brand, footer .nav-brand span { color: white !important; }""")

    # ── Responsive safeguards ──
    if "@media" not in css:
        additions.append("""
@media (max-width: 768px) {
  section { padding: 3rem 0; }
  h1 { font-size: 2rem !important; }
  h2 { font-size: 1.5rem !important; }
  .grid { grid-template-columns: 1fr !important; }
}""")

    # Dark theme scrollbar
    if theme == "dark":
        if "scrollbar" not in css:
            additions.append("::-webkit-scrollbar { width: 8px; }")
            additions.append("::-webkit-scrollbar-track { background: var(--bg, #0a0a0f); }")
            additions.append("::-webkit-scrollbar-thumb { background: var(--primary, #3b82f6); border-radius: 4px; }")

    # ── Section visual rhythm: alternating backgrounds (exclude footer) ──
    if "nth-child" not in css and "section:nth" not in css:
        if theme == "dark":
            additions.append("section:nth-child(even):not([data-section-type='footer']):not(footer) { background: rgba(255,255,255,0.02); }")
        else:
            additions.append("section:nth-child(even):not([data-section-type='footer']):not(footer) { background: rgba(0,0,0,0.015); }")

    if additions:
        polish = "\n/* === Auto-polish === */\n" + "\n".join(additions) + "\n"
        css = css.rstrip() + "\n" + polish

    return css


# ═══════════════════════════════════════════════════════════════════════
# IMAGE SAFETY
# ═══════════════════════════════════════════════════════════════════════


def _convert_hallucinated_urls_to_placeholders(html: str) -> str:
    """Convert hallucinated Pexels/Unsplash URLs to {{IMG:}} placeholders.

    The model sometimes ignores the {{IMG:}} instruction and generates fake
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


def _fix_url_quotes(html: str) -> str:
    """Normalize all url() with http/https or {{IMG:}} URLs to use single quotes.

    LLMs frequently generate mismatched quotes like url("https://...') or url("https://...")
    inside style="" attributes.  The double quote prematurely closes the attribute.
    This function finds all url(...) containing http URLs and rewrites them to url('...').

    Does NOT touch url("data:...") since SVG data URIs may contain single quotes.
    """
    def _normalize_url(m: re.Match) -> str:
        inner = m.group(1)
        # Strip any leading/trailing quotes (single or double, possibly mismatched)
        inner = inner.strip("\"'")
        return f"url('{inner}')"

    # Match url(...) containing http:// or https:// or {{IMG:
    # The inner part can have any quote combination (or none)
    html = re.sub(
        r"""url\(\s*["']?(https?://[^)'"]*?)["']?\s*\)""",
        _normalize_url,
        html,
    )
    html = re.sub(
        r"""url\(\s*["']?(\{\{IMG:[^)'"]*?)["']?\s*\)""",
        _normalize_url,
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


def _apply_user_images(html: str, user_images: list[dict] | None) -> str:
    """Replace {{IMG:...}} placeholders with user-assigned images based on section mapping.

    user_images: list of {url, section, filename} dicts.
    section values: "hero", "about", "services", "gallery", "team", etc.
    """
    if not user_images:
        return html

    # Build section → URL mapping
    section_map = {}
    gallery_images = []
    unassigned = []
    for img in user_images:
        section = (img.get("section") or "").lower().strip()
        url = img.get("url", "")
        if not url:
            continue
        if section == "gallery":
            gallery_images.append(url)
        elif section:
            section_map[section] = url
        else:
            unassigned.append(url)

    if not section_map and not gallery_images and not unassigned:
        return html

    used_unassigned = 0

    def _replace_placeholder(match):
        nonlocal used_unassigned
        query = match.group(1).lower()

        # Try matching section keywords in the placeholder query
        for section_key, url in section_map.items():
            if section_key in query:
                return url

        # Use unassigned images for remaining placeholders
        if used_unassigned < len(unassigned):
            url = unassigned[used_unassigned]
            used_unassigned += 1
            return url

        # No user image available — keep placeholder for stock photo resolution
        return match.group(0)

    html = re.sub(r'\{\{IMG:([^}]+)\}\}', _replace_placeholder, html)

    # Inject gallery images into gallery section if any
    if gallery_images:
        gallery_match = re.search(
            r'(<section[^>]*data-section-type="gallery"[^>]*>)(.*?)(</section>)',
            html, re.DOTALL
        )
        if gallery_match:
            gallery_html = gallery_match.group(2)
            # Find existing img tags in gallery and append user images
            for gimg_url in gallery_images:
                img_tag = f'<img src="{gimg_url}" alt="Gallery" class="img-cover gallery-image" loading="lazy" decoding="async">'
                # Insert before closing grid div or at end of gallery content
                grid_match = re.search(r'(</div>\s*</div>\s*$)', gallery_html)
                if grid_match:
                    gallery_html = gallery_html[:grid_match.start()] + f'\n<div class="gallery-item" data-aos="zoom-in">{img_tag}</div>\n' + gallery_html[grid_match.start():]
            html = html[:gallery_match.start(2)] + gallery_html + html[gallery_match.end(2):]

    return html


def _ensure_hero_has_image(html: str, niche_key: str = None) -> str:
    """Pre-resolution check: if hero section has no {{IMG:}} placeholder or background-image url(),
    inject one so the image resolver can find a proper niche-appropriate image."""
    # Try data-section-type="hero" first, then fall back to class-based or id-based hero detection
    hero_match = re.search(
        r'(<section[^>]*data-section-type="hero"[^>]*>)(.*?)(</section>)',
        html, re.DOTALL
    )
    if not hero_match:
        # Fallback: detect hero by class name or id (LLM may omit data-section-type on subpages)
        hero_match = re.search(
            r'(<section[^>]*(?:class="[^"]*hero[^"]*"|id="hero")[^>]*>)(.*?)(</section>)',
            html, re.DOTALL | re.IGNORECASE
        )
    if not hero_match:
        # Last resort: first <section> after navbar (common pattern — hero is always first content section)
        hero_match = re.search(
            r'(?:</nav>|</header>)\s*(<section[^>]*>)(.*?)(</section>)',
            html, re.DOTALL | re.IGNORECASE
        )
    if not hero_match:
        return html

    hero_tag = hero_match.group(1)
    hero_content = hero_match.group(2)
    hero_full = hero_tag + hero_content

    # Check if hero already has an image (placeholder or real URL)
    has_image = bool(re.search(r'\{\{IMG:|background[^;]*url\(|<img\s[^>]*src\s*=', hero_full, re.IGNORECASE))
    if has_image:
        return html

    # No image found — inject background-image with {{IMG:}} placeholder
    niche_desc = (niche_key or "professional business").replace("_", " ")
    bg_with_image = f"background:linear-gradient(135deg,rgba(10,10,20,0.75),rgba(20,20,40,0.8)),url('{{{{IMG:{niche_desc} hero background professional}}}}');background-size:cover;background-position:center;"

    if 'style="' in hero_tag:
        # Replace any existing background/background-color property to avoid conflicts
        existing_style = re.search(r'style="([^"]*)"', hero_tag)
        if existing_style:
            old_style = existing_style.group(1)
            # Remove existing background properties that would conflict
            cleaned = re.sub(r'background(?:-color|-image|-size|-position)?:\s*[^;]+;?\s*', '', old_style)
            new_style = bg_with_image + cleaned
            new_tag = hero_tag[:existing_style.start()] + f'style="{new_style}"' + hero_tag[existing_style.end():]
        else:
            new_tag = hero_tag.replace('style="', f'style="{bg_with_image}')
    else:
        new_tag = hero_tag[:-1] + f' style="{bg_with_image}">'

    html = html[:hero_match.start(1)] + new_tag + html[hero_match.end(1):]
    logger.info(f"[HERO IMAGE] Injected {{{{IMG:}}}} placeholder for missing hero background (niche={niche_key})")
    return html


async def _resolve_images_safe(html: str, niche_key: str = None, user_images: list[dict] | None = None) -> str:
    """Resolve image placeholders with safety cleanup for any unresolved ones."""
    # First: ensure hero has a background image (inject {{IMG:}} if missing)
    html = _ensure_hero_has_image(html, niche_key)

    # Apply user-assigned images
    html = _apply_user_images(html, user_images)

    # Then: convert any hallucinated Pexels/Unsplash URLs to {{IMG:}} placeholders
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

    # Fix url() quotes — must run AFTER image resolution since LLM and resolver
    # may produce url("https://...") which breaks inside style="" attributes.
    # Normalize ALL url() with http/https URLs to use single quotes consistently.
    html = _fix_url_quotes(html)

    return html


# ═══════════════════════════════════════════════════════════════════════
# OUTPUT VALIDATORS
# ═══════════════════════════════════════════════════════════════════════


def validate_html(html: str) -> str:
    """Validate HTML output meets minimum quality."""
    # Strip any code fence markers the LLM may have left
    html = re.sub(r"^```\w*\s*\n?", "", html.strip())
    html = re.sub(r"\n?```\s*$", "", html.strip())

    # Strip orphaned comment closers (-->) that leak into visible output
    # These appear when an edit deletes the opening <!-- but leaves the -->
    html = re.sub(r'(?<![->])\s*-->\s*(?=<|\s*$)', '', html)

    # Fix url() quotes — CRITICAL for hero background images.
    html = _fix_url_quotes(html)

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

    # Fix common layout issues that hide footer:
    # 1. Remove overflow:hidden from body/html/main wrappers (clips footer off-screen)
    # 2. Remove height:100vh from body/html (prevents scrolling to footer)
    html = re.sub(
        r'(<(?:body|html)[^>]*style="[^"]*)\boverflow\s*:\s*hidden\b',
        r'\1overflow:visible',
        html,
        flags=re.IGNORECASE,
    )
    # Fix any wrapper div that has both height:100vh and overflow:hidden
    html = re.sub(
        r'(style="[^"]*height\s*:\s*100vh[^"]*)\boverflow\s*:\s*hidden\b',
        r'\1overflow:visible',
        html,
        flags=re.IGNORECASE,
    )
    # Ensure <style> block doesn't have body { height: 100vh; overflow: hidden }
    def _fix_body_css(m):
        block = m.group(0)
        # Remove overflow:hidden from body/html rules
        block = re.sub(r'((?:body|html)\s*\{[^}]*)\boverflow\s*:\s*hidden\b', r'\1overflow-x:hidden', block)
        # Change body height:100vh to min-height:100vh (negative lookbehind to avoid min-height → min-min-height)
        block = re.sub(r'(body\s*\{[^}]*)(?<!min-)height\s*:\s*100vh\b', r'\1min-height:100vh', block)
        return block
    html = re.sub(r'<style[^>]*>.*?</style>', _fix_body_css, html, flags=re.DOTALL)

    # Ensure footer has dark background (LLM sometimes forgets)
    # Match both <section data-section-type="footer"> and <footer data-section-type="footer">
    footer_match = re.search(r'<(?:section|footer)([^>]*data-section-type="footer"[^>]*)>', html)
    if footer_match:
        attrs = footer_match.group(1)
        # Check if footer tag itself already has a dark bg
        section_has_bg = (
            "background" in attrs
            or "bg-[#" in attrs
            or "bg-gray-9" in attrs
            or "bg-black" in attrs
            or "bg-slate-9" in attrs
        )
        # Also check if an inner div right after the footer tag has a dark bg class
        inner_div_match = re.search(
            r'<(?:section|footer)[^>]*data-section-type="footer"[^>]*>\s*<div([^>]*)>',
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
                tag = footer_match.group(0)
                tag_name = "footer" if tag.startswith("<footer") else "section"
                html = html.replace(
                    tag,
                    f'<{tag_name}{attrs} style="background:#1a1a2e">',
                )
            logger.info("🔧 Footer Fix → Added dark background to footer section")

    # Ensure mobile hamburger menu CSS is present (LLM often writes .nav-links { display: none } but forgets .active state)
    if ".nav-links" in html and ".nav-links.active" not in html:
        mobile_menu_css = """<style>
@media (max-width: 768px) {
  .nav-links.active { display: flex !important; position: fixed; top: 70px; left: 0; right: 0; flex-direction: column; padding: 1.5rem 2rem; gap: 1.25rem; z-index: 999; background: var(--bg, #fff); backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0,0,0,0.15); }
  .nav-toggle { display: flex !important; }
}
</style>"""
        if "</head>" in html:
            html = html.replace("</head>", f"{mobile_menu_css}\n</head>", 1)
        elif "</style>" in html:
            # Inject before the closing of the first style block
            html = html.replace("</style>", f"</style>\n{mobile_menu_css}", 1)
        logger.info("🔧 Mobile Nav Fix → Injected .nav-links.active CSS")

    # ── Hero split-grid fix: detect empty image column ──────────────────
    # If hero uses hero-split-grid but the image column has no <img> tag,
    # the left/right side will be empty (wasted space). Convert to centered.
    hero_section_match = re.search(
        r'(<section[^>]*data-section-type="hero"[^>]*>)(.*?)(</section>)',
        html, re.DOTALL
    )
    if hero_section_match:
        hero_inner = hero_section_match.group(2)
        has_split_grid = "hero-split-grid" in hero_inner
        has_img = "<img" in hero_inner
        has_bg_cover = "hero-bg-cover" in hero_inner
        # If split grid but no image at all → convert to centered layout
        if has_split_grid and not has_img and not has_bg_cover:
            logger.info("🔧 Hero Fix → hero-split-grid has no image, converting to centered layout")
            # Remove the split-grid class and convert to centered
            hero_inner = hero_inner.replace("hero-split-grid", "")
            hero_inner = hero_inner.replace("hero-split-asymmetric", "")
            # Find the content div and add hero-center-content
            hero_inner = re.sub(
                r'<div([^>]*class="[^"]*container[^"]*"[^>]*)>',
                lambda m: m.group(0).replace('class="', 'class="hero-center-content ') if 'hero-center-content' not in m.group(0) else m.group(0),
                hero_inner,
                count=1
            )
            # Remove empty hero-image-wrapper divs
            hero_inner = re.sub(
                r'<div[^>]*class="[^"]*hero-image-wrapper[^"]*"[^>]*>\s*</div>',
                '',
                hero_inner,
                flags=re.DOTALL
            )
            # Also remove floating cards that reference missing images
            hero_inner = re.sub(
                r'<div[^>]*class="[^"]*floating-card[^"]*"[^>]*>.*?</div>\s*</div>',
                '',
                hero_inner,
                flags=re.DOTALL
            )
            html = html[:hero_section_match.start(2)] + hero_inner + html[hero_section_match.end(2):]
            logger.info("🔧 Hero Fix → Converted empty split-grid hero to centered layout")

    # ── Hero class enforcement: fix invented class names ──────────────────
    # LLM often invents classes like .hero-content, .hero-buttons instead of framework ones.
    # Enforce proper alignment classes so the CSS framework works correctly.
    hero_match = re.search(
        r'(<section[^>]*data-section-type="hero"[^>]*>)(.*?)(</section>)',
        html, re.DOTALL
    )
    if hero_match:
        hero_html = hero_match.group(2)
        hero_changed = False

        # Detect if hero already has proper alignment class
        has_center = "hero-center-content" in hero_html
        has_left = "hero-full-overlay" in hero_html

        if not has_center and not has_left:
            # Find the main content wrapper inside hero (first div inside container)
            # Common invented names: hero-content, hero-text, hero-wrapper, hero-inner
            def _fix_hero_wrapper(m_inner):
                tag = m_inner.group(0)
                classes = m_inner.group(1) or ""
                # Default to centered alignment for heroes
                if "hero-center-content" not in classes and "hero-full-overlay" not in classes:
                    if 'class="' in tag:
                        tag = tag.replace('class="', 'class="hero-center-content ', 1)
                    else:
                        tag = tag.replace('>', ' class="hero-center-content">', 1)
                return tag

            # Match the content wrapper: a div inside container that holds heading/subtitle
            # Pattern: div with hero-related class OR first div after container
            hero_html_new = re.sub(
                r'<div[^>]*class="([^"]*(?:hero-content|hero-text|hero-wrapper|hero-inner|hero-body)[^"]*)"[^>]*>',
                _fix_hero_wrapper,
                hero_html,
                count=1
            )
            if hero_html_new != hero_html:
                hero_html = hero_html_new
                hero_changed = True

            # If no common wrapper class found, try to add to the first div inside container
            if not hero_changed and "hero-center-content" not in hero_html:
                hero_html_new = re.sub(
                    r'(<div[^>]*class="container[^"]*"[^>]*>\s*)<div([^>]*)>',
                    lambda m2: m2.group(1) + '<div' + (
                        m2.group(2).replace('class="', 'class="hero-center-content ')
                        if 'class="' in m2.group(2)
                        else m2.group(2) + ' class="hero-center-content"'
                    ) + '>',
                    hero_html,
                    count=1
                )
                if hero_html_new != hero_html:
                    hero_html = hero_html_new
                    hero_changed = True

        # Fix invented button wrapper class: hero-buttons → hero-ctas
        if "hero-buttons" in hero_html and "hero-ctas" not in hero_html:
            hero_html = hero_html.replace("hero-buttons", "hero-ctas")
            hero_changed = True

        if hero_changed:
            html = html[:hero_match.start(2)] + hero_html + html[hero_match.end(2):]
            logger.info("🔧 Hero Fix → Enforced alignment classes (hero-center-content/hero-ctas)")

    # Fix hero-subtitle alignment: ensure margin auto when max-width is set
    def _fix_hero_subtitle(m):
        block = m.group(0)
        # Add margin auto to hero-subtitle if it has max-width but no margin auto
        if ".hero-subtitle" in block and "max-width" in block:
            block = re.sub(
                r'(\.hero-subtitle\s*\{[^}]*max-width\s*:[^;]+;)',
                lambda sub: sub.group(0) + ' margin-left: auto; margin-right: auto;'
                if 'margin-left' not in sub.group(0) and 'margin: 0 auto' not in sub.group(0)
                else sub.group(0),
                block,
            )
        # Fix hero overlays that are too dark (>0.55 opacity)
        def _lighten_overlay(sub):
            val_str = sub.group(1)  # e.g. "7" for 0.7, "65" for 0.65
            # Normalize to hundredths: "7" → 70, "65" → 65
            hundredths = int(val_str) * (10 if len(val_str) == 1 else 1)
            new_val = max(35, hundredths - 15)  # reduce by 0.15
            # Format back: 50 → "5", 45 → "45"
            return f'rgba(0,0,0,0.{new_val if new_val % 10 else new_val // 10})'
        block = re.sub(
            r'rgba\(0\s*,\s*0\s*,\s*0\s*,\s*0\.([6-9]\d*)\)',
            _lighten_overlay,
            block,
        )
        return block
    html = re.sub(r'<style[^>]*>.*?</style>', _fix_hero_subtitle, html, flags=re.DOTALL)

    # ── Force hero navbar clearance: inject padding override ──────────────
    # LLM often overrides hero padding with smaller values, causing text to hide under navbar.
    # This is a bulletproof fix: inject a CSS rule that FORCES minimum padding-top on hero.
    hero_padding_fix = '\n/* Hero navbar clearance fix */\nsection[data-section-type="hero"]:not(.hero-section-flush) { padding-top: 10rem !important; }\nsection[data-section-type="hero"].hero-section-flush .hero-bg-cover { padding-top: 100px !important; }\nsection[data-section-type="hero"].hero-section-flush .hero-animated-bg { padding-top: 100px !important; }\n/* Hero split-grid: if image column is empty, let text take full width */\n.hero-split-grid > div:only-child { grid-column: 1 / -1; text-align: center; max-width: 800px; margin: 0 auto; }\n.hero-split-grid > .hero-image-wrapper:empty { display: none; }\n.hero-split-grid > .hero-image-wrapper:not(:has(img)) { display: none; }\n'
    if "</style>" in html:
        # Insert before the LAST </style> tag
        last_style_pos = html.rfind("</style>")
        html = html[:last_style_pos] + hero_padding_fix + html[last_style_pos:]
        logger.info("🔧 Hero Padding Fix → Injected navbar clearance CSS override")

    # Ensure WhatsApp float button is present on every generated page
    if "whatsapp-float" not in html and "wa.me" not in html:
        whatsapp_btn = '<a href="https://wa.me/971XXXXXXXXX" target="_blank" rel="noopener" class="whatsapp-float" style="position:fixed;bottom:1.5rem;right:1.5rem;width:3.5rem;height:3.5rem;background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:1.5rem;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:50;transition:transform 0.3s;text-decoration:none" aria-label="Chat on WhatsApp"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.612.638l4.716-1.244A11.944 11.944 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.143 0-4.144-.663-5.795-1.796l-.404-.282-3.14.828.843-3.076-.309-.444A9.96 9.96 0 012 12C2 6.486 6.486 2 12 2s10 4.486 10 10-4.486 10-10 10z"/></svg></a>'
        if "</body>" in html:
            html = html.replace("</body>", f"\n{whatsapp_btn}\n</body>")
        else:
            html += f"\n{whatsapp_btn}\n"
        logger.info("🔧 WhatsApp Fix → Injected WhatsApp float button")

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
    # Strip verbose comments to reduce size
    if len(js) > 20000:
        js = re.sub(r'^\s*//[^\n]*\n', '', js, flags=re.MULTILINE)  # single-line comments
        js = re.sub(r'/\*[\s\S]*?\*/', '', js)  # block comments
        js = re.sub(r'\n{3,}', '\n\n', js)  # collapse blank lines
        logger.warning(f"[validate_js] JS was oversized, stripped comments → {len(js):,} chars")
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

    # Note: bracket auto-closing removed — it produced invalid JS (}})); garbage).
    # Instead, the form handler is now injected as a separate <script> tag in HTML,
    # so LLM JS syntax errors don't affect it.

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
# LLM STREAMING HELPER
# ═══════════════════════════════════════════════════════════════════════


async def _llm_stream(client, model: str, max_tokens: int, system: str, user_msg: str, retries: int = 2, temperature: float = 0.5, use_prompt_cache: bool = False) -> tuple[str, dict]:
    """Call LLM with streaming. Returns (text, {"input_tokens": N, "output_tokens": N}).

    If use_prompt_cache=True, the system prompt is sent with cache_control
    so the API caches the large static prefix across calls (~90% faster on cache hit).
    """

    @circuit_protected(provider="anthropic")
    async def _inner_call():
        collected = []
        usage = {"input_tokens": 0, "output_tokens": 0}

        # Build system param — use cache_control for large prompts
        if use_prompt_cache:
            system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        else:
            system_param = system

        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_param,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            async for text in stream.text_stream:
                collected.append(text)
            # Get final message for usage stats
            try:
                final = await stream.get_final_message()
                usage["input_tokens"] = final.usage.input_tokens
                usage["output_tokens"] = final.usage.output_tokens
            except Exception:
                pass
        result = "".join(collected)
        if not result.strip():
            raise ValueError("Empty response from LLM")
        return result, usage

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            result_text, usage = await _inner_call()
            # Auto-deduct tokens via contextvar
            uid = _current_user_id.get()
            if uid:
                _deduct_bg(uid, usage, "anthropic", model, "llm_stream")
            return result_text, usage
        except CircuitOpenError:
            raise  # Don't retry if circuit is open
        except Exception as e:
            last_error = e
            is_rate_limit = "429" in str(e) or "rate_limit" in str(e).lower()
            if attempt < retries:
                wait = 30 if is_rate_limit else 2
                logger.warning(f"[RETRY] LLM attempt {attempt} failed: {e} — waiting {wait}s")
                await asyncio.sleep(wait)
            else:
                logger.error(f"[RETRY] LLM exhausted after {retries} attempts: {e}")
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
        # Track token usage
        uid = _current_user_id.get()
        if uid and response.usage:
            _deduct_bg(uid, {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens}, "openai", "gpt-4.1-mini", "enhance")
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
    _hero_variants = ["hero_split", "hero_center", "hero_full_image", "hero_asymmetric"]
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

    plan_max_tokens = 12000 if multipage else 4000

    @circuit_protected(provider="openai")
    async def _call_openai_plan():
        response = await client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.7,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=plan_max_tokens,
        )
        # Track token usage
        uid = _current_user_id.get()
        if uid and response.usage:
            _deduct_bg(uid, {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens}, "openai", "gpt-4.1", "plan")
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
        # Clamp page count to 5 (Home + 4 subpages max — quality drops with too many)
        if len(plan["pages"]) > 5:
            logger.info(f"[PLAN] trimmed pages: {len(plan['pages'])} → 5")
            plan["pages"] = plan["pages"][:5]

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
# STAGE 2: HTML Generation (LLM → HTML only)
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

    text, _usage = await _llm_stream(
        client,
        "claude-sonnet-4-20250514",
        28000,
        system,
        "Generate the HTML markup for this website using the specified layout patterns. Return only the html code block.",
        use_prompt_cache=True,
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
    template HTML (~30K) with a short customization prompt (~5K). The model modifies
    the proven structure rather than building from zero.
    """
    from app.utils.prompt_pipeline import build_template_customize_prompt

    logger.info("🚀 Stage 2: HTML → Template-first customization (faster path)")
    t0 = time.time()
    client = get_anthropic_client()

    system = build_template_customize_prompt(template_html, plan)
    logger.info(f"⚙️ Template Customize Prompt → {len(system):,} chars (vs ~72K for from-scratch)")

    text, _usage = await _llm_stream(
        client,
        "claude-sonnet-4-20250514",
        28000,
        system,
        "Customize this template for the business described in the plan. Return the complete HTML.",
        use_prompt_cache=True,
    )

    html = parse_single_code_block(text, "html")
    html = validate_html(html)

    # Ensure data-section-type attributes exist (post-process if the model missed some)
    html = _ensure_section_types(html)
    html = _ensure_section_ids(html)

    html_duration = int((time.time() - t0) * 1000)
    n_sections = html.count("data-section-type")
    log_stage("HTML-TEMPLATE", html_duration, len(html), True, f"{n_sections} sections (template-customized)")
    logger.info(f"✅ HTML Generated (template path) → {len(html):,} chars with {n_sections} sections in {_fmt_duration(html_duration)}")

    # Resolve {{IMG:query}} placeholders to real image URLs (niche-aware)
    img_count = html.count("{{IMG:")
    # Also handle any REPLACE_ME markers that the model didn't convert
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


def _ensure_section_ids(html: str) -> str:
    """Post-process: add id=TYPE to sections with data-section-type but no id, so navbar anchors work."""
    import re

    def _add_id(match):
        tag = match.group(0)
        section_type = match.group(1)
        # Already has an id attribute — don't override
        if re.search(r'\bid\s*=', tag):
            return tag
        # Insert id before the closing >
        return tag[:-1] + f' id="{section_type}">'

    return re.sub(r'<section[^>]*data-section-type="(\w+)"[^>]*>', _add_id, html)


def extract_style_block(html: str) -> tuple[str, str]:
    """Extract ALL <style> blocks from HTML, merge them, return (css, html_without_styles).

    The HTML stage now outputs a <style> block + body content.
    We extract the <style> contents into the css field so the frontend
    can inject it into <head> as before.
    """
    import re

    matches = list(re.finditer(r"<style[^>]*>(.*?)</style>", html, re.DOTALL))
    if not matches:
        return "", html

    # Merge all style blocks
    css_parts = [m.group(1).strip() for m in matches]
    css = "\n\n".join(css_parts)

    # Remove all style blocks from HTML
    html_clean = html
    for m in reversed(matches):  # reverse to preserve offsets
        html_clean = html_clean[:m.start()] + html_clean[m.end():]
    html_clean = html_clean.strip()

    return css, html_clean


# ═══════════════════════════════════════════════════════════════════════
# STAGE 3: JS Generation (LLM → JS only)
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
    logger.info(f"⚙️ JS Prompt Built → {len(system):,} chars, sending to LLM...")

    text, _usage = await _llm_stream(
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
# COMBINED HTML + JS GENERATION (Single LLM Call — saves 5-10s)
# ═══════════════════════════════════════════════════════════════════════


async def stage_2_html_and_js(
    plan: dict, session_id: str = "", niche_key: str = None,
    reference_html: str = None, enhanced_brief: str = None,
    use_template: bool = False, template_html: str = None,
) -> tuple[str, str]:
    """Generate HTML AND JS in a single LLM call — eliminates the separate JS round-trip.

    Returns (html_with_images_resolved, js).
    Saves ~5-10 seconds by merging two sequential LLM calls into one.
    """
    from app.utils.prompt_pipeline import build_template_customize_prompt

    logger.info("🚀 Stage 2+3 COMBINED: HTML+JS → Single LLM call")
    t0 = time.time()
    client = get_anthropic_client()

    # Build the HTML system prompt (same as stage_2_html)
    if use_template and template_html:
        system = build_template_customize_prompt(template_html, plan)
        logger.info(f"⚙️ Template Customize Prompt → {len(system):,} chars")
    else:
        system = build_html_prompt(plan, enhanced_brief=enhanced_brief)
        if reference_html:
            import re as _re
            root_match = _re.search(r':root\s*\{[^}]+\}', reference_html)
            if root_match:
                ref_css_vars = root_match.group(0)
                system += f"""

REFERENCE DESIGN SYSTEM (use as quality inspiration — adapt colors/spacing to the plan above):
{ref_css_vars}
Study this reference's design quality: variable naming, spacing values, shadow depths, and transitions. Apply similar polish to the generated HTML.
"""
        logger.info(f"⚙️ HTML+JS Combined Prompt → {len(system):,} chars")

    # Append JS generation instructions to the same system prompt
    system += """

═══════════════════════════════════════════════════════════════
JAVASCRIPT GENERATION — include AFTER the HTML code block
═══════════════════════════════════════════════════════════════

After the ```html code block, output a SECOND code block: ```js
This JS block must contain vanilla JavaScript for all interactions:
- Mobile hamburger: querySelector('.nav-toggle') toggles 'active' on querySelector('.nav-links'). Button already exists in HTML.
- Close mobile menu on nav link click
- Smooth scroll for anchor links (skip bare "#" — only scroll to "#section-name" links)
- Sticky/transparent navbar on scroll (add class 'nav-scrolled')
- FAQ accordion (.faq-item toggle 'active' on .faq-question click)
- Counter animation (.stat-number — parse number, animate from 0, preserve suffix +/%/M/K)
- Testimonial slider (.slider-dot shows matching .testimonial-slide, auto-advance 5s)
- Image carousel (.carousel-container — prev/next/dots, auto-advance 5s, pause on hover)
- Gallery lightbox (#gallery-lightbox — click img to open, close/prev/next, keyboard nav)
- Service modals (.modal-trigger → data-modal → 'active' class, close on backdrop/Escape)
- Typed.js hero (.typed-text with data-typed — only if typeof Typed !== 'undefined')
- Newsletter form (.newsletter-form — preventDefault, inline success message, no alert())
- Logo carousel (.logo-carousel-track — duplicate children for seamless loop)
- Back-to-top (#back-to-top — show when scrollY > 300, smooth scroll to top)
- Search bar (.search-toggle → toggle .search-dropdown, close on outside click/Escape)
- Vanilla-tilt ([data-tilt] — only if typeof VanillaTilt !== 'undefined')
- tsParticles (#tsparticles — only if typeof tsParticles !== 'undefined')
- Splitting.js ([data-splitting] — only if typeof Splitting !== 'undefined')
- Lenis smooth scroll (only if typeof Lenis !== 'undefined')
- Section scroll reveal: IntersectionObserver on all <section> — add 'visible' class (threshold 0.1)
- Staggered grid reveals: '[data-section-type] .grid > *' — transitionDelay = (index % 3) * 120 + 'ms'
- Hero stagger entrance: add 'visible' to hero section immediately
- Active nav highlighting on scroll
- Set footer year: document.getElementById('year').textContent = new Date().getFullYear()

JS RULES:
- IIFE wrapper: (function() { ... })();
- CRITICAL: NO template literals (backticks) — use string concatenation only
- Vanilla JS only, no frameworks. Use const/let/arrow functions.
- Do NOT wrap in DOMContentLoaded — runs inline at bottom of body
- Only implement behaviors for sections that ACTUALLY exist in the HTML above — skip any feature whose selectors don't match
- KEEP JS CONCISE: aim for under 8,000 characters total. Combine similar handlers, avoid verbose comments, use short variable names. Do NOT generate boilerplate for features not present in the HTML.
"""

    text, _usage = await _llm_stream(
        client,
        "claude-sonnet-4-20250514",
        28000,
        system,
        "Generate the complete HTML markup AND JavaScript. Return TWO code blocks: first ```html then ```js. Keep JS concise — only implement interactions for elements that exist in the HTML.",
        use_prompt_cache=True,
    )

    # Parse both code blocks from the response
    html_raw = parse_single_code_block(text, "html")
    js_raw = parse_single_code_block(text, "js")

    html = validate_html(html_raw)
    js = validate_js(js_raw) if js_raw else ""

    combined_duration = int((time.time() - t0) * 1000)
    n_sections = html.count("data-section-type")
    log_stage("HTML+JS-COMBINED", combined_duration, len(html) + len(js), True,
              f"{n_sections} sections, {len(js):,} chars JS")
    logger.info(
        f"✅ HTML+JS Combined → {len(html):,} chars HTML + {len(js):,} chars JS "
        f"with {n_sections} sections in {_fmt_duration(combined_duration)}"
    )

    if use_template and template_html:
        html = _ensure_section_types(html)
    html = _ensure_section_ids(html)

    # Resolve images (can run while we return)
    img_count = html.count("{{IMG:")
    replace_me_count = html.count('src="REPLACE_ME"')
    if replace_me_count > 0:
        html = html.replace('src="REPLACE_ME"', 'src="{{IMG:feature placeholder}}"')
        img_count = html.count("{{IMG:")

    logger.info(f"🖼️ Resolving Images → {img_count} placeholders (niche={niche_key or 'general'})")
    html = await _resolve_images_safe(html, niche_key=niche_key)
    logger.info("✅ Images Resolved → all placeholders replaced with real URLs")

    save_debug(session_id, "html", html)
    save_debug(session_id, "js", js)

    # If JS extraction failed, fall back to separate stage_3_js call
    if not js.strip():
        logger.warning("⚠️ Combined call produced no JS — falling back to separate stage_3_js")
        js = await stage_3_js(html, session_id)

    return html, js


# ═══════════════════════════════════════════════════════════════════════
# MULTI-PAGE HTML GENERATION
# ═══════════════════════════════════════════════════════════════════════


# WhatsApp float HTML snippet to inject on every page
_WHATSAPP_FLOAT_HTML = """<a href="https://wa.me/971XXXXXXXXX" target="_blank" rel="noopener" class="whatsapp-float" style="position:fixed;bottom:1.5rem;right:1.5rem;width:3.5rem;height:3.5rem;background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:1.5rem;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:50;transition:transform 0.3s;text-decoration:none" aria-label="Chat on WhatsApp"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.612.638l4.716-1.244A11.944 11.944 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.143 0-4.144-.663-5.795-1.796l-.404-.282-3.14.828.843-3.076-.309-.444A9.96 9.96 0 012 12C2 6.486 6.486 2 12 2s10 4.486 10 10-4.486 10-10 10z"/></svg></a>"""


def _convert_anchor_links_to_page_hrefs(pages_html: dict) -> dict:
    """Convert anchor links (#contact, #booking, etc.) to actual page hrefs in multipage sites.

    CTA buttons like 'Book Now' or 'Contact Us' often use href="#contact" or href="#booking".
    In multipage sites these anchors don't work because the target section is on a different page.
    This converts them to proper page links (e.g. /contact.html, /booking.html) when a matching page exists.
    """
    page_slugs = set(pages_html.keys())
    # Build mapping: anchor fragment → page href (e.g. "contact" → "/contact.html")
    # Also map common CTA anchor variants to their likely page
    slug_map = {}
    for slug in page_slugs:
        if slug == "index":
            continue
        slug_map[slug] = f"/{slug}.html"
        # Map common variants: "book-now" → "booking", "get-started" → "services", etc.
        slug_map[slug.replace("-", "")] = f"/{slug}.html"

    # Common CTA anchor → page mappings
    cta_to_page = {
        "book": "booking", "book-now": "booking", "booknow": "booking",
        "reserve": "booking", "reservation": "booking", "reservations": "booking",
        "appointment": "booking", "schedule": "booking",
        "contact": "contact", "contact-us": "contact", "contactus": "contact",
        "get-in-touch": "contact", "reach-us": "contact",
        "get-started": "contact", "getstarted": "contact",
        "pricing": "pricing", "plans": "pricing",
        "services": "services", "our-services": "services",
        "about": "about", "about-us": "about",
        "portfolio": "portfolio", "gallery": "gallery", "work": "portfolio",
        "menu": "menu", "our-menu": "menu",
        "rooms": "rooms", "our-rooms": "rooms", "accommodations": "rooms",
        "properties": "properties", "listings": "properties",
        "courses": "courses", "programs": "courses", "classes": "courses",
    }

    def _replace_anchor(match):
        full = match.group(0)
        anchor = match.group(1).lower().strip()
        # Direct slug match
        if anchor in slug_map:
            return full.replace(f'href="#{match.group(1)}"', f'href="{slug_map[anchor]}"')
        # CTA mapping match
        if anchor in cta_to_page:
            target = cta_to_page[anchor]
            if target in page_slugs:
                return full.replace(f'href="#{match.group(1)}"', f'href="/{target}.html"')
        # Partial match: anchor "booking-form" should match "booking" page
        for slug in page_slugs:
            if slug != "index" and (slug in anchor or anchor in slug):
                return full.replace(f'href="#{match.group(1)}"', f'href="/{slug}.html"')
        return full

    # Pattern: match <a ... href="#something" ...> but NOT navbar anchors on index page
    anchor_pattern = re.compile(r'<a\s[^>]*href="#([^"]+)"[^>]*>', re.IGNORECASE)

    for slug, html in pages_html.items():
        if slug == "index":
            # On index page, only convert anchors that match a subpage (not section anchors)
            # Only convert anchors inside CTA buttons/hero sections, not navbar
            # Find navbar end to avoid touching navbar anchors
            nav_end = 0
            nav_close = re.search(r'</nav>|</header>', html, re.IGNORECASE)
            if nav_close:
                nav_end = nav_close.end()
            # Process only the body after navbar
            before_nav = html[:nav_end]
            after_nav = html[nav_end:]
            after_nav = anchor_pattern.sub(_replace_anchor, after_nav)
            pages_html[slug] = before_nav + after_nav
        else:
            # On subpages, convert ALL anchor links that match a page
            pages_html[slug] = anchor_pattern.sub(_replace_anchor, html)

    return pages_html


def _sync_multipage_shared_elements(pages_html: dict) -> dict:
    """Ensure footer and WhatsApp button exist on every page.

    Strategy:
    - Extract footer HTML from the page that has the best footer (usually index)
    - Inject it into any page missing a footer
    - Ensure WhatsApp float button is on every page
    """
    # 1) Find the best footer from any page (prefer index/home)
    best_footer_html = None
    footer_pattern = re.compile(
        r'(<section[^>]*data-section-type="footer"[^>]*>.*?</section>)',
        re.DOTALL | re.IGNORECASE,
    )

    # Check index first, then other pages
    check_order = ["index"] + [s for s in pages_html if s != "index"]
    for slug in check_order:
        html = pages_html.get(slug, "")
        footer_match = footer_pattern.search(html)
        if footer_match:
            best_footer_html = footer_match.group(1)
            break

    # 2) Sync footer to all pages missing it
    if best_footer_html:
        for slug, html in pages_html.items():
            if not footer_pattern.search(html):
                # Insert footer before </body> or at end
                if "</body>" in html:
                    html = html.replace("</body>", f"\n{best_footer_html}\n</body>")
                else:
                    html += f"\n{best_footer_html}\n"
                pages_html[slug] = html
                logger.info(f"[MULTIPAGE] Footer synced → injected footer into '{slug}' page")

    # 3) Ensure WhatsApp float button on every page
    for slug, html in pages_html.items():
        if "whatsapp-float" not in html and "wa.me" not in html:
            # Insert before </body> or before closing footer
            if "</body>" in html:
                html = html.replace("</body>", f"\n{_WHATSAPP_FLOAT_HTML}\n</body>")
            elif "</footer>" in html.lower():
                # Insert after the last </section> (footer)
                html = html + f"\n{_WHATSAPP_FLOAT_HTML}\n"
            else:
                html += f"\n{_WHATSAPP_FLOAT_HTML}\n"
            pages_html[slug] = html
            logger.info(f"[MULTIPAGE] WhatsApp → injected float button into '{slug}' page")

    return pages_html


async def generate_multipage_html(
    plan: dict, session_id: str, niche_key: str = None, reference_html: str = None
) -> dict:
    """Generate HTML for each page in a multi-page plan. Returns {slug: html_string}.

    Strategy: Generate homepage FIRST, then use its full CSS as a design reference
    for all subpages to ensure visual consistency across the site.
    """
    pages = plan.get("pages", [])
    shared_sections = plan.get("shared_sections", [])

    if not pages:
        raise ValueError("No pages found in multi-page plan")

    # Separate homepage from subpages — homepage generates first as design reference
    homepage = None
    subpages = []
    for p in pages:
        if p.get("slug", "index") == "index":
            homepage = p
        else:
            subpages.append(p)

    if not homepage:
        homepage = pages[0]
        subpages = pages[1:]

    logger.info(f"[MULTIPAGE] Generating homepage first, then {len(subpages)} subpages...")

    # Extract CSS from reference_html if provided (template-based generation)
    _reference_css = ""
    if reference_html:
        import re as _re
        style_match = _re.search(r'<style[^>]*>(.*?)</style>', reference_html, _re.DOTALL)
        if style_match:
            _reference_css = style_match.group(1).strip()

    def _extract_smart_css_reference(full_css: str, max_chars: int = 20000) -> str:
        """Extract a smart CSS reference that preserves design tokens and critical styles.

        Priority order:
        1. CSS custom properties / :root variables (ALWAYS preserved in full)
        2. @import / @font-face rules (font loading)
        3. Navbar styles (shared across all pages)
        4. Hero styles (critical for visual quality)
        5. Button / CTA styles
        6. Footer styles
        7. Everything else (truncated if needed)
        """
        import re as _re

        # Step 1: Minify — collapse whitespace, remove comments
        minified = _re.sub(r'/\*.*?\*/', '', full_css, flags=_re.DOTALL)
        minified = _re.sub(r'\n\s*\n', '\n', minified)
        minified = _re.sub(r'  +', ' ', minified)

        # If minified fits, return it all
        if len(minified) <= max_chars:
            return minified

        # Step 2: Extract priority sections
        sections = {
            "variables": [],    # :root, CSS vars
            "imports": [],      # @import, @font-face
            "navbar": [],       # nav, navbar, header
            "hero": [],         # hero section styles
            "buttons": [],      # btn, button, cta
            "footer": [],       # footer styles
            "other": [],        # everything else
        }

        # Split into rule blocks (approximate — split on } at line start)
        blocks = _re.split(r'(?<=\})\s*\n', minified)

        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lower = block.lower()
            if ':root' in lower or 'var(--' in lower[:100]:
                sections["variables"].append(block)
            elif '@import' in lower or '@font-face' in lower:
                sections["imports"].append(block)
            elif any(k in lower[:80] for k in ['nav', '.navbar', '.header', '.nav-']):
                sections["navbar"].append(block)
            elif any(k in lower[:80] for k in ['hero', '.hero']):
                sections["hero"].append(block)
            elif any(k in lower[:80] for k in ['.btn', 'button', '.cta', '.primary-btn']):
                sections["buttons"].append(block)
            elif any(k in lower[:80] for k in ['footer', '.footer']):
                sections["footer"].append(block)
            else:
                sections["other"].append(block)

        # Step 3: Assemble in priority order
        result_parts = []
        remaining = max_chars

        for key in ["variables", "imports", "navbar", "hero", "buttons", "footer", "other"]:
            for block in sections[key]:
                if len(block) + 2 <= remaining:
                    result_parts.append(block)
                    remaining -= len(block) + 2
                elif key in ("variables", "imports"):
                    # Always include variables even if tight — they're critical
                    result_parts.append(block)
                    remaining -= len(block) + 2

        return "\n\n".join(result_parts)

    def _extract_hero_html(homepage_html: str) -> str:
        """Extract the hero section HTML from the homepage for visual reference."""
        import re as _re
        # Try data-section-type="hero"
        match = _re.search(
            r'<section[^>]*data-section-type="hero"[^>]*>.*?</section>',
            homepage_html, _re.DOTALL
        )
        if match:
            hero = match.group(0)
            return hero[:3000]  # Cap to avoid token bloat
        # Fallback: first <section> after navbar
        match = _re.search(
            r'</nav>.*?(<section[^>]*>.*?</section>)',
            homepage_html, _re.DOTALL
        )
        if match:
            return match.group(1)[:3000]
        return ""

    async def generate_one_page(page: dict, design_reference_css: str = "", homepage_hero_html: str = "") -> tuple:
        slug = page.get("slug", "index")
        title = page.get("title", slug)
        logger.info(f"[MULTIPAGE] Starting page '{title}' (slug: {slug})")
        t0 = time.time()

        prompt = build_page_html_prompt(plan, page, shared_sections)

        # Inject full CSS design reference for consistent styling across pages
        if design_reference_css:
            css_ref = _extract_smart_css_reference(design_reference_css, max_chars=20000)

            prompt += f"""

DESIGN REFERENCE CSS (BRAND FOUNDATION — use as starting point, NOT a straitjacket):
This CSS is from the homepage. Copy the :root variables, fonts, and navbar/footer styles to maintain brand consistency.
BUT: write FRESH, UNIQUE section CSS for this page's content — do NOT clone the homepage's section layouts.

```css
{css_ref}
```

WHAT TO COPY FROM THE REFERENCE:
1. :root {{ }} variables — copy them VERBATIM (colors, fonts, spacing tokens)
2. Navbar class names and styles — keep navbar identical
3. Footer class names and styles — keep footer identical
4. Button base styles (.btn, .cta) — keep buttons consistent
5. Font imports (@import) — use the same fonts

WHAT TO CREATE FRESH (do NOT copy from reference):
1. Hero section layout and style — use a DIFFERENT hero pattern than the homepage
2. Content section layouts — design new grid/split/card arrangements unique to this page
3. Section backgrounds — create new visual rhythm (alternate white/tinted/dark-accent-band)
4. Section-specific CSS — write new class names for this page's unique content sections
5. Decorative elements — use different accents, borders, shapes than the homepage

Think of it like designing a new page in a premium magazine: same brand identity (fonts, colors, logo), but each page has its OWN creative layout.
"""

            # Add homepage hero as visual QUALITY reference (not a clone template)
            if homepage_hero_html and slug != "index":
                prompt += f"""

HOMEPAGE HERO (quality reference only — do NOT clone this layout):
Below is the homepage hero. Study its QUALITY LEVEL (polish, depth, detail), then create a DIFFERENT hero for this page.

```html
{homepage_hero_html}
```

Your hero MUST:
- Match this quality level — equally polished and professional
- Use the SAME brand colors (from :root variables) and font families
- BUT use a DIFFERENT layout/pattern than the homepage hero
- Have a full-width background image with {{{{IMG:page-specific description}}}} placeholder
- Use page-appropriate content and imagery (NOT the same as homepage)
- Feel distinct from the homepage hero while belonging to the same brand
"""

        client = get_anthropic_client()
        text, _usage = await _llm_stream(
            client,
            "claude-sonnet-4-20250514",
            28000,
            prompt,
            f"Generate the {title} page HTML. Use the same brand (colors, fonts, navbar, footer) but create a UNIQUE page layout distinct from the homepage.",
            use_prompt_cache=True,
        )

        html = parse_single_code_block(text, "html")
        html = validate_html(html)

        # Resolve image placeholders (with hallucination safety + comment stripping)
        html = await _resolve_images_safe(html, niche_key=niche_key)

        duration = int((time.time() - t0) * 1000)
        logger.info(f"[MULTIPAGE] Page '{title}' done → {len(html):,} chars in {_fmt_duration(duration)}")
        save_debug(session_id, f"html_{slug}", html)
        return slug, html

    # ── Step 1: Generate homepage first ──
    homepage_slug, homepage_html = await generate_one_page(homepage, _reference_css)
    pages_html = {homepage_slug: homepage_html}
    logger.info("[MULTIPAGE] Homepage generated → extracting CSS as design reference for subpages")

    # Extract the homepage's full CSS to use as reference for subpages
    import re as _re
    homepage_style_match = _re.search(r'<style[^>]*>(.*?)</style>', homepage_html, _re.DOTALL)
    homepage_css = homepage_style_match.group(1).strip() if homepage_style_match else _reference_css

    # Extract homepage hero HTML for visual reference
    homepage_hero = _extract_hero_html(homepage_html)
    if homepage_hero:
        logger.info(f"[MULTIPAGE] Extracted homepage hero ({len(homepage_hero):,} chars) as visual reference")

    if not subpages:
        pages_html = _sync_multipage_shared_elements(pages_html)
        return pages_html

    # ── Step 2: Generate subpages in parallel using homepage CSS + hero as reference ──
    logger.info(f"[MULTIPAGE] Using {len(homepage_css):,} chars of homepage CSS as design reference")
    BATCH_SIZE = 2
    results = []
    for batch_start in range(0, len(subpages), BATCH_SIZE):
        batch = subpages[batch_start:batch_start + BATCH_SIZE]
        batch_coros = [generate_one_page(p, homepage_css, homepage_hero) for p in batch]
        batch_results = await asyncio.gather(*batch_coros, return_exceptions=True)
        results.extend(batch_results)
        # Longer delay between batches to respect rate limits
        if batch_start + BATCH_SIZE < len(subpages):
            await asyncio.sleep(8)

    failed_pages = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"[MULTIPAGE] Page generation failed: {result}")
            failed_pages.append(subpages[i])
            continue
        slug, html = result
        pages_html[slug] = html

    # Retry failed pages sequentially (one at a time to avoid rate limits)
    for page in failed_pages:
        try:
            logger.info(f"[MULTIPAGE] Retrying failed page '{page.get('title', page.get('slug'))}'...")
            await asyncio.sleep(5)
            slug, html = await generate_one_page(page, homepage_css, homepage_hero)
            pages_html[slug] = html
            logger.info(f"[MULTIPAGE] Retry succeeded for '{slug}'")
        except Exception as e:
            logger.error(f"[MULTIPAGE] Retry also failed for '{page.get('slug')}': {e}")

    if not pages_html:
        raise ValueError("All page generations failed")

    # ── Post-processing: ensure footer + WhatsApp on every page ──
    pages_html = _sync_multipage_shared_elements(pages_html)

    # ── Convert anchor links (#contact, #booking) to page hrefs ──
    pages_html = _convert_anchor_links_to_page_hrefs(pages_html)
    logger.info("[MULTIPAGE] Anchor links converted to page hrefs")

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
        # Track token usage
        uid = _current_user_id.get()
        if uid and response.usage:
            _deduct_bg(uid, {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens}, "openai", "gpt-4.1-mini", "route_edit")
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
        logger.warning(f"❌ Router Failed → {e} — falling back to style edit (safer than full rewrite)")

    # Safer fallback: try style edit instead of full page rewrite
    # Full page rewrites often corrupt the navbar and create spurious sections
    return ["__style__"]


def extract_css_vars(css: str) -> str:
    """Extract just the :root CSS variables block for context."""
    match = re.search(r":root\s*\{([^}]+)\}", css)
    if match:
        return ":root {" + match.group(1) + "}"
    return ""


async def edit_single_component(section_html: str, section_type: str, css_vars: str, prompt: str) -> str:
    """Edit a single section using LLM. Returns updated section HTML."""
    logger.info(f'🔧 Editing Section → type="{section_type}" ({len(section_html):,} chars)')
    logger.info(f'📝 Edit Request → "{prompt[:80]}{"..." if len(prompt) > 80 else ""}"')
    t0 = time.time()
    client = get_anthropic_client()

    from app.utils.animations import get_animation_prompt_compact
    system = COMPONENT_EDIT_PROMPT.format(
        css_vars=css_vars,
        section_type=section_type,
        section_html=section_html,
        prompt=prompt,
        animation_ref=get_animation_prompt_compact(),
    )
    logger.info(f"⚙️ Edit Prompt Built → {len(system):,} chars (section HTML + CSS vars + rules), sending to LLM...")

    text, _usage = await _llm_stream(
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

    text, _usage = await _llm_stream(
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
        f"🚀 Executing Step → Editing {len(edit_tasks)} section(s) via LLM{'  (parallel)' if len(edit_tasks) > 1 else ''}"
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

    # Resolve any {{IMG:}} placeholders the model may have added (with hallucination safety)
    if "{{IMG:" in updated_html or re.search(r'src=["\']https?://images\.(pexels|unsplash)\.com/', updated_html):
        plan = session.get("plan", {})
        niche_key = plan.get("brand", {}).get("industry", "general") if plan else "general"
        updated_html = await _resolve_images_safe(updated_html, niche_key=niche_key)

    return {"html": updated_html, "css": css, "js": js}


def _extract_nav_items(content: str, fmt: str) -> list[dict]:
    """Extract nav link items from a nav-links block.

    Returns a list of dicts: [{"full": "<li>...", "text": "About", "href": "#about"}, ...]
    fmt is "li" for <ul> format or "a" for <div> format.
    """
    items = []
    if fmt == "li":
        for m in re.finditer(
            r'(<li(?:\s[^>]*)?>)\s*(<a\s[^>]*href="([^"]*)"[^>]*>(.*?)</a>)\s*(</li>)',
            content, re.IGNORECASE | re.DOTALL,
        ):
            items.append({
                "full": m.group(0),
                "text": re.sub(r'<[^>]+>', '', m.group(4)).strip(),
                "href": m.group(3),
                "is_cta": "mobile-cta" in m.group(1).lower(),
            })
    else:  # "a" format
        for m in re.finditer(
            r'<a\s[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            content, re.IGNORECASE | re.DOTALL,
        ):
            text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            is_cta = "btn-primary" in m.group(0).lower()
            items.append({
                "full": m.group(0),
                "text": text,
                "href": m.group(1),
                "is_cta": is_cta,
            })
    return items


def _find_best_nav_match(nav_items: list[dict], new_title: str) -> int | None:
    """Find the nav item that best matches the new page title.

    Uses fuzzy matching + keyword overlap. Returns the index of the best match
    among non-CTA, anchor-only (href starts with #) items, or None if no
    reasonable match is found (score < 0.3).
    """
    new_lower = new_title.lower()
    new_words = set(new_lower.split())
    best_idx = None
    best_score = 0.0

    for i, item in enumerate(nav_items):
        if item["is_cta"]:
            continue
        # Only consider anchor links (intra-page) for replacement, not existing page links
        href = item["href"]
        if href.endswith(".html") or href == "/":
            continue

        text_lower = item["text"].lower()
        text_words = set(text_lower.split())

        # Fuzzy string ratio
        ratio = difflib.SequenceMatcher(None, new_lower, text_lower).ratio()

        # Word overlap bonus
        overlap = len(new_words & text_words)
        word_bonus = overlap * 0.3

        # Keyword synonyms bonus
        synonym_groups = [
            {"services", "service", "solutions", "offerings", "what we do", "our services"},
            {"about", "about us", "our story", "who we are", "company"},
            {"contact", "contact us", "get in touch", "reach us"},
            {"team", "our team", "people", "staff", "leadership"},
            {"portfolio", "work", "projects", "our work", "case studies", "gallery"},
            {"pricing", "plans", "packages"},
            {"blog", "news", "articles", "insights"},
            {"faq", "faqs", "questions", "help"},
            {"careers", "jobs", "join us", "work with us"},
        ]
        synonym_bonus = 0.0
        for group in synonym_groups:
            if new_lower in group and text_lower in group:
                synonym_bonus = 0.5
                break
            # Partial: check if any word from new_title matches any word in a group that text is in
            if text_lower in group and new_words & group:
                synonym_bonus = 0.35
                break
            if new_lower in group and text_words & group:
                synonym_bonus = 0.35
                break

        score = ratio + word_bonus + synonym_bonus
        if score > best_score:
            best_score = score
            best_idx = i

    if best_score >= 0.3 and best_idx is not None:
        logger.info(f'[NAV MATCH] Best match for "{new_title}": "{nav_items[best_idx]["text"]}" (score={best_score:.2f})')
        return best_idx

    logger.info(f'[NAV MATCH] No good match for "{new_title}" (best score={best_score:.2f}), will append')
    return None


def _sync_page_navbar(html: str, pages_dict: dict, current_slug: str, new_slug: str, new_title: str) -> str:
    """Smart-update the navbar: replace the best-matching nav item with the new page link,
    keep all other existing nav items intact, and ensure a Home link exists for inter-page nav.

    Handles both formats:
      Format A: <ul class="nav-links"><li><a>...</a></li>...</ul>
      Format B: <div class="nav-links"><a>...</a>...</div>

    Preserves CTA buttons.
    """
    new_href = f"/{new_slug}.html"
    # For subpages, the page itself needs a Home link pointing to /
    is_subpage = current_slug != "index"

    # --- Format A: <ul class="nav-links"> ---
    ul_pattern = re.compile(
        r'(<ul\s+class="nav-links"[^>]*>)(.*?)(</ul>)',
        re.IGNORECASE | re.DOTALL,
    )
    ul_match = ul_pattern.search(html)
    if ul_match:
        old_content = ul_match.group(2)
        items = _extract_nav_items(old_content, "li")
        non_cta = [it for it in items if not it["is_cta"]]
        cta_items = [it for it in items if it["is_cta"]]

        # Check if new page link already exists
        if any(it["href"] == new_href for it in items):
            return html

        best_idx = _find_best_nav_match(non_cta, new_title)

        # Build the replacement link
        new_li = f'<li><a href="{new_href}">{new_title}</a></li>'

        if best_idx is not None:
            # Replace the matched item
            replaced_text = non_cta[best_idx]["text"]
            non_cta[best_idx] = {**non_cta[best_idx], "full": new_li, "text": new_title, "href": new_href}
            logger.info(f'[NAV SYNC] Replacing "{replaced_text}" → "{new_title}" in "{current_slug}"')
        else:
            # Append before CTAs
            non_cta.append({"full": new_li, "text": new_title, "href": new_href, "is_cta": False})
            logger.info(f'[NAV SYNC] Appending "{new_title}" link to "{current_slug}"')

        # Ensure Home link exists (for inter-page navigation from subpages)
        has_home = any(it["href"] == "/" for it in non_cta)
        if not has_home and is_subpage:
            home_li = '<li><a href="/">Home</a></li>'
            non_cta.insert(0, {"full": home_li, "text": "Home", "href": "/", "is_cta": False})

        # Reassemble
        all_items = [it["full"] for it in non_cta] + [it["full"] for it in cta_items]
        new_content = "\n      " + "\n      ".join(all_items) + "\n    "
        html = html[:ul_match.start(2)] + new_content + html[ul_match.end(2):]
        return html

    # --- Format B: <div class="nav-links"> ---
    div_pattern = re.compile(
        r'(<div\s+class="nav-links"[^>]*>)(.*?)(</div>)',
        re.IGNORECASE | re.DOTALL,
    )
    div_match = div_pattern.search(html)
    if div_match:
        old_content = div_match.group(2)
        items = _extract_nav_items(old_content, "a")
        non_cta = [it for it in items if not it["is_cta"]]
        cta_items = [it for it in items if it["is_cta"]]

        # Check if new page link already exists
        if any(it["href"] == new_href for it in items):
            return html

        best_idx = _find_best_nav_match(non_cta, new_title)

        new_a = f'<a href="{new_href}">{new_title}</a>'

        if best_idx is not None:
            replaced_text = non_cta[best_idx]["text"]
            non_cta[best_idx] = {**non_cta[best_idx], "full": new_a, "text": new_title, "href": new_href}
            logger.info(f'[NAV SYNC] Replacing "{replaced_text}" → "{new_title}" in "{current_slug}"')
        else:
            non_cta.append({"full": new_a, "text": new_title, "href": new_href, "is_cta": False})
            logger.info(f'[NAV SYNC] Appending "{new_title}" link to "{current_slug}"')

        has_home = any(it["href"] == "/" for it in non_cta)
        if not has_home and is_subpage:
            home_a = '<a href="/">Home</a>'
            non_cta.insert(0, {"full": home_a, "text": "Home", "href": "/", "is_cta": False})

        all_items = [it["full"] for it in non_cta] + [it["full"] for it in cta_items]
        new_content = "\n      " + "\n      ".join(all_items) + "\n    "
        html = html[:div_match.start(2)] + new_content + html[div_match.end(2):]
        return html

    logger.warning(f"[NAV SYNC] Could not find nav-links in page '{current_slug}'")
    return html


def _sync_footer_quick_links(html: str, pages_dict: dict, new_slug: str, new_title: str) -> str:
    """Smart-update the 'Quick Links' column in the footer.

    Same strategy as navbar: replace the best-matching anchor link with the new page link,
    keep all other footer links intact.
    """
    new_href = f"/{new_slug}.html"

    # Find the footer element
    footer_match = re.search(r'<footer[\s>]', html, re.IGNORECASE)
    if not footer_match:
        return html
    footer_start = footer_match.start()

    # Look for Quick Links heading
    quick_link_headings = re.compile(
        r'<h[3-6][^>]*class="footer-heading"[^>]*>\s*'
        r'(Quick\s*Links?|Navigation|Pages|Explore|Site\s*Map|Menu|Links)\s*'
        r'</h[3-6]>',
        re.IGNORECASE,
    )
    heading_match = quick_link_headings.search(html, footer_start)
    if not heading_match:
        return html

    search_start = heading_match.end()

    # Try <ul class="footer-links"> first
    ul_pattern = re.compile(
        r'(<ul\s+class="footer-links"[^>]*>)(.*?)(</ul>)',
        re.IGNORECASE | re.DOTALL,
    )
    ul_match = ul_pattern.search(html, search_start)
    if ul_match and ul_match.start() - search_start < 200:
        old_content = ul_match.group(2)
        items = _extract_nav_items(old_content, "li")

        # Already has this page link?
        if any(it["href"] == new_href for it in items):
            return html

        best_idx = _find_best_nav_match(items, new_title)
        new_li = f'<li><a href="{new_href}">{new_title}</a></li>'

        if best_idx is not None:
            items[best_idx] = {**items[best_idx], "full": new_li}
        else:
            items.append({"full": new_li, "text": new_title, "href": new_href, "is_cta": False})

        # Ensure Home link
        if not any(it["href"] == "/" for it in items):
            items.insert(0, {"full": '<li><a href="/">Home</a></li>', "text": "Home", "href": "/", "is_cta": False})

        new_content = "\n          " + "\n          ".join(it["full"] for it in items) + "\n        "
        return html[:ul_match.start(2)] + new_content + html[ul_match.end(2):]

    # Try <div class="footer-links">
    div_pattern = re.compile(
        r'(<div\s+class="footer-links"[^>]*>)(.*?)(</div>)',
        re.IGNORECASE | re.DOTALL,
    )
    div_match = div_pattern.search(html, search_start)
    if div_match and div_match.start() - search_start < 200:
        old_content = div_match.group(2)
        items = _extract_nav_items(old_content, "a")

        if any(it["href"] == new_href for it in items):
            return html

        best_idx = _find_best_nav_match(items, new_title)
        new_a = f'<a href="{new_href}">{new_title}</a>'

        if best_idx is not None:
            items[best_idx] = {**items[best_idx], "full": new_a}
        else:
            items.append({"full": new_a, "text": new_title, "href": new_href, "is_cta": False})

        if not any(it["href"] == "/" for it in items):
            items.insert(0, {"full": '<a href="/">Home</a>', "text": "Home", "href": "/", "is_cta": False})

        new_content = "\n          " + "\n          ".join(it["full"] for it in items) + "\n        "
        return html[:div_match.start(2)] + new_content + html[div_match.end(2):]

    return html


def _update_all_page_navbars(pages_dict: dict, new_slug: str, new_title: str) -> dict:
    """Smart-sync navbars AND footer quick links in ALL pages.

    Instead of replacing all nav items, finds the best-matching anchor link
    and swaps it with the new page link. Keeps all other nav items intact.
    Returns the updated pages_dict.
    """
    for slug, page_data in pages_dict.items():
        page_html = page_data.get("html", "")
        if not page_html:
            continue
        updated = _sync_page_navbar(page_html, pages_dict, slug, new_slug, new_title)
        updated = _sync_footer_quick_links(updated, pages_dict, new_slug, new_title)
        if updated != page_html:
            pages_dict[slug] = {**page_data, "html": updated}
            logger.info(f'[NAV SYNC] Updated navbar + footer in "{slug}" page')
    return pages_dict


def _rebuild_multipage_navbars(pages_dict: dict) -> dict:
    """Full navbar rebuild for all pages — used after single→multipage conversion.

    Unlike _update_all_page_navbars (incremental, one page at a time), this function:
    1. Builds the canonical nav link list from ALL pages in pages_dict
    2. Replaces the entire nav-links content in every page
    3. Keeps CTA buttons intact
    4. Rebuilds footer quick links too

    This ensures every page has consistent, working inter-page navigation.
    """
    # Build canonical page list: Home first, then subpages alphabetically
    page_links = [{"slug": "index", "title": "Home", "href": "/"}]
    for slug in sorted(pages_dict.keys()):
        if slug == "index":
            continue
        # Derive title from slug
        title = slug.replace("-", " ").replace("_", " ").title()
        page_links.append({"slug": slug, "title": title, "href": f"/{slug}.html"})

    logger.info(f'[NAV REBUILD] Building navbar with {len(page_links)} pages: {[p["title"] for p in page_links]}')

    for current_slug, page_data in pages_dict.items():
        page_html = page_data.get("html", "")
        if not page_html:
            continue

        updated = _rebuild_page_nav(page_html, page_links, current_slug)
        updated = _rebuild_footer_links(updated, page_links)
        if updated != page_html:
            pages_dict[current_slug] = {**page_data, "html": updated}
            logger.info(f'[NAV REBUILD] Rebuilt navbar + footer in "{current_slug}"')

    return pages_dict


def _rebuild_page_nav(html: str, page_links: list[dict], current_slug: str) -> str:
    """Replace the entire nav-links content with canonical inter-page links.

    - Index page: keeps its original anchor links (#about, #services) + adds new page links
    - Subpages: replaces all anchor links with inter-page links; any leftover #anchors → /#anchor (homepage)
    Preserves CTA buttons and the nav container structure.
    """
    is_index = current_slug == "index"

    # --- Format A: <ul> with nav-related class ---
    # Try progressively broader patterns
    ul_match = None
    for ul_cls_pattern in [
        r'<ul\s+class="nav-links"[^>]*>',           # exact "nav-links"
        r'<ul\s+class="[^"]*(?:nav|menu|links)[^"]*"[^>]*>',  # any nav-related class
    ]:
        m = re.search(f'({ul_cls_pattern})(.*?)(</ul>)', html, re.IGNORECASE | re.DOTALL)
        if m and '<li' in m.group(2) and '<a ' in m.group(2):
            ul_match = m
            break

    # Last resort: any <ul> inside <nav> that contains <li><a> items
    if not ul_match:
        nav_match = re.search(r'<nav\b[^>]*>(.*?)</nav>', html, re.IGNORECASE | re.DOTALL)
        if nav_match:
            # Find the <ul> inside this nav
            nav_start = nav_match.start(1)
            for inner_m in re.finditer(r'(<ul[^>]*>)(.*?)(</ul>)', nav_match.group(1), re.IGNORECASE | re.DOTALL):
                if '<li' in inner_m.group(2) and '<a ' in inner_m.group(2):
                    # Re-search in full html at the right offset
                    ul_match = re.search(
                        r'(<ul[^>]*>)(' + re.escape(inner_m.group(2)) + r')(</ul>)',
                        html, re.DOTALL,
                    )
                    break
    if ul_match:
        old_content = ul_match.group(2)
        old_items = _extract_nav_items(old_content, "li")
        cta_items = [it for it in old_items if it["is_cta"]]

        new_items = []
        if is_index:
            # Add all page links including Home for consistent nav across all pages
            for link in page_links:
                new_items.append(f'<li><a href="{link["href"]}">{link["title"]}</a></li>')
        else:
            # Subpage: full inter-page nav, convert leftover anchors to homepage
            for link in page_links:
                if link["slug"] == current_slug:
                    new_items.append(f'<li><a href="#" class="active">{link["title"]}</a></li>')
                else:
                    new_items.append(f'<li><a href="{link["href"]}">{link["title"]}</a></li>')

        # Add CTA buttons back at the end
        for cta in cta_items:
            new_items.append(cta["full"])

        new_content = "\n      " + "\n      ".join(new_items) + "\n    "
        html = html[:ul_match.start(2)] + new_content + html[ul_match.end(2):]
        return html

    # --- Format B: <div> with nav-related class containing <a> links ---
    div_match = None
    for _div_cls in [
        r'<div\s+class="nav-links"[^>]*>',
        r'<div\s+class="[^"]*(?:nav-menu|menu-links|nav-items|links)[^"]*"[^>]*>',
    ]:
        _dm = re.search(f'({_div_cls})(.*?)(</div>)', html, re.IGNORECASE | re.DOTALL)
        if _dm and '<a ' in _dm.group(2) and 'href=' in _dm.group(2):
            div_match = _dm
            break
    if div_match:
        old_content = div_match.group(2)
        old_items = _extract_nav_items(old_content, "a")
        cta_items = [it for it in old_items if it["is_cta"]]

        new_items = []
        if is_index:
            # Add all page links including Home for consistent nav
            for link in page_links:
                new_items.append(f'<a href="{link["href"]}">{link["title"]}</a>')
        else:
            for link in page_links:
                if link["slug"] == current_slug:
                    new_items.append(f'<a href="#" class="active">{link["title"]}</a>')
                else:
                    new_items.append(f'<a href="{link["href"]}">{link["title"]}</a>')

        for cta in cta_items:
            new_items.append(cta["full"])

        new_content = "\n      " + "\n      ".join(new_items) + "\n    "
        html = html[:div_match.start(2)] + new_content + html[div_match.end(2):]
        return html

    logger.warning(f"[NAV REBUILD] Could not find nav-links in page '{current_slug}'")
    return html


def _rebuild_footer_links(html: str, page_links: list[dict]) -> str:
    """Rebuild footer Quick Links section with canonical inter-page links."""
    footer_match = re.search(r'<footer[\s>]', html, re.IGNORECASE)
    if not footer_match:
        return html
    footer_start = footer_match.start()

    quick_link_headings = re.compile(
        r'<h[3-6][^>]*class="footer-heading"[^>]*>\s*'
        r'(Quick\s*Links?|Navigation|Pages|Explore|Site\s*Map|Menu|Links)\s*'
        r'</h[3-6]>',
        re.IGNORECASE,
    )
    heading_match = quick_link_headings.search(html, footer_start)
    if not heading_match:
        return html

    search_start = heading_match.end()

    # Try <ul class="footer-links">
    ul_pattern = re.compile(
        r'(<ul\s+class="footer-links"[^>]*>)(.*?)(</ul>)',
        re.IGNORECASE | re.DOTALL,
    )
    ul_match = ul_pattern.search(html, search_start)
    if ul_match and ul_match.start() - search_start < 200:
        new_items = [f'<li><a href="{p["href"]}">{p["title"]}</a></li>' for p in page_links]
        new_content = "\n          " + "\n          ".join(new_items) + "\n        "
        return html[:ul_match.start(2)] + new_content + html[ul_match.end(2):]

    # Try <div class="footer-links">
    div_pattern = re.compile(
        r'(<div\s+class="footer-links"[^>]*>)(.*?)(</div>)',
        re.IGNORECASE | re.DOTALL,
    )
    div_match = div_pattern.search(html, search_start)
    if div_match and div_match.start() - search_start < 200:
        new_items = [f'<a href="{p["href"]}">{p["title"]}</a>' for p in page_links]
        new_content = "\n          " + "\n          ".join(new_items) + "\n        "
        return html[:div_match.start(2)] + new_content + html[div_match.end(2):]

    return html


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
    text, _usage = await _llm_stream(
        client,
        "claude-sonnet-4-20250514",
        8000,
        system_prompt,
        f"Generate the {page_title} page HTML. Return only the html code block.",
    )

    page_html = parse_single_code_block(text, "html")
    if not page_html:
        logger.error("[ADD PAGE] LLM returned empty HTML")
        return {"html": "", "css": ref_css, "js": js}

    # Separate CSS and HTML
    page_css, page_html_clean = extract_style_block(page_html)
    # Merge: reference CSS + any new page-specific CSS
    merged_css = ref_css
    if page_css:
        merged_css = ref_css + f"\n\n/* === {page_title} Page Styles === */\n" + page_css

    # Inject section IDs
    page_html_clean = inject_section_ids(page_html_clean)

    # Apply the same post-processing fixes as the main pipeline
    try:
        page_html_clean = validate_html(page_html_clean)
    except Exception as e:
        logger.warning(f"[ADD PAGE] validate_html failed: {e}")

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
        "features": "feature_cards",
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
        "menu": "feature_cards",
        "portfolio": "gallery_grid",
        "photos": "gallery_grid",
        "images": "gallery_grid",
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
        f"🚀 Executing Step → Sending to LLM to generate {section_type} section ({len(prompt_text):,} chars prompt)"
    )

    client = get_anthropic_client()
    t0 = time.time()

    try:
        raw, _usage = await _llm_stream(
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
    max_tokens = 64000 if is_redesign else 28000
    logger.info(f"⚙️ Rewrite Config → {'MAJOR REDESIGN' if is_redesign else 'standard edit'}, max_tokens={max_tokens:,}")
    logger.info(f"📦 Current Page → HTML={len(session['html']):,} chars, CSS={len(session['css']):,} chars")

    system = ITERATION_SYSTEM_PROMPT.format(
        html=session["html"],
        css=session["css"],
        js=session.get("js", ""),
        conversation_history=format_conversation_history(session),
        prompt=prompt,
    )
    logger.info(f"🚀 Executing Step → Sending full page + edit request to LLM ({len(system):,} chars prompt)")

    text, _usage = await _llm_stream(
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

    # CRITICAL: If LLM didn't return CSS (omitted <style> block), preserve the original CSS.
    # This prevents multipage pages from losing all styles during redesign.
    if not blocks.get("css") or len(blocks["css"].strip()) < 50:
        logger.warning("[ITERATE] LLM returned no CSS — preserving original session CSS")
        blocks["css"] = session["css"]

    # If LLM didn't return JS, preserve the original
    if not blocks.get("js"):
        blocks["js"] = session.get("js", "")

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
- ONLY modify the targeted element — keep ALL other elements byte-for-byte identical
- The <nav> / navbar MUST remain completely unchanged and visible — NEVER remove, hide, or modify it
- When removing an element, simply delete it — do NOT replace it with new content or sections
- Use CSS classes already defined in the <style> block for styling changes
- Do NOT use Tailwind utility classes. Add new CSS rules to the <style> block if needed.
- Do NOT generate large inline SVGs or decorative clip-path shapes
- Do NOT include any explanation, just the code block

SECTION SIZE CONSTRAINTS:
- Hero: max height 80vh. NEVER taller than viewport.
- All sections: keep the same size as original. No excessive padding.

IMAGE HANDLING:
- "Add image" or "add background image" on a hero/section = CSS background-image with overlay. Use: background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{{IMG:relevant query}}'); background-size: cover; background-position: center;
- Do NOT add tiny avatar/thumbnail images when user says "add image" on a hero — they want a FULL background image
- Background images: background-size: cover; background-position: center; with overlay
- NEVER add BOTH a background-image AND a foreground <img> for the same purpose
- For hero sections: "add image" ALWAYS means a full-width background image, never small inline images

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
    userImages: list[dict] | None = None  # [{url, filename, section}] — user-assigned images


class EditElementRequest(BaseModel):
    sessionId: str
    elementHtml: str
    elementPath: str
    prompt: str
    currentHtml: str
    currentCss: str
    currentPage: str = "index"
    contextBefore: str = ""
    contextAfter: str = ""
    sectionId: str = ""
    sectionType: str = ""
    parentTag: str = ""
    parentClass: str = ""


# ═══════════════════════════════════════════════════════════════════════
# RESTORE SESSION (hydrate backend session from saved project)
# ═══════════════════════════════════════════════════════════════════════


class RestoreSessionRequest(BaseModel):
    html: str
    css: str
    js: str = ""
    projectId: str | None = None
    projectName: str | None = None
    isMultipage: bool = False
    pages: dict | None = None
    currentPage: str = "index"


@router.post("/upload-files")
async def upload_files(
    request: Request,
    user: dict = Depends(require_auth),
):
    """Upload documents and images for website generation.

    Accepts multipart form data with files. Returns extracted text and uploaded image URLs.
    Images are stored in S3 for use during generation.
    """
    from app.utils.file_parser import extract_text, extract_zip, is_image, is_zip, upload_image_to_s3

    form = await request.form()
    files = form.getlist("files")

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files allowed")

    extracted_texts = []
    uploaded_images = []
    errors = []

    async def _process_file(filename: str, content: bytes):
        """Process a single file — extract text or upload image."""
        if len(content) > 10 * 1024 * 1024:
            errors.append(f"{filename}: File too large (max 10MB)")
            return

        if is_image(filename):
            try:
                img_data = await upload_image_to_s3(filename, content, user["user_id"])
                uploaded_images.append(img_data)
            except Exception as e:
                errors.append(f"{filename}: Upload failed — {e}")
        else:
            text = extract_text(filename, content)
            if text and text.strip():
                extracted_texts.append({"filename": filename, "text": text.strip()})
            else:
                errors.append(f"{filename}: Could not extract text")

    for f in files:
        if not hasattr(f, "filename") or not f.filename:
            continue

        content = await f.read()

        # Handle ZIP files — extract and process contents
        if is_zip(f.filename):
            if len(content) > 50 * 1024 * 1024:  # 50MB for ZIP
                errors.append(f"{f.filename}: ZIP too large (max 50MB)")
                continue
            zip_files = extract_zip(content)
            logger.info(f"[UPLOAD] ZIP {f.filename} → {len(zip_files)} files extracted")
            for zf_name, zf_content in zip_files:
                await _process_file(zf_name, zf_content)
        else:
            await _process_file(f.filename, content)

    combined_text = "\n\n".join(t["text"] for t in extracted_texts) if extracted_texts else ""

    return {
        "extracted_text": combined_text,
        "text_files": [{"filename": t["filename"], "chars": len(t["text"])} for t in extracted_texts],
        "images": uploaded_images,
        "errors": errors,
    }


@router.post("/restore-session")
async def restore_session(req: RestoreSessionRequest, user: dict = Depends(require_auth)):
    """Create a backend session from saved project data.
    This is called when loading a project from the dashboard so that
    all features (chat iteration, sections, design system) work.
    """
    # Validate input size to prevent abuse
    MAX_RESTORE_SIZE = 500_000  # 500KB (multipage projects can be large)
    total_size = len(req.html) + len(req.css) + len(req.js)
    if req.pages:
        for pg in req.pages.values():
            if isinstance(pg, dict):
                total_size += len(pg.get("html", "")) + len(pg.get("css", ""))
    if total_size > MAX_RESTORE_SIZE:
        raise HTTPException(status_code=413, detail=f"Payload too large ({total_size} chars, max {MAX_RESTORE_SIZE})")

    session_id = str(uuid.uuid4())

    html = inject_section_ids(req.html)
    sections_list = parse_sections(html)

    session_data = {
        "html": html,
        "css": req.css,
        "js": req.js,
        "plan": {},
        "prompts": [],
        "versions": [],
        "current_version": 1,
        "user_id": user["user_id"],
        "project_id": req.projectId,
    }

    # Restore multipage structure if provided
    if req.isMultipage and req.pages:
        session_data["multipage"] = True
        session_data["pages"] = {}
        for slug, page_data in req.pages.items():
            if isinstance(page_data, dict):
                page_html = inject_section_ids(page_data.get("html", ""))
                page_css = page_data.get("css", "")
                # If CSS is empty but HTML contains <style> blocks, extract them
                if not page_css and "<style" in page_html:
                    page_css, page_html = extract_style_block(page_html)
                session_data["pages"][slug] = {"html": page_html, "css": page_css}
        # Ensure index is the top-level html/css
        if "index" in session_data["pages"]:
            session_data["html"] = session_data["pages"]["index"]["html"]
            session_data["css"] = session_data["pages"]["index"]["css"]

    await redis_save_session(session_id, session_data)

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

    # ── Check token budget ──────────────────────────────────────────
    budget = await check_budget(user["user_id"])
    if not budget["ok"]:
        raise HTTPException(status_code=402, detail="[RESTRICTED] Token budget exhausted. Contact admin for more tokens.")
    _current_user_id.set(user["user_id"])

    is_new = req.sessionId is None or not await redis_session_exists(req.sessionId)
    session_id = req.sessionId if not is_new else str(uuid.uuid4())

    # ── Check generation usage limit (only for new websites) ────
    if is_new:
        from app.utils.usage_limits import check_usage_limit
        limit_check = await check_usage_limit(user["user_id"], "generation")
        if not limit_check["ok"]:
            raise HTTPException(status_code=402, detail=limit_check["message"])

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
        f'{"🆕" if is_new else "✏️"} [{mode}] session={sanitize_log(session_id[:8])}... prompt="{sanitize_log(req.prompt[:80])}{"..." if len(req.prompt) > 80 else ""}"'
    )

    # ── Track job for admin visibility ──────────────────────────────
    job_id = await _track_job(session_id, user["user_id"], "generate" if is_new else "edit")

    # ── Mark session as "generating" so recovery polling waits ─────
    if is_new:
        await redis_save_session(session_id, {"prompt": req.prompt[:500], "status": "generating"})
    else:
        # For edits: mark existing session as generating so recovery doesn't pick up stale data
        existing_sess = await redis_get_session(session_id)
        if existing_sess:
            existing_sess["status"] = "generating"
            await redis_save_session(session_id, existing_sess)

    # ── Launch generation as a background task (survives client disconnect) ──
    from app.utils.session_store import push_sse_event, pop_sse_events, clear_sse_events

    async def _run_generation():
        """Run the full generation pipeline in the background, pushing SSE events to Redis."""
        # Clear old SSE events before starting new generation
        await clear_sse_events(session_id)

        async def emit(event: str, data: dict):
            data["sessionId"] = session_id
            await push_sse_event(session_id, event, data)

        logger.info(f"[BG GEN START] session={session_id[:8]}...")
        pipeline_start = time.time()
        metrics_increment("generations_total")
        quality_scores = {}
        is_multipage = False
        pages_dict = None
        current_stage = "init"  # Track which stage we're in for error reporting

        try:
            if is_new:
                # ── Block e-commerce requests ─────────────────────────
                _prompt_lower = req.prompt.lower()
                _ecommerce_keywords = [
                    "e-commerce", "ecommerce", "e commerce", "online store", "online shop",
                    "shopping cart", "add to cart", "checkout", "product listing",
                    "buy now", "shop now", "storefront", "webshop", "web shop",
                    "sell online", "selling online", "payment gateway",
                    "shopify", "woocommerce", "magento",
                ]
                if any(kw in _prompt_lower for kw in _ecommerce_keywords):
                    await emit("error", {"message": "E-commerce websites are not supported. Our platform generates informational and business websites only. For online stores, please use a dedicated e-commerce platform like Shopify or WooCommerce."})
                    await _complete_job(job_id, "failed", "E-commerce not supported")
                    return

                # ── Stage 0: Prompt Enhancement ───────────────────────
                current_stage = "enhance"
                await emit(
                    "stage",
                    {"stage": -1, "name": "enhance", "status": "running", "message": "Understanding your vision..."},
                )

                enhanced_prompt = await enhance_prompt(req.prompt)
                await _update_job_progress(job_id, 10, "Prompt enhanced")

                await emit(
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

                # ── Detect multi-page request (only check ORIGINAL prompt, not enhanced) ──
                # Enhanced prompt often mentions "Contact page", "Blog" etc. which falsely triggers multipage
                multipage_requested = is_multipage_request(req.prompt)

                # ── Stage 1: Plan ──────────────────────────────────────
                current_stage = "plan"
                await emit(
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
                    await asyncio.sleep(3)
                    if not plan_task.done():
                        await asyncio.sleep(0)  # yield control
                plan = plan_task.result()
                is_multipage = plan.get("multipage", False)

                brand = plan.get("brand", {}).get("name", "")
                if is_multipage:
                    n_pages = len(plan.get("pages", []))
                    n_sections = sum(len(p.get("sections", [])) for p in plan.get("pages", []))
                    await emit(
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
                    await emit(
                        "stage",
                        {
                            "stage": 0,
                            "name": "plan",
                            "status": "done",
                            "message": f"Plan ready: {brand}" if brand else "Plan ready",
                            "detail": f"{n_sections} sections planned",
                        },
                    )

                await _update_job_progress(job_id, 30, "Plan ready, generating HTML...")

                # ── Stage 2: HTML + Image Resolution ──────────────────
                current_stage = "html"
                pages_dict = None  # Will hold {slug: {html, css}} for multipage

                if is_multipage:
                    # Multi-page: generate all pages in parallel
                    await emit(
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
                    _progress_tick = 0
                    while not html_task.done():
                        await asyncio.sleep(5)
                        _progress_tick += 1
                        if not html_task.done() and _progress_tick % 6 == 0:
                            elapsed = _progress_tick * 5
                            await emit("stage", {"stage": 1, "name": "html", "status": "running", "message": f"Building pages... ({elapsed}s elapsed)"})
                    pages_html = html_task.result()  # {slug: html_string}

                    total_html_chars = sum(len(h) for h in pages_html.values())
                    await emit(
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

                    # Rebuild navbars to ensure consistent inter-page navigation
                    pages_dict = _rebuild_multipage_navbars(pages_dict)
                    logger.info("[MULTIPAGE] Navbars rebuilt for consistent navigation")

                    # Use index page as the main html/css for backward compatibility
                    index_data = pages_dict.get(
                        "index", list(pages_dict.values())[0] if pages_dict else {"html": "", "css": ""}
                    )
                    html = index_data["html"]
                    css = index_data["css"]
                    save_debug(session_id, "css", css)

                    await emit(
                        "stage",
                        {
                            "stage": 2,
                            "name": "css",
                            "status": "done",
                            "message": f"CSS extracted from {len(pages_dict)} pages",
                        },
                    )
                else:
                    # Single-page: COMBINED HTML+JS in one LLM call (saves 5-10s)
                    use_template_path = reference_html is not None
                    if use_template_path:
                        await emit(
                            "stage",
                            {"stage": 1, "name": "html", "status": "running", "message": "Customizing template + adding interactions..."},
                        )
                    else:
                        await emit(
                            "stage",
                            {"stage": 1, "name": "html", "status": "running", "message": "Building page structure + interactions..."},
                        )

                    combined_task = asyncio.create_task(
                        stage_2_html_and_js(
                            plan, session_id, niche_key=niche_key,
                            reference_html=reference_html if not use_template_path else None,
                            enhanced_brief=enhanced_prompt,
                            use_template=use_template_path,
                            template_html=reference_html if use_template_path else None,
                        )
                    )

                    while not combined_task.done():
                        await asyncio.sleep(3)
                        if not combined_task.done():
                            await asyncio.sleep(0)  # yield control
                    html, js = combined_task.result()

                    await emit(
                        "stage",
                        {"stage": 1, "name": "html", "status": "done", "message": f"HTML + JS ready ({len(html):,} + {len(js):,} chars)"},
                    )

                    # ── Extract CSS from HTML <style> block ──────────────
                    css, html = extract_style_block(html)
                    # Auto-polish CSS
                    theme = plan.get("design", {}).get("theme", "light")
                    css = polish_css(css, theme)
                    save_debug(session_id, "css", css)

                    await emit(
                        "stage",
                        {"stage": 2, "name": "css", "status": "done", "message": f"CSS extracted ({len(css):,} chars)"},
                    )

                # ── Apply user-assigned images (if any) ────────────────
                if req.userImages:
                    html = _apply_user_images(html, req.userImages)
                    if is_multipage and pages_dict:
                        for _slug, _pd in pages_dict.items():
                            _pd["html"] = _apply_user_images(_pd["html"], req.userImages)
                    logger.info(f"[USER IMAGES] Applied {len(req.userImages)} user-assigned images")

                # ── Quality scoring + auto-fix ──
                current_stage = "quality"
                try:
                    from app.utils.quality_scorer import score_generation
                    _quality_html = html if not is_multipage else (pages_dict or {}).get("index", {}).get("html", html)
                    _quality_css = css if not is_multipage else (pages_dict or {}).get("index", {}).get("css", css)
                    _theme = plan.get("design", {}).get("theme", "light")
                    quality_result = score_generation(_quality_html, _quality_css, _theme)
                    quality_scores["design_score"] = quality_result["score"]
                    quality_scores["design_issues"] = len(quality_result["issues"])
                    if quality_result["auto_fixes"]:
                        # Apply auto-fixes to CSS
                        if is_multipage and pages_dict and "index" in pages_dict:
                            pages_dict["index"]["css"] = quality_result["css"]
                        else:
                            css = quality_result["css"]
                        logger.info(f"[QUALITY] Score: {quality_result['score']}/100, {len(quality_result['issues'])} issues, {len(quality_result['auto_fixes'])} auto-fixed")
                    else:
                        logger.info(f"[QUALITY] Score: {quality_result['score']}/100, {len(quality_result['issues'])} issues")
                except Exception as e:
                    logger.warning(f"[QUALITY] Scoring failed: {e}")

                # ── Premium post-processing (hero, whitespace, cards, animations) ──
                try:
                    from app.utils.premium_postcss import apply_premium_postprocessing
                    _theme = plan.get("design", {}).get("theme", "light")
                    if is_multipage and pages_dict:
                        for _slug, _pd in pages_dict.items():
                            _pd["html"], _pd["css"] = apply_premium_postprocessing(_pd["html"], _pd["css"], _theme)
                        # Update main html/css from index
                        if "index" in pages_dict:
                            html = pages_dict["index"]["html"]
                            css = pages_dict["index"]["css"]
                    else:
                        html, css = apply_premium_postprocessing(html, css, _theme)
                except Exception as e:
                    logger.warning(f"[PREMIUM] Post-processing failed: {e}")

                await _update_job_progress(job_id, 60, "HTML, CSS & JS ready, polishing...")

                # ── Stage 3: JS — only needed for multipage (single-page already has JS from combined call)
                if is_multipage and pages_dict:
                    await emit("stage", {"stage": 2, "name": "js", "status": "running", "message": "Adding interactions..."})
                    combined_html = "\n".join(pd["html"] for pd in pages_dict.values())
                    js = await stage_3_js(combined_html, session_id)
                    await emit(
                        "stage", {"stage": 2, "name": "js", "status": "done", "message": f"JS ready ({len(js):,} chars)"}
                    )
                else:
                    await emit(
                        "stage", {"stage": 2, "name": "js", "status": "done", "message": f"JS ready ({len(js):,} chars)"}
                    )

                # ── Stage 4: Quality checks + auto-fix ─────────────────
                await emit(
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
                    """Apply validate_html, responsive, image fixes. Returns (html, css)."""
                    # validate_html fixes: footer bg, mobile nav CSS, overflow:hidden, WhatsApp, etc.
                    try:
                        page_html = validate_html(page_html)
                    except Exception as e:
                        logger.warning(f"[VALIDATE] subpage fix failed: {e}")
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
                        logger.info("[FORMS] contact form handler injected (index)")

                    # Also inject form handler into multipage subpages
                    if is_multipage and pages_dict:
                        for _slug, _pd in pages_dict.items():
                            if _slug == "index":
                                continue  # index already handled above
                            if has_contact_form(_pd["html"]):
                                _pd["html"], js = inject_form_handler(_pd["html"], js)
                                logger.info(f"[FORMS] contact form handler injected ({_slug})")
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
                await emit(
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
                    if anim_js and "Mobile Hamburger Menu Toggle" not in js:
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
                    await emit("error", {"message": "Session not found"})
                    return

                # ── Check for "add WhatsApp button" BEFORE normal routing ──
                prompt_lower = req.prompt.lower()
                if re.search(r'\b(?:add|enable|include|put|show|want)\b.*\bwhats\s*app\b', prompt_lower):
                    html = session["html"]
                    if "whatsapp-float" not in html and "wa.me" not in html:
                        wa_html = (
                            '\n<!-- WHATSAPP_FLOAT -->\n'
                            '<a href="https://wa.me/971XXXXXXXXX" target="_blank" rel="noopener" '
                            'class="whatsapp-float" style="position:fixed;bottom:1.5rem;right:1.5rem;'
                            'width:3.5rem;height:3.5rem;background:#25D366;border-radius:50%;display:flex;'
                            'align-items:center;justify-content:center;color:white;font-size:1.5rem;'
                            'box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:50;transition:transform 0.3s;'
                            'text-decoration:none;" aria-label="Chat on WhatsApp">'
                            '<i class="fa-brands fa-whatsapp"></i></a>\n'
                            '<!-- END_WHATSAPP_FLOAT -->\n'
                        )
                        # Insert before closing </footer> or at end of HTML
                        if '</footer>' in html:
                            html = html.replace('</footer>', '</footer>' + wa_html, 1)
                        else:
                            html = html + wa_html
                        session["html"] = html

                        # Also update in pages dict if multipage
                        if session.get("multipage") and session.get("pages"):
                            for slug in session["pages"]:
                                pg_html = session["pages"][slug]["html"]
                                if "whatsapp-float" not in pg_html:
                                    if '</footer>' in pg_html:
                                        pg_html = pg_html.replace('</footer>', '</footer>' + wa_html, 1)
                                    else:
                                        pg_html = pg_html + wa_html
                                    session["pages"][slug]["html"] = pg_html

                        code = {"html": html, "css": session["css"], "js": session.get("js", "")}
                        plan = session.get("plan") or {}

                        await emit("stage", {"stage": 0, "name": "route", "status": "done", "message": "Adding WhatsApp button"})
                        await emit("stage", {"stage": 1, "name": "edit", "status": "done", "message": "WhatsApp button added — update the phone number in site settings"})

                        # Skip to finalization (don't go through router/LLM)
                        # Save session and emit complete
                        await redis_save_session(session_id, {**session, "html": html})

                        sections_list = parse_sections(html)
                        complete_payload = {
                            "success": True,
                            "website": {"html": html, "css": session["css"], "js": session.get("js", "")},
                            "sessionId": session_id,
                            "isNewDesign": False,
                            "sections": sections_list,
                        }
                        if session.get("multipage"):
                            complete_payload["isMultipage"] = True
                            complete_payload["pages"] = session.get("pages", {})
                        from app.utils.usage_limits import increment_usage
                        asyncio.ensure_future(increment_usage(user["user_id"], "edit"))
                        await emit("complete", complete_payload)
                        return
                    else:
                        await emit("stage", {"stage": 0, "name": "route", "status": "done", "message": "WhatsApp button already exists"})
                        await emit("stage", {"stage": 1, "name": "edit", "status": "done", "message": "WhatsApp button is already on the page — update number in site settings"})
                        code = {"html": html, "css": session["css"], "js": session.get("js", "")}
                        plan = session.get("plan") or {}
                        sections_list = parse_sections(html)
                        await emit("complete", {
                            "success": True,
                            "website": {"html": html, "css": session["css"], "js": session.get("js", "")},
                            "sessionId": session_id,
                            "isNewDesign": False,
                            "sections": sections_list,
                        })
                        return

                # ── Check for "add page" request → triggers full multipage regeneration ──
                add_page_list = detect_add_page_request(req.prompt)
                existing_pages = session.get("pages", {})
                is_already_multipage = session.get("multipage", False)

                # Filter out pages that already exist or use reserved slug
                if add_page_list:
                    add_page_list = [
                        p for p in add_page_list
                        if p["slug"] not in existing_pages and p["slug"] != "index"
                    ]

                if add_page_list and not is_already_multipage:
                    # ── SINGLE→MULTI: Full regeneration as multipage website ──
                    # Keep the same design/brand but regenerate everything with multiple pages
                    page_names = ", ".join(p["title"] for p in add_page_list[:4])

                    await emit(
                        "stage",
                        {"stage": 0, "name": "plan", "status": "running", "message": f"Converting to multipage: {page_names}..."},
                    )

                    # Build a new prompt that includes the original + page requests
                    original_plan = session.get("plan", {})
                    original_prompt = session.get("original_prompt", req.prompt)
                    brand_name = original_plan.get("brand", {}).get("name", "")
                    from app.utils.niches import detect_niche as _detect_niche
                    niche_key = original_plan.get("niche", "") or _detect_niche(original_prompt)

                    # Build multipage prompt from original context
                    multipage_prompt = f"{original_prompt}. Make this a multipage website with pages: Home, {page_names}"

                    # Re-plan as multipage
                    plan_task = asyncio.create_task(
                        stage_1_plan(multipage_prompt, session_id, niche_key=niche_key, multipage=True)
                    )
                    while not plan_task.done():
                        await asyncio.sleep(3)
                        if not plan_task.done():
                            await asyncio.sleep(0)  # yield control
                    plan = plan_task.result()

                    n_pages = len(plan.get("pages", []))
                    await emit(
                        "stage",
                        {"stage": 0, "name": "plan", "status": "done", "message": f"Plan ready: {brand_name or 'Multipage'} ({n_pages} pages)"},
                    )

                    # Generate all pages
                    await emit(
                        "stage",
                        {"stage": 1, "name": "html", "status": "running", "message": f"Building {n_pages} pages..."},
                    )

                    reference_html = session.get("html", "")  # Use current homepage as design reference
                    html_task = asyncio.create_task(
                        generate_multipage_html(plan, session_id, niche_key=niche_key, reference_html=reference_html)
                    )
                    _progress_tick = 0
                    while not html_task.done():
                        await asyncio.sleep(5)
                        _progress_tick += 1
                        if not html_task.done() and _progress_tick % 6 == 0:
                            elapsed = _progress_tick * 5
                            await emit("stage", {"stage": 1, "name": "html", "status": "running", "message": f"Building pages... ({elapsed}s elapsed)"})
                    pages_html = html_task.result()

                    total_html_chars = sum(len(h) for h in pages_html.values())
                    await emit(
                        "stage",
                        {"stage": 1, "name": "html", "status": "done", "message": f"{len(pages_html)} pages generated ({total_html_chars:,} chars)"},
                    )

                    # Extract CSS from each page
                    theme = plan.get("design", {}).get("theme", "light")
                    pages_dict = {}
                    for slug, page_html in pages_html.items():
                        page_css, page_html_clean = extract_style_block(page_html)
                        page_css = polish_css(page_css, theme)
                        pages_dict[slug] = {"html": page_html_clean, "css": page_css}

                    # Generate JS
                    await emit(
                        "stage",
                        {"stage": 2, "name": "js", "status": "running", "message": "Generating interactions..."},
                    )
                    index_html = pages_dict.get("index", {}).get("html", "")
                    index_css = pages_dict.get("index", {}).get("css", "")
                    js_task = asyncio.create_task(
                        stage_3_js(index_html, session_id)
                    )
                    while not js_task.done():
                        await asyncio.sleep(5)
                        if not js_task.done():
                            await asyncio.sleep(0)  # yield control
                    js_code = js_task.result()

                    await emit(
                        "stage",
                        {"stage": 2, "name": "js", "status": "done", "message": f"JS ready ({len(js_code):,} chars)"},
                    )

                    # Save to session
                    session["html"] = index_html
                    session["css"] = index_css
                    session["js"] = js_code
                    session["plan"] = plan
                    session["multipage"] = True
                    session["pages"] = pages_dict

                    code = {"html": index_html, "css": index_css, "js": js_code}

                elif add_page_list and is_already_multipage:
                    # ── ALREADY MULTIPAGE: add individual pages ──
                    page_count = len(existing_pages)
                    available_slots = 5 - page_count
                    if available_slots <= 0:
                        await emit("error", {"message": "Maximum 5 pages reached."})
                        return

                    pages_to_add = add_page_list[:available_slots]
                    page_names = ", ".join(p["title"] for p in pages_to_add)

                    await emit("stage", {"stage": 0, "name": "route", "status": "running", "message": f"Adding pages: {page_names}..."})
                    await emit("stage", {"stage": 0, "name": "route", "status": "done", "message": f"Target: {len(pages_to_add)} new page(s)"})

                    pages_dict = {**existing_pages}
                    last_slug = None

                    for i, page_info in enumerate(pages_to_add):
                        page_slug = page_info["slug"]
                        page_title = page_info["title"]

                        await emit("stage", {"stage": 1, "name": "edit", "status": "running", "message": f"Generating {page_title} page ({i+1}/{len(pages_to_add)})..."})

                        new_page_code = await _add_new_page(req.prompt, session, page_slug, page_title)

                        if not new_page_code.get("html"):
                            await emit("error", {"message": f"Failed to generate {page_title} page"})
                            return

                        pages_dict[page_slug] = {"html": new_page_code["html"], "css": new_page_code["css"]}
                        last_slug = page_slug

                        await emit("stage", {"stage": 1, "name": "edit", "status": "done", "message": f"{page_title} page created ({i+1}/{len(pages_to_add)})"})

                    pages_dict = _rebuild_multipage_navbars(pages_dict)

                    if "index" in pages_dict:
                        session["html"] = pages_dict["index"]["html"]

                    code = {**pages_dict[last_slug], "js": session.get("js", "")}
                    plan = session.get("plan") or {}

                    session["multipage"] = True
                    session["pages"] = pages_dict
                    session["_added_page"] = last_slug

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
                    await emit(
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

                    await emit(
                        "stage", {"stage": 0, "name": "route", "status": "done", "message": f"Target: {target_desc}"}
                    )

                    # Edit the component(s)
                    edit_action = "Adding" if append_targets else "Editing"
                    await emit(
                        "stage",
                        {"stage": 1, "name": "edit", "status": "running", "message": f"{edit_action} {target_desc}..."},
                    )

                    # Call iterate_website which handles routing internally too,
                    # but pass pre-routed targets to avoid double routing
                    code = await _execute_component_edit(req.prompt, session, targets)
                    plan = session.get("plan")

                    if not code.get("html"):
                        await emit("error", {"message": "Failed to apply changes"})
                        return

                    await emit("stage", {"stage": 1, "name": "edit", "status": "done", "message": "Changes applied"})

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
            converted_to_multipage = not is_new and session.get("multipage") and session.get("pages") and not added_page_slug and not existing.get("multipage")
            if is_new and is_multipage and pages_dict:
                session_data["multipage"] = True
                session_data["pages"] = {
                    slug: {"html": pd["html"], "css": pd["css"]} for slug, pd in pages_dict.items()
                }
            elif converted_to_multipage:
                # Single→multipage full regeneration
                session_data["multipage"] = True
                session_data["pages"] = session["pages"]
                session_data["plan"] = session.get("plan", plan)
                session_data["js"] = session.get("js", code.get("js", ""))
                index_data = session_data["pages"].get("index")
                if index_data:
                    session_data["html"] = index_data["html"]
                    session_data["css"] = index_data["css"]
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

            await _complete_job(job_id, "completed")

            # Log generation to admin dashboard (fire-and-forget)
            if is_new:
                _page_count = len(pages_dict) if is_multipage and pages_dict else 1
                _log_generation_bg(
                    user_id=user["user_id"],
                    prompt=req.prompt,
                    status="completed",
                    session_id=session_id,
                    html_size=len(code.get("html", "")),
                    duration_ms=int(generation_ms),
                    is_multipage=is_multipage,
                    page_count=_page_count,
                    performance_score=quality_scores.get("performance_score"),
                    seo_score=quality_scores.get("seo_score"),
                )
            else:
                # Increment edit count for modifications
                from app.utils.usage_limits import increment_usage
                asyncio.ensure_future(increment_usage(user["user_id"], "edit"))

            await emit("complete", complete_payload)

        except CircuitOpenError:
            metrics_increment("generation_errors")
            await _complete_job(job_id, "failed", "AI service temporarily unavailable")
            _log_generation_bg(
                user_id=user["user_id"],
                prompt=req.prompt,
                status="failed",
                session_id=session_id,
                duration_ms=int((time.time() - pipeline_start) * 1000) if pipeline_start else None,
                stage_failed=current_stage,
                error_message="AI service temporarily unavailable (circuit open)",
            )
            await emit("error", {"message": "AI service is temporarily unavailable. Please try again in a few minutes."})
        except asyncio.CancelledError:
            logger.info(f"[BG GEN] Task cancelled (session={session_id[:8]})")
            await _complete_job(job_id, "failed", "Generation cancelled")
            raise  # Must re-raise CancelledError per asyncio contract
        except Exception as e:
            metrics_increment("generation_errors")
            err_msg = str(e).strip() or type(e).__name__
            logger.error(f"[BG GEN ERROR] stage={current_stage} error={err_msg}", exc_info=True)
            await _complete_job(job_id, "failed", err_msg[:200])
            _log_generation_bg(
                user_id=user["user_id"],
                prompt=req.prompt,
                status="failed",
                session_id=session_id,
                duration_ms=int((time.time() - pipeline_start) * 1000) if pipeline_start else None,
                stage_failed=current_stage,
                error_message=err_msg[:500],
            )
            try:
                await emit("error", {"message": str(e)})
            except Exception:
                pass

    # Launch generation as background task (survives client disconnect)
    gen_task = asyncio.create_task(_run_generation())
    _background_tasks.add(gen_task)
    gen_task.add_done_callback(_background_tasks.discard)

    # SSE stream: tail the Redis event queue and relay to client
    async def event_stream():
        event_index = 0
        idle_count = 0
        max_idle = 600  # 10 minutes max wait

        while idle_count < max_idle:
            events = await pop_sse_events(session_id, event_index)
            if events:
                idle_count = 0
                for ev in events:
                    event_type = ev.get("event", "stage")
                    data = ev.get("data", {})
                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                    event_index += 1
                    # Stop streaming after complete or error
                    if event_type in ("complete", "error"):
                        return
            else:
                idle_count += 1
                yield ": keepalive\n\n"
                await asyncio.sleep(1)

        # Timed out waiting
        yield f"event: error\ndata: {json.dumps({'message': 'Generation timed out'})}\n\n"

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

    # ── Check token budget ──────────────────────────────────────────
    budget = await check_budget(user["user_id"])
    if not budget["ok"]:
        raise HTTPException(status_code=402, detail="[RESTRICTED] Token budget exhausted. Contact admin for more tokens.")
    _current_user_id.set(user["user_id"])

    is_new = req.sessionId is None or not await redis_session_exists(req.sessionId)
    session_id = req.sessionId if not is_new else str(uuid.uuid4())

    # ── Check generation usage limit (only for new websites) ────
    if is_new:
        from app.utils.usage_limits import check_usage_limit
        limit_check = await check_usage_limit(user["user_id"], "generation")
        if not limit_check["ok"]:
            raise HTTPException(status_code=402, detail=limit_check["message"])

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
                    logger.info(f"[TEMPLATE] loaded '{sanitize_log(req.templateId)}' ({len(reference_html):,} chars)")
                except Exception as e:
                    logger.warning(f"[TEMPLATE] failed to load '{sanitize_log(req.templateId)}': {e}")

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

                # Also inject form handler into multipage subpages
                if is_multipage_gen and pages_dict:
                    for _slug, _pd in pages_dict.items():
                        if _slug == "index":
                            continue
                        if has_contact_form(_pd["html"]):
                            _pd["html"], js = inject_form_handler(_pd["html"], js)
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
                if anim_js and "Mobile Hamburger Menu Toggle" not in js:
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

                            p_html = validate_html(pages_dict[slug]["html"])
                            p_html, p_css = auto_fix_responsive(p_html, pages_dict[slug]["css"])
                            p_html = optimize_image_tags(p_html)
                            pages_dict[slug] = {"html": p_html, "css": p_css}
                        except Exception:
                            pass
                # Inject animation CSS into subpages
                try:
                    from app.utils.animations import get_animation_css
                    anim_css = get_animation_css()
                    if anim_css:
                        for slug in pages_dict:
                            if slug != "index" and anim_css not in pages_dict[slug].get("css", ""):
                                pages_dict[slug]["css"] += "\n\n/* === Built-in Animations === */\n" + anim_css
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

        # Log generation to admin dashboard (fire-and-forget)
        if is_new:
            _page_count = len(pages_dict) if is_multipage_gen and pages_dict else 1
            _log_generation_bg(
                user_id=user["user_id"],
                prompt=req.prompt,
                status="completed",
                session_id=session_id,
                html_size=len(code.get("html", "")),
                duration_ms=int(generation_ms),
                is_multipage=is_multipage_gen,
                page_count=_page_count,
            )

        return result

    except HTTPException:
        metrics_increment("generation_errors")
        raise
    except CircuitOpenError as e:
        metrics_increment("generation_errors")
        _log_generation_bg(
            user_id=user["user_id"],
            prompt=req.prompt,
            status="failed",
            session_id=session_id,
            duration_ms=int((time.time() - generation_start) * 1000),
            error_message="AI service temporarily unavailable (circuit open)",
        )
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again in a few minutes.",
        ) from e
    except Exception as e:
        metrics_increment("generation_errors")
        _log_generation_bg(
            user_id=user["user_id"],
            prompt=req.prompt,
            status="failed",
            session_id=session_id,
            duration_ms=int((time.time() - generation_start) * 1000),
            error_message=str(e)[:500],
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


# ═══════════════════════════════════════════════════════════════════════
# ELEMENT EDITING
# ═══════════════════════════════════════════════════════════════════════

ELEMENT_EDIT_PROMPT_PRECISE = """You are a surgical HTML editor. You will receive a specific HTML element from a website and an edit instruction. Return ONLY the edited version of that element.

DESIGN SYSTEM (CSS variables in the page):
{css_vars}

CSS CLASSES available in the page <style>:
Layout: .container, .container-wide, .container-narrow, .container-xs
Grid: .grid-2, .grid-3, .grid-4 (auto-responsive)
Buttons: .btn-primary, .btn-secondary, .btn-group
Cards: .card, .card-title, .card-text, .card-body, .icon-box
Images: .img-cover, .img-wrapper
Section: .section-header, .section-title, .section-subtitle, .text-center, .text-light
Hero: .hero-section, .hero-heading, .hero-subtitle, .hero-split-grid, .hero-ctas, .hero-bg-cover, .hero-overlay
Stats: .stat-item, .stat-number, .stat-label
Forms: .form-input, .contact-form
Footer: .footer-grid, .footer-heading, .footer-links, .footer-bottom, .social-links, .social-link

LOCATION: {section_type} section, path: {element_path}
Parent: <{parent_tag} class="{parent_class}">

{context_block}

ELEMENT TO EDIT:
```html
{element_html}
```

EDIT REQUEST: {prompt}

RULES:
- Return ONLY the edited element in a single ```html code block
- Same opening tag (e.g. if it's a <div>, return a <div>; if <h2>, return <h2>)
- Keep existing classes, ids, data attributes unless the edit requires changing them
- Use inline style for one-off changes, or use the CSS classes listed above
- BUTTON COLOR CHANGES: When changing a button's background color, use style="background: COLOR !important" (with !important) because .btn-primary has a gradient that will override plain inline styles. For text color changes on buttons, use style="color: COLOR !important".
- COLOR CHANGES: Apply with inline style using !important to override CSS class styles. Example: style="color: red !important" or style="background-color: #333 !important". Always use !important for color overrides.
- ALIGNMENT / POSITIONING: Apply via inline style. text-align: center/left/right for text. For flexbox containers, use justify-content and align-items inline. Do NOT restructure the DOM — just add/modify the style attribute.
- SPACING (padding/margin): Apply via inline style. e.g. style="padding: 2rem" or style="margin-bottom: 1rem". Do NOT restructure the DOM.
- BACKGROUND CHANGES: Apply via inline style. e.g. style="background: #1a1a2e" or style="background: linear-gradient(...)". Do NOT restructure the DOM.
- VISIBILITY (hide/show): To hide, return an empty HTML comment: <!-- removed -->. Do NOT delete surrounding elements.
- SIZE CHANGES (bigger/smaller/wider/narrower): Apply via inline style. e.g. style="font-size: 2rem" or style="width: 80%". Do NOT restructure the DOM.
- Use var(--primary), var(--accent), var(--bg), var(--text), var(--radius) for colors/tokens
- Keep existing image src URLs unless user explicitly asks to change images
- Do NOT bloat the element — keep it concise
- Do NOT add extra wrapper divs
- Do NOT generate inline SVGs or decorative clip-path shapes
- Do NOT include explanation — just the code block
- For background images: use inline style background-image with overlay
- Icons: use <i class="fa-solid fa-xxx"> (Font Awesome is pre-loaded)
- REMOVAL: If user asks to remove/delete this element, return ONLY: <!-- removed -->

TYPOGRAPHY & STYLING (when changing text appearance):
- Font size: use inline style font-size (rem units: 0.875rem, 1rem, 1.25rem, 1.5rem, 2rem, 3rem)
- Font weight: 400 (normal), 500 (medium), 600 (semibold), 700 (bold), 800 (extrabold)
- Text color: use var(--primary), var(--accent), var(--text), var(--text-muted), or any CSS color
- Font family: use var(--font-heading) or var(--font-body) for existing fonts.
  For a NEW font: inline style with Google Fonts-safe family, e.g. style="font-family: 'Playfair Display', serif"
  Popular: Inter, Poppins, Playfair Display, Space Grotesk, DM Sans, Outfit, Sora, Crimson Text, Lora
- Letter spacing: e.g. letter-spacing: 0.05em, 0.1em | Text transform: uppercase, lowercase, capitalize

{animation_ref}

IMAGE RULES (when adding/changing images):
- If the user provides a URL, use that exact URL as the src
- Adapt image size to context with inline style:
  - Navbar logo: max-height: 40-50px, width: auto
  - Card/grid image: width: 100%, height: 200-280px, object-fit: cover
  - Hero image: width: 100%, max-height: 500px, object-fit: cover
  - Team/avatar: width: 80-120px, height: 80-120px, border-radius: 50%, object-fit: cover
  - Icon/thumbnail: width: 48-64px, height: auto
  - General: max-width: 100%, height: auto (responsive default)
- Always add alt attribute describing the image
- Add loading="lazy" for images below the fold

JS-DEPENDENT CLASS NAMES (do NOT rename):
.nav-links, .nav-toggle, .faq-item, .faq-question, .faq-answer,
.testimonial-slide, .slider-dot, .carousel-container, .carousel-track,
.carousel-slide, .carousel-prev, .carousel-next, .carousel-dot,
#gallery-lightbox, .gallery-item, .stat-number, #year, #back-to-top"""

ELEMENT_EDIT_PROMPT_SECTION = """You are an expert frontend developer editing a specific element inside a website section.
The edit requires structural changes (adding/removing elements, reordering, layout changes).

DESIGN SYSTEM (CSS variables):
{css_vars}

CSS CLASSES available:
Layout: .container, .container-wide, .container-narrow, .container-xs
Grid: .grid-2, .grid-3, .grid-4 | Buttons: .btn-primary, .btn-secondary, .btn-group
Cards: .card, .card-title, .card-text, .card-body, .icon-box
Images: .img-cover, .img-wrapper | Section: .section-header, .section-title, .section-subtitle, .text-center, .text-light
Hero: .hero-section, .hero-heading, .hero-subtitle, .hero-split-grid, .hero-ctas
Stats: .stat-item, .stat-number, .stat-label
Forms: .form-input (ALL inputs/textareas MUST have this), .form-textarea (add to textareas), .contact-form, .form-hint, .contact-item, .contact-icon
Footer: .footer-grid, .footer-heading, .footer-links (list-style:none), .footer-description, .social-links, .social-link, .footer-bottom

FORM RULES: Every <input> and <textarea> MUST have class="form-input". Use placeholder="..." for labels, NOT floating <label> elements. Submit buttons use .btn-primary. Footer lists use <ul class="footer-links"> (NO raw bullets).

FULL SECTION ({section_type}, id={section_id}):
{section_html}

TARGET ELEMENT (path: {element_path}):
```html
{element_html}
```

EDIT REQUEST: {prompt}

RULES:
- Return the COMPLETE updated section HTML in a single ```html code block
- Keep the same <section data-section-type data-section-id> wrapper
- ONLY modify what the user asked for — keep everything else byte-for-byte identical
- Do NOT remove or modify elements the user didn't mention
- Do NOT remove or hide the <nav> or navbar — it must always remain visible and functional
- Do NOT add new sections or generate replacement content when removing an element — just remove that specific element
- Use CSS classes above, NOT Tailwind. Use var(--primary), var(--accent), etc.
- Keep existing image src URLs unless asked to change
- Do NOT add Font Awesome script tags
- Do NOT generate large inline SVGs or decorative clip-path shapes
- Do NOT include explanation

REMOVAL RULES:
- When removing an element (form, button, card, etc.), simply DELETE it from the HTML
- Do NOT replace removed elements with new sections or content
- Do NOT add padding/spacing to "fill" the gap left by a removed element
- The section should still render correctly with the element removed

ALIGNMENT CHANGES:
- To CENTER a hero: remove .hero-full-overlay class (if present), add .text-center class to the content wrapper, and add style="text-align: center" on the content container. Also set .hero-ctas to justify-content: center.
- To LEFT-ALIGN a hero: add .hero-full-overlay class to the content wrapper, remove .text-center, set text-align: left.
- For non-hero sections: add style="text-align: center/left/right" on the container or wrapper div.
- ALL child elements (heading, subtitle, buttons, trust line) must have the SAME alignment — never mix.

TYPOGRAPHY & STYLING (when changing text appearance):
- Font size: inline style font-size in rem (0.875rem, 1rem, 1.25rem, 1.5rem, 2rem, 3rem)
- Font weight: 400-800 | Text color: var(--primary), var(--accent), var(--text), or any CSS color
- Font family: var(--font-heading), var(--font-body), or Google Fonts family inline (e.g. 'Playfair Display', serif)
- Letter spacing, text-transform: via inline style

{animation_ref}

IMAGE RULES (when adding/changing images):
- If the user provides a URL, use that exact URL as the src
- Adapt image size to context:
  Navbar logo: max-height: 40-50px | Card: width:100%, height:200-280px, object-fit:cover
  Hero: width:100%, max-height:500px | Avatar: 80-120px, border-radius:50% | General: max-width:100%, height:auto
- Always add alt attribute, loading="lazy" for below-fold images

JS-DEPENDENT CLASS NAMES (do NOT rename):
.nav-links, .nav-toggle, .faq-item, .faq-question, .faq-answer,
.testimonial-slide, .slider-dot, .carousel-container, .carousel-track,
.carousel-slide, .carousel-prev, .carousel-next, .carousel-dot,
#gallery-lightbox, .gallery-item, .stat-number, #year, #back-to-top"""


def _is_structural_edit(prompt: str) -> bool:
    """Detect if the edit requires adding/removing/reordering DOM elements (needs full section context).

    ONLY returns True for changes that genuinely alter DOM structure:
    adding/removing/reordering/duplicating elements, or converting layout type.

    CSS-only changes (alignment, colors, spacing, backgrounds, visibility, sizing)
    are NOT structural — they go through the precise element edit path which
    handles them much better without risk of corrupting the section.
    """
    structural_keywords = [
        # ── Adding elements ──
        r'\badd\b.*\b(card|item|column|row|button|link|section|image|picture|photo|logo|img|icon|field|input|element)',
        r'\badd\s+(a|an|another|new|more)\b(?!\s*(space|spacing|gap|padding|margin|room))',
        r'\binsert\b',
        r'\bput\b.*\b(image|picture|photo|logo|img)\b',
        r'\bplace\b.*\b(image|picture|photo|logo|img)\b',
        # ── Removing elements ──
        r'\bremove\b', r'\bdelete\b',
        # ── Reordering / moving DOM elements ──
        r'\breorder\b', r'\brearrange\b',
        r'\bmove\b.*\b(before|after|above|below|up|down)\b',
        r'\bswap\b',
        # ── Duplicating / splitting / merging ──
        r'\bsplit\b', r'\bmerge\b', r'\bduplicate\b', r'\bcopy\b',
        # ── Layout type conversion (e.g. "convert to grid") ──
        r'\bchange\s+layout\b',
        r'\bgrid\b.*\bcolumn',
        r'\bconvert\b.*\b(to|into)\b',
        r'\b(vertical|horizontal)\s*layout\b', r'\bcolumn\s*layout\b', r'\brow\s*layout\b',
        r'\bstack\b.*\b(vertical|horizontal)',
        r'\bside\s*by\s*side\b',
    ]
    prompt_lower = prompt.lower()
    return any(re.search(pat, prompt_lower) for pat in structural_keywords)


VOID_ELEMENTS = frozenset([
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
])


def _find_element_end(full_html: str, start: int, tag_name: str) -> int | None:
    """From *start* (the '<' of the opening tag), find where the element ends.

    For void elements (img, br, hr …) → end of the self-closing tag.
    For normal elements → matching closing tag respecting nesting depth.
    """
    tag_lower = tag_name.lower()

    if tag_lower in VOID_ELEMENTS:
        # Find the end of this self-closing tag: scan for '>'
        gt = full_html.find('>', start)
        if gt == -1:
            return None
        return gt + 1

    # Normal element — walk the HTML counting open/close of the same tag
    depth = 0
    tag_re = re.compile(
        rf'(<{tag_name}[\s>/])|(</{tag_name}\s*>)', re.IGNORECASE
    )
    for m in tag_re.finditer(full_html, start):
        if m.group(1):   # opening tag
            depth += 1
        elif m.group(2): # closing tag
            depth -= 1
            if depth == 0:
                return m.end()
    return None


def _find_element_in_html(full_html: str, element_html: str) -> tuple[int, int] | None:
    """Find the exact position of an element's outerHTML in the full page HTML.

    Tries exact match first, then normalised whitespace match, then
    prefix match, then attribute-flexible match (handles browser HTML normalization).
    All fallbacks use tag-aware end detection so we never blindly slice by len(element_html).
    """
    # Exact match
    idx = full_html.find(element_html)
    if idx != -1:
        return idx, idx + len(element_html)

    tag = re.match(r'<(\w+)', element_html)
    tag_name = tag.group(1) if tag else None

    # Normalise whitespace and try again
    def normalise(s: str) -> str:
        return re.sub(r'\s+', ' ', s).strip()

    norm_el = normalise(element_html)
    norm_full = normalise(full_html)
    idx = norm_full.find(norm_el)
    if idx != -1:
        anchor = element_html[:80].strip()
        orig_idx = full_html.find(anchor)
        if orig_idx != -1 and tag_name:
            end = _find_element_end(full_html, orig_idx, tag_name)
            if end is not None:
                return orig_idx, end

    # Prefix match — use the first 80 chars to locate, then find the
    # actual end of the element in the stored HTML (not len(element_html))
    prefix = element_html[:80].strip()
    idx = full_html.find(prefix)
    if idx != -1 and tag_name:
        end = _find_element_end(full_html, idx, tag_name)
        if end is not None:
            return idx, end

    # ── Attribute-flexible match ──────────────────────────────────
    # Browser DOM normalises HTML: reorders attrs, changes quotes, adds/removes whitespace.
    # Extract key attributes (class, id) + text content and search for a matching element.
    if tag_name:
        # Extract class and id from the element
        cls_match = re.search(r'class\s*=\s*["\']([^"\']*)["\']', element_html)
        id_match = re.search(r'id\s*=\s*["\']([^"\']*)["\']', element_html)
        # Extract visible text (strip tags)
        text_content = re.sub(r'<[^>]+>', '', element_html).strip()[:60]

        # Build a regex to find this element in the stored HTML
        # Match: same tag, same class (if any), same id (if any)
        attr_parts = []
        if id_match:
            attr_parts.append(rf'id\s*=\s*["\']?{re.escape(id_match.group(1))}["\']?')
        if cls_match:
            # Match class value (may be in different order but usually same)
            attr_parts.append(rf'class\s*=\s*["\']?{re.escape(cls_match.group(1))}["\']?')

        if attr_parts:
            # Find opening tag with these attributes
            attr_pattern = r'<' + tag_name + r'(?=[^>]*' + r')(?=[^>]*'.join([''] + attr_parts) + r')[^>]*>'
            try:
                for m in re.finditer(attr_pattern, full_html, re.IGNORECASE):
                    # Verify text content matches (at least partial)
                    end = _find_element_end(full_html, m.start(), tag_name)
                    if end is not None:
                        candidate = full_html[m.start():end]
                        candidate_text = re.sub(r'<[^>]+>', '', candidate).strip()[:60]
                        # If text content is similar enough, we found it
                        if text_content and candidate_text and (
                            text_content[:30] in candidate_text or candidate_text[:30] in text_content
                        ):
                            return m.start(), end
                        # If no text to compare (e.g. img, input), accept the attribute match
                        if not text_content.strip():
                            return m.start(), end
            except re.error:
                pass

        # Last resort: match by text content alone (for elements like <p>, <h2>)
        if text_content and len(text_content) > 10 and tag_name:
            # Find all elements of this tag type and match by text
            tag_pattern = rf'<{tag_name}[\s>]'
            for m in re.finditer(tag_pattern, full_html, re.IGNORECASE):
                end = _find_element_end(full_html, m.start(), tag_name)
                if end is not None:
                    candidate = full_html[m.start():end]
                    candidate_text = re.sub(r'<[^>]+>', '', candidate).strip()
                    if text_content[:40] in candidate_text:
                        return m.start(), end

    return None


@router.post("/edit-element")
async def edit_element(req: EditElementRequest, user: dict = Depends(require_auth)):
    logger.info(
        f'🖱️ [ELEMENT EDIT] path="{sanitize_log(req.elementPath)}" prompt="{sanitize_log(req.prompt[:80])}" '
        f'element={len(req.elementHtml):,}chars section={sanitize_log(req.sectionType or "?")} page={sanitize_log(req.currentPage)}'
    )

    req.prompt = sanitize_prompt(req.prompt)
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    moderation = await moderate_prompt(req.prompt)
    if not moderation["safe"]:
        raise HTTPException(status_code=400, detail=moderation["reason"])

    # ── Check token budget ──────────────────────────────────────────
    budget = await check_budget(user["user_id"])
    if not budget["ok"]:
        raise HTTPException(status_code=402, detail="[RESTRICTED] Token budget exhausted. Contact admin for more tokens.")
    _current_user_id.set(user["user_id"])


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
        structural = _is_structural_edit(req.prompt)

        # ── FAST PATH: Direct removal (no LLM call) ─────────────
        remove_pattern = re.compile(
            r"^(remove|delete|get rid of|take out|strip|hide|drop)\b"
            r"(\s+(this|it|the|that|entire))?"
            r"(\s+(section|element|button|form|card|item|image|text|block|component|div|field|input|link|icon|row|column|paragraph|heading|title|subtitle|nav|footer|header))?"
            r"(\s*(please|now|pls|from\s+(here|this\s+page|the\s+page)))?"
            r"\s*[.!]?\s*$",
            re.IGNORECASE,
        )
        if remove_pattern.match(req.prompt.strip()):
            # Try to find and remove the element directly from HTML
            element_snippet = req.elementHtml.strip()
            if element_snippet and element_snippet in full_html:
                result_html = full_html.replace(element_snippet, "", 1)
                # Verify we didn't wipe everything
                if len(result_html.strip()) > 200:
                    logger.info("🖱️ [ELEMENT EDIT] ✅ Direct removal (no LLM) — removed %d chars", len(element_snippet))
                    from app.utils.usage_limits import increment_usage
                    await increment_usage(user["user_id"], "edit")
                    return {
                        "success": True,
                        "website": {"html": result_html, "css": css},
                        "manualReplace": False,
                    }
                else:
                    logger.warning("🖱️ [ELEMENT EDIT] Direct removal would leave page empty, falling through to LLM")

        # ── Find which section contains the element ──────────────
        sections = parse_sections(full_html)
        target_section = None

        # Method 1: Use sectionId from frontend if provided
        if req.sectionId:
            for s in sections:
                if s["id"] == req.sectionId:
                    target_section = s
                    break

        # Method 2: Find by element HTML substring
        if not target_section:
            element_snippet = req.elementHtml[:80]
            for s in sections:
                section_html = full_html[s["start"]:s["end"]]
                if element_snippet in section_html:
                    target_section = s
                    break

        # Method 3: Fallback — path class matching
        if not target_section:
            path_classes = re.findall(r"\.([a-zA-Z][\w-]*)", req.elementPath)
            for s in sections:
                section_html = full_html[s["start"]:s["end"]]
                if any(cls in section_html for cls in path_classes):
                    target_section = s
                    break

        client = get_anthropic_client()

        # ── Protect navbar/header from structural rewrites ──────
        # Nav/header sections are fragile — structural edits (which rewrite
        # the whole section) frequently corrupt or hide them.  Force these
        # to the precise element-edit path instead.
        nav_types = {"nav", "navbar", "header", "navigation"}
        if structural and target_section and target_section["type"].lower() in nav_types:
            logger.info(
                f'🖱️ [ELEMENT EDIT] Downgrading structural → precise for nav/header section '
                f'"{target_section["id"]}" to prevent navbar corruption'
            )
            structural = False

        if structural and target_section:
            # ── STRUCTURAL EDIT: needs full section context ──────
            section_html = full_html[target_section["start"]:target_section["end"]]
            section_type = target_section["type"]
            section_id = target_section["id"]
            logger.info(f'🖱️ [ELEMENT EDIT] Structural edit in section "{section_id}" ({section_type})')

            from app.utils.animations import get_animation_prompt_compact as _anim_compact
            system = ELEMENT_EDIT_PROMPT_SECTION.format(
                css_vars=css_vars,
                section_type=section_type,
                section_id=section_id,
                section_html=section_html,
                element_path=req.elementPath,
                element_html=req.elementHtml,
                prompt=req.prompt,
                animation_ref=_anim_compact(),
            )

            text, _ = await _llm_stream(client, "claude-sonnet-4-20250514", 8000, system, req.prompt)
            edited_section = parse_single_code_block(text, "html")
            if not edited_section:
                logger.error("🖱️ [ELEMENT EDIT] FAILED — no HTML parsed from section edit")
                raise HTTPException(status_code=500, detail="Failed to parse edited section")

            result_html = replace_section_html(full_html, section_id, edited_section)
            result_css = css
            logger.info(f'🖱️ [ELEMENT EDIT] Section patched: {len(edited_section):,} chars')

        elif target_section or not structural:
            # ── PRECISE ELEMENT EDIT: return only the element ────
            result_css = None  # may be set by CSS override fallback
            section_type = req.sectionType or (target_section["type"] if target_section else "unknown")

            # Build context block showing surrounding elements
            context_parts = []
            if req.contextBefore:
                context_parts.append(f"ELEMENT BEFORE (sibling):\n{req.contextBefore}")
            if req.contextAfter:
                context_parts.append(f"ELEMENT AFTER (sibling):\n{req.contextAfter}")
            context_block = "\n\n".join(context_parts) if context_parts else ""

            from app.utils.animations import get_animation_prompt_compact as _anim_compact2
            system = ELEMENT_EDIT_PROMPT_PRECISE.format(
                css_vars=css_vars,
                section_type=section_type,
                element_path=req.elementPath,
                parent_tag=req.parentTag or "div",
                parent_class=req.parentClass or "",
                context_block=context_block,
                element_html=req.elementHtml,
                prompt=req.prompt,
                animation_ref=_anim_compact2(),
            )
            logger.info(f"🖱️ [ELEMENT EDIT] Precise prompt: {len(system):,} chars")

            text, _ = await _llm_stream(
                client, "claude-sonnet-4-20250514", 4000, system,
                f"Edit this element: {req.prompt}"
            )
            edited_element = parse_single_code_block(text, "html")
            if not edited_element:
                logger.error(f"🖱️ [ELEMENT EDIT] FAILED — no HTML parsed. Response: {text[:500]}")
                raise HTTPException(status_code=500, detail="Failed to parse edited element")

            # If LLM returned a removal marker, treat as element removal
            if edited_element.strip() in ("<!-- removed -->", "<!-- element removed -->", ""):
                edited_element = ""
                logger.info("🖱️ [ELEMENT EDIT] LLM indicated removal — deleting element")
            else:
                logger.info(f"🖱️ [ELEMENT EDIT] Got edited element: {len(edited_element):,} chars (was {len(req.elementHtml):,})")

            # ── Patch the edited element back into the page ──────
            # Try to find and replace the original element in the HTML
            if target_section:
                # Replace within the section first, then patch section into page
                section_html = full_html[target_section["start"]:target_section["end"]]
                pos = _find_element_in_html(section_html, req.elementHtml)
                if pos:
                    new_section = section_html[:pos[0]] + edited_element + section_html[pos[1]:]
                    result_html = replace_section_html(full_html, target_section["id"], new_section)
                    logger.info("🖱️ [ELEMENT EDIT] Matched element within section")
                else:
                    # Fallback: search in full HTML
                    pos = _find_element_in_html(full_html, req.elementHtml)
                    if pos:
                        result_html = full_html[:pos[0]] + edited_element + full_html[pos[1]:]
                        logger.info("🖱️ [ELEMENT EDIT] Matched element in full HTML")
                    else:
                        logger.warning("🖱️ [ELEMENT EDIT] Could not locate element — using simple replace")
                        result_html = full_html.replace(req.elementHtml, edited_element, 1)
                        # Check if simple replace actually worked
                        if result_html == full_html and edited_element != req.elementHtml:
                            logger.warning("🖱️ [ELEMENT EDIT] Simple replace FAILED — element not found in HTML. Trying CSS-based patch.")
                            # Last resort: inject the edit as a CSS override using the element path
                            # Extract inline style from the edited element
                            style_match = re.search(r'style\s*=\s*["\']([^"\']*)["\']', edited_element)
                            if style_match and req.elementPath:
                                css_selector = req.elementPath.replace(' > ', ' > ')
                                css_override = f"\n/* Element edit override */\n{css_selector} {{ {style_match.group(1)} !important; }}\n"
                                result_css = css + css_override
                                logger.info(f"🖱️ [ELEMENT EDIT] Applied CSS override: {css_selector}")
                            else:
                                # Force replace by finding any matching tag with same text
                                element_text = re.sub(r'<[^>]+>', '', req.elementHtml).strip()[:50]
                                if element_text:
                                    tag_m = re.match(r'<(\w+)', req.elementHtml)
                                    if tag_m:
                                        tag_re = rf'<{tag_m.group(1)}[^>]*>[^<]*{re.escape(element_text[:30])}[^<]*</{tag_m.group(1)}>'
                                        match = re.search(tag_re, full_html, re.IGNORECASE | re.DOTALL)
                                        if match:
                                            result_html = full_html[:match.start()] + edited_element + full_html[match.end():]
                                            logger.info("🖱️ [ELEMENT EDIT] Matched via text content regex")
            else:
                # Element outside sections (nav, footer, etc.)
                pos = _find_element_in_html(full_html, req.elementHtml)
                if pos:
                    result_html = full_html[:pos[0]] + edited_element + full_html[pos[1]:]
                else:
                    result_html = full_html.replace(req.elementHtml, edited_element, 1)
                    if result_html == full_html and edited_element != req.elementHtml:
                        logger.warning("🖱️ [ELEMENT EDIT] Replace failed for non-section element — trying text match")
                        element_text = re.sub(r'<[^>]+>', '', req.elementHtml).strip()[:50]
                        if element_text:
                            tag_m = re.match(r'<(\w+)', req.elementHtml)
                            if tag_m:
                                tag_re = rf'<{tag_m.group(1)}[^>]*>[^<]*{re.escape(element_text[:30])}[^<]*</{tag_m.group(1)}>'
                                match = re.search(tag_re, full_html, re.IGNORECASE | re.DOTALL)
                                if match:
                                    result_html = full_html[:match.start()] + edited_element + full_html[match.end():]

            if result_css is None:
                result_css = css

        else:
            # ── Fallback: no section found — try precise edit on full HTML ──
            # Avoid full-page rewrite which often corrupts navbar and creates
            # spurious sections.  Instead, try to find and replace the element
            # directly in the full HTML using the precise element editor.
            logger.info("🖱️ [ELEMENT EDIT] No section found — trying precise edit on element in full HTML")
            from app.utils.animations import get_animation_prompt_compact as _anim_fallback
            system = ELEMENT_EDIT_PROMPT_PRECISE.format(
                css_vars=css_vars,
                section_type=req.sectionType or "unknown",
                element_path=req.elementPath,
                parent_tag=req.parentTag or "div",
                parent_class=req.parentClass or "",
                context_block="",
                element_html=req.elementHtml,
                prompt=req.prompt,
                animation_ref=_anim_fallback(),
            )
            text, _ = await _llm_stream(client, "claude-sonnet-4-20250514", 4000, system,
                                        f"Edit this element: {req.prompt}")
            edited_element = parse_single_code_block(text, "html")
            if not edited_element:
                logger.error("🖱️ [ELEMENT EDIT] FAILED — no HTML parsed in fallback")
                raise HTTPException(status_code=500, detail="Failed to parse edited element")

            pos = _find_element_in_html(full_html, req.elementHtml)
            if pos:
                result_html = full_html[:pos[0]] + edited_element + full_html[pos[1]:]
            else:
                result_html = full_html.replace(req.elementHtml, edited_element, 1)
            result_css = css

        # ── Save to session ──────────────────────────────────────
        s = await redis_get_session(req.sessionId) if req.sessionId else None
        if s:
            _verify_session_ownership(s, user)
            versions = s.get("versions", [])
            versions.append({
                "version": s.get("current_version", 0),
                "html": s["html"], "css": s["css"], "js": s.get("js", ""),
                "prompt": f"[Element edit: {req.elementPath}] {req.prompt}",
            })
            MAX_VERSIONS = 15
            if len(versions) > MAX_VERSIONS:
                versions = versions[-MAX_VERSIONS:]
            s["versions"] = versions
            if s.get("multipage") and req.currentPage:
                if "pages" not in s:
                    s["pages"] = {}
                s["pages"][req.currentPage] = {"html": result_html, "css": result_css}
                # session["html"] always holds the index page — don't overwrite with other pages
                if req.currentPage == "index":
                    s["html"] = result_html
                    s["css"] = result_css
                # else: leave session["html"] as-is (it's the index page)
            else:
                s["html"] = result_html
                s["css"] = result_css
            s["current_version"] = s.get("current_version", 0) + 1
            s["prompts"] = s.get("prompts", []) + [f"[Element: {req.elementPath}] {req.prompt}"]
            await redis_save_session(req.sessionId, s)

        logger.info(f"🖱️ [ELEMENT EDIT] ✅ Done → html={len(result_html):,}, css={len(result_css):,}")
        from app.utils.usage_limits import increment_usage
        await increment_usage(user["user_id"], "edit")
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
async def delete_session_endpoint(session_id: str, _user: dict = Depends(require_auth)):
    await redis_delete_session(session_id)
    return {"success": True}


@router.get("/niches")
async def get_niches(_user: dict = Depends(require_auth)):
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
