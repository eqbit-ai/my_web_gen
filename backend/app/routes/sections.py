"""
Section manipulation routes — reorder, delete, duplicate, regenerate sections.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import aiofiles

from app.utils import sanitize_log
from app.utils.auth import decode_access_token
from app.utils.content_moderation import check_prompt_safety
from app.utils.design_system import design_system_to_prompt_context
from app.utils.llm_clients import get_anthropic_client
from app.utils.section_parser import (
    duplicate_section,
    extract_section_html,
    inject_section_ids,
    insert_section_at,
    parse_sections,
    remove_section,
    reorder_sections,
    replace_section_html,
    toggle_section_visibility,
    update_section_style,
)
from app.utils.session_store import get_session as redis_get_session
from app.utils.session_store import save_session as redis_save_session

router = APIRouter()
security = HTTPBearer()

# Shared rules appended to ALL section edit/regen prompts
SHARED_SECTION_RULES = """
SECTION SIZE CONSTRAINTS (CRITICAL):
- Hero sections: max height 80vh. NEVER taller than viewport.
- All other sections: keep roughly the same visual size as the original.
- Do NOT add excessive padding/margins.

IMAGE HANDLING:
- "Add background image" = CSS background-image ONLY. Do NOT also add a foreground <img>.
- NEVER add BOTH a background-image AND a foreground <img> for the same purpose.
- Background images: background-size: cover; background-position: center; with overlay div (max 40% opacity).
- For NEW images use placeholder: src="{{IMG:descriptive keywords}}"
- Image queries must be industry-specific. NEVER use generic/unrelated images.

STYLING:
- Use pure CSS classes already defined in the page's <style> block. NO Tailwind utility classes.
- Use CSS variables: var(--primary), var(--accent), var(--bg), var(--radius), etc.
- Do NOT generate large inline SVGs or decorative clip-path shapes.

JS-DEPENDENT CLASS NAMES (do NOT rename or remove — JS will break):
- Navbar: .nav-links, .nav-toggle, .nav-scrolled, .nav-cta, .mobile-cta
- FAQ: .faq-item, .faq-question, .faq-answer
- Testimonial slider: .testimonial-slider, .testimonial-slide, .slider-dot
- Image carousel: .carousel-container, .carousel-track, .carousel-slide, .carousel-prev, .carousel-next, .carousel-dot
- Gallery: #gallery-lightbox, .gallery-item, .lightbox-image, .lightbox-close, .lightbox-prev, .lightbox-next
- Service modals: .modal-trigger, .detail-modal, .modal-close, data-modal attribute
- Stats counter: .stat-number
- Footer year: #year
- Back to top: #back-to-top, .progress-ring
- Search: .search-toggle, .search-dropdown, .search-container
"""


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


async def _verify_session_ownership(session_id: str, user: dict) -> dict:
    """Verify that a session exists and belongs to the authenticated user.

    Returns the session data if valid.
    Raises 404 if session not found, 403 if it belongs to another user.
    """
    session = await redis_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session_user = session.get("user_id")
    if session_user and str(session_user) != str(user.get("user_id")):
        raise HTTPException(status_code=403, detail="Forbidden — session belongs to another user")
    return session


import html as _html_mod
import re as _re


def _sanitize_text_input(text: str) -> str:
    """Sanitize user text input to prevent XSS.
    Strips HTML tags and escapes dangerous characters.
    Only allows plain text — no HTML, no scripts, no event handlers.
    """
    # Strip all HTML tags
    stripped = _re.sub(r"<[^>]+>", "", text)
    # Escape any remaining HTML entities to prevent injection
    stripped = _html_mod.escape(stripped)
    return stripped


def _merge_section_css(base_css: str, section_id: str, new_css: str) -> str:
    """Merge new section CSS using markers — replaces previous CSS for the same section.
    Prevents CSS bloat from repeated updates.
    """
    marker = f"/* Section: {section_id} */"
    end_marker = f"/* End Section: {section_id} */"

    result = base_css

    # Remove previous block for this section if it exists
    if marker in result:
        start_idx = result.index(marker)
        if end_marker in result:
            end_idx = result.index(end_marker) + len(end_marker)
        else:
            next_marker = result.find("/* Section:", start_idx + len(marker))
            end_idx = next_marker if next_marker != -1 else len(result)
        result = result[:start_idx].rstrip() + result[end_idx:]

    # Also strip any old-style markers (/* Updated navbar */, /* Updated footer */, etc.)
    old_markers = [
        f"/* Updated {section_id.split('-')[0] if '-' in section_id else section_id} */",
        f"/* Regenerated: {section_id} */",
        f"/* End Regenerated: {section_id} */",
    ]
    for old in old_markers:
        result = result.replace(old, "")

    # Append new CSS with markers
    result = result.rstrip() + f"\n\n{marker}\n{new_css}\n{end_marker}"
    return result


def _validate_regen_html(html: str, section_id: str, section_type: str) -> str:
    """Validate and fix regenerated section HTML.
    Ensures data-section-id and data-section-type attributes exist.
    Strips Font Awesome kit scripts that LLM sometimes adds.
    Checks for required elements per section type (e.g. H1 in hero).
    """
    import logging
    import re as _re
    _logger = logging.getLogger(__name__)

    if not html or len(html) < 20:
        return html

    # Strip orphaned comment closers (-->) that leak into visible output
    html = _re.sub(r'(?<![->])\s*-->\s*(?=<|\s*$)', '', html)

    # Strip Font Awesome kit/CDN script and link tags
    html = _re.sub(
        r"<script[^>]*(?:kit\.fontawesome\.com|fontawesome)[^>]*>(?:</script>)?\s*",
        "",
        html,
        flags=_re.IGNORECASE,
    )
    html = _re.sub(
        r"<link[^>]*(?:fontawesome|font-awesome)[^>]*/?\s*>\s*",
        "",
        html,
        flags=_re.IGNORECASE,
    )

    # Check for data-section-id
    if f'data-section-id="{section_id}"' not in html:
        # Inject into the first opening tag
        first_tag_end = html.index(">") if ">" in html else -1
        if first_tag_end > 0:
            html = html[:first_tag_end] + f' data-section-id="{section_id}"' + html[first_tag_end:]

    # Check for data-section-type
    if "data-section-type=" not in html:
        first_tag_end = html.index(">") if ">" in html else -1
        if first_tag_end > 0:
            html = html[:first_tag_end] + f' data-section-type="{section_type}"' + html[first_tag_end:]

    # ── Required elements check ──────────────────────────────────────
    section_lower = section_type.lower() if section_type else ""

    # Hero sections: fix Typed.js inside H1 — H1 must have static readable text
    if section_lower == "hero" and _re.search(r"<h1[\s>]", html, _re.IGNORECASE):
        # Check if H1 contains data-typed or typed-text spans (JS-dependent text)
        h1_match = _re.search(r"<h1[^>]*>(.*?)</h1>", html, _re.IGNORECASE | _re.DOTALL)
        if h1_match:
            h1_content = h1_match.group(1)
            has_typed = "data-typed" in h1_content or "typed-text" in h1_content
            if has_typed:
                _logger.warning("⚠️ Hero H1 contains Typed.js — extracting static text")
                # Extract the typed strings to use as static text
                typed_strings_match = _re.search(r'data-typed=\'(\[.*?\])\'', h1_content)
                static_text = ""
                if typed_strings_match:
                    try:
                        import json
                        strings = json.loads(typed_strings_match.group(1))
                        static_text = strings[0] if strings else ""
                    except Exception:
                        pass
                # Extract any non-typed text (e.g. "with Intelligent ERP Solutions")
                remaining_text = _re.sub(r'<span[^>]*(?:typed-text|data-typed)[^>]*>.*?</span>', '', h1_content, flags=_re.DOTALL)
                remaining_text = _re.sub(r'<br\s*/?>', ' ', remaining_text)
                remaining_text = _re.sub(r'<[^>]+>', '', remaining_text).strip()
                # Build clean H1 content
                full_text = f"{static_text} {remaining_text}".strip() if static_text else remaining_text
                if not full_text:
                    full_text = "Your Business Solution"
                # Get original H1 opening tag
                h1_open_match = _re.search(r"(<h1[^>]*>)", html, _re.IGNORECASE)
                if h1_open_match:
                    # Remove data-splitting from the H1 tag
                    clean_h1_open = _re.sub(r'\s*data-splitting(?:="[^"]*")?', '', h1_open_match.group(1))
                    html = html[:h1_match.start()] + f'{clean_h1_open}{full_text}</h1>' + html[h1_match.end():]

    # Hero sections MUST have an H1
    if section_lower == "hero" and not _re.search(r"<h1[\s>]", html, _re.IGNORECASE):
        _logger.warning("⚠️ Regenerated hero section missing <h1> — injecting fallback heading")
        # Find a good insertion point: after the first container/wrapper div, or after section opening tag
        # Look for a subtitle/span/p to insert before
        subtitle_match = _re.search(r"(<(?:span|p|div)[^>]*class=\"[^\"]*(?:subtitle|tagline|badge|label)[^\"]*\")", html, _re.IGNORECASE)
        if subtitle_match:
            # Insert H1 after the subtitle element's closing tag
            # Find the end of this element
            pos = subtitle_match.end()
            # Find the closing tag
            tag_name = _re.match(r"<(\w+)", subtitle_match.group(1)).group(1)
            close_pattern = f"</{tag_name}>"
            close_pos = html.find(close_pattern, pos)
            if close_pos != -1:
                insert_at = close_pos + len(close_pattern)
                html = html[:insert_at] + '\n            <h1 class="hero-heading">Your Heading Here</h1>' + html[insert_at:]
        else:
            # Insert after first container-like div
            container_match = _re.search(r"(<div[^>]*class=\"[^\"]*container[^\"]*\"[^>]*>)", html, _re.IGNORECASE)
            if container_match:
                insert_at = container_match.end()
                html = html[:insert_at] + '\n            <h1 class="hero-heading">Your Heading Here</h1>' + html[insert_at:]

    # ── Fix url() quotes (centralized — covers ALL section code paths) ──
    # LLM generates url("https://...") inside style="" attributes, which breaks HTML
    # because the " inside url(" prematurely closes the style attribute.
    # Only fix url("http...) — NOT url("data:...) which needs double quotes.
    html = _re.sub(r'url\("(https?://)', r"url('\1", html)
    html = _re.sub(r'url\("(\{\{IMG:)', r"url('\1", html)
    html = _re.sub(r"(url\('https?://[^'\"]*?)\"(\s*\))", r"\1'\2", html)
    html = _re.sub(r"(url\('\{\{IMG:[^'\"]*?)\"(\s*\))", r"\1'\2", html)

    return html


def _extract_section_css(css: str, section_id: str, section_html: str) -> str:
    """Extract CSS rules relevant to a specific section.
    Looks for: rules targeting the section ID, and class names found in the section HTML.
    """
    if not css:
        return ""

    # Collect class names from the section HTML
    class_names = set(_re.findall(r'class="([^"]*)"', section_html))
    classes = set()
    for cn in class_names:
        for c in cn.split():
            # Skip responsive prefixes (sm:, md:, lg:) if any remain
            if ":" not in c:
                classes.add(c)

    # Also look for the section ID directly
    relevant_rules = []
    # Split CSS into rule blocks (rough but effective)
    blocks = _re.findall(r"([^{}]+\{[^{}]*\})", css)
    for block in blocks:
        selector = block.split("{")[0].strip()
        # Check if selector references the section ID
        if section_id in selector:
            relevant_rules.append(block.strip())
            continue
        # Check if selector references any class from the section
        for cls in classes:
            if f".{cls}" in selector:
                relevant_rules.append(block.strip())
                break

    return "\n".join(relevant_rules)


def _strip_section_css(css: str, section_id: str) -> str:
    """Remove CSS rules added by a previous section regeneration (marked with comment markers).

    Only removes rules inside /* Section: {section_id} */ ... /* End Section: {section_id} */ markers
    (added by _merge_section_css). Does NOT strip rules by substring match — that was destroying
    unrelated CSS like .hero-heading when section_id was "hero".
    """
    if not css or not section_id:
        return css
    import re as _re
    # Remove marked section CSS blocks (matches _merge_section_css markers)
    marker_start = f"/* Section: {section_id} */"
    marker_end = f"/* End Section: {section_id} */"
    if marker_start in css:
        pattern = _re.escape(marker_start) + r".*?" + _re.escape(marker_end)
        css = _re.sub(pattern, "", css, flags=_re.DOTALL)
    return css.strip()


# ── Multi-page helpers ──────────────────────────────────────────────────


def _get_page_html(session: dict, page_slug: str = "index") -> str:
    """Get HTML for the specified page from session."""
    if session.get("multipage") and page_slug != "index" and session.get("pages", {}).get(page_slug):
        return session["pages"][page_slug]["html"]
    return session.get("html", "")


def _set_page_html(session: dict, html: str, page_slug: str = "index"):
    """Set HTML for the specified page in session."""
    if session.get("multipage") and page_slug:
        if "pages" not in session:
            session["pages"] = {}
        if page_slug not in session["pages"]:
            session["pages"][page_slug] = {"html": "", "css": ""}
        session["pages"][page_slug]["html"] = html
    if page_slug == "index" or not session.get("multipage"):
        session["html"] = html


# ── Schemas ─────────────────────────────────────────────────────────────


class ReorderRequest(BaseModel):
    sessionId: str
    newOrder: list[str]  # List of section IDs in desired order
    pageSlug: str = "index"


class DeleteRequest(BaseModel):
    sessionId: str
    sectionId: str
    pageSlug: str = "index"


class DuplicateRequest(BaseModel):
    sessionId: str
    sectionId: str
    pageSlug: str = "index"


class RegenerateRequest(BaseModel):
    sessionId: str
    sectionId: str
    prompt: str
    variantKey: str | None = None
    pageSlug: str = "index"


class UpdateTextRequest(BaseModel):
    sessionId: str
    sectionId: str
    changes: list[dict]  # [{selector, newText}]
    pageSlug: str = "index"


class InsertSectionRequest(BaseModel):
    sessionId: str
    sectionHtml: str
    sectionCss: str = ""
    referenceSectionId: str
    position: str = "after"  # "before" or "after"
    pageSlug: str = "index"


class ToggleVisibilityRequest(BaseModel):
    sessionId: str
    sectionId: str
    visible: bool
    pageSlug: str = "index"


class UpdateStyleRequest(BaseModel):
    sessionId: str
    sectionId: str
    styles: dict
    pageSlug: str = "index"


class UpdateNavRequest(BaseModel):
    sessionId: str
    items: list[dict]  # [{label, href, isButton}]
    sticky: bool = False
    logoUrl: str | None = None
    pageSlug: str = "index"


class UpdateFooterRequest(BaseModel):
    sessionId: str
    columns: list[dict]  # [{heading, links}]
    copyrightText: str
    socialLinks: dict
    logoUrl: str | None = None
    pageSlug: str = "index"


class UpdateMetaRequest(BaseModel):
    sessionId: str
    title: str | None = None
    description: str | None = None
    keywords: str | None = None
    faviconUrl: str | None = None
    whatsappNumber: str | None = None
    pageSlug: str = "index"


class UpdateContactRequest(BaseModel):
    sessionId: str
    recipientEmail: str | None = None  # form recipient — None means "leave unchanged"
    fields: list[str] | None = None
    successMessage: str | None = None
    pageSlug: str = "index"
    # Floating contact widgets — all optional. Empty/missing values cause the
    # corresponding widget to be removed from the page on next inject.
    whatsappNumber: str | None = None
    socialFacebook: str | None = None
    socialInstagram: str | None = None
    socialTiktok: str | None = None
    socialLinkedin: str | None = None
    socialYoutube: str | None = None


# ── Endpoints ───────────────────────────────────────────────────────────


@router.get("/{session_id}")
async def get_sections(session_id: str, page_slug: str = "index", user: dict = Depends(require_auth)):
    """Parse and return section list for the current session HTML."""
    session = await _verify_session_ownership(session_id, user)

    html = _get_page_html(session, page_slug)

    # Inject section IDs if not already present
    if "data-section-id" not in html:
        html = inject_section_ids(html)
        _set_page_html(session, html, page_slug)
        await redis_save_session(session_id, session)

    sections = parse_sections(html)
    return {"sections": sections}


@router.post("/reorder")
async def reorder(req: ReorderRequest, user: dict = Depends(require_auth)):
    """Reorder sections by their IDs."""
    session = await _verify_session_ownership(req.sessionId, user)

    html = _get_page_html(session, req.pageSlug)
    new_html = reorder_sections(html, req.newOrder)
    _set_page_html(session, new_html, req.pageSlug)
    await redis_save_session(req.sessionId, session)

    return {"success": True, "html": new_html, "css": session["css"], "js": session.get("js", "")}


@router.post("/delete")
async def delete(req: DeleteRequest, user: dict = Depends(require_auth)):
    """Remove a section from the website."""
    session = await _verify_session_ownership(req.sessionId, user)

    html = _get_page_html(session, req.pageSlug)
    new_html = remove_section(html, req.sectionId)
    _set_page_html(session, new_html, req.pageSlug)
    await redis_save_session(req.sessionId, session)

    return {"success": True, "html": new_html, "css": session["css"], "js": session.get("js", "")}


@router.post("/duplicate")
async def dup(req: DuplicateRequest, user: dict = Depends(require_auth)):
    """Duplicate a section."""
    session = await _verify_session_ownership(req.sessionId, user)

    html = _get_page_html(session, req.pageSlug)
    new_html = duplicate_section(html, req.sectionId)
    _set_page_html(session, new_html, req.pageSlug)
    await redis_save_session(req.sessionId, session)

    return {"success": True, "html": new_html, "css": session["css"], "js": session.get("js", "")}


@router.post("/regenerate")
async def regenerate(req: RegenerateRequest, user: dict = Depends(require_auth)):
    """Regenerate a single section with AI — fresh content, same design system."""
    import logging
    import time

    _logger = logging.getLogger(__name__)
    t0 = time.time()

    _logger.info(
        f'🟡 Section Regenerate Request → id="{sanitize_log(req.sectionId)}", prompt="{sanitize_log((req.prompt or "")[:80])}", pageSlug="{sanitize_log(req.pageSlug)}"'
    )

    if req.prompt:
        moderation = check_prompt_safety(req.prompt)
        if not moderation["safe"]:
            raise HTTPException(status_code=400, detail=moderation["reason"])

    session = await _verify_session_ownership(req.sessionId, user)

    _logger.info(
        f"📄 Session → multipage={session.get('multipage')}, pages={list(session.get('pages', {}).keys())}, pageSlug={sanitize_log(req.pageSlug)}"
    )
    page_html = _get_page_html(session, req.pageSlug)
    existing_section = extract_section_html(page_html, req.sectionId)
    if not existing_section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Detect section type from the parsed sections
    all_sections = parse_sections(page_html)
    section_meta = next((s for s in all_sections if s["id"] == req.sectionId), None)
    section_type = section_meta["type"] if section_meta else "section"
    _logger.info(f'🧠 Understanding Intent → Editing "{section_type}" section ({len(existing_section):,} chars)')
    _logger.info(f"📦 Page Context → {len(all_sections)} sections: {', '.join(s['type'] for s in all_sections)}")

    ds_context = ""
    if session.get("design_system"):
        ds_context = design_system_to_prompt_context(session["design_system"])

    variant_context = ""
    if req.variantKey:
        from app.utils.components import get_variant_prompt

        vp = get_variant_prompt("", req.variantKey)
        for comp_type in [
            "hero",
            "navbar",
            "features",
            "testimonials",
            "pricing",
            "cta",
            "contact",
            "footer",
            "faq",
            "stats",
            "gallery",
            "team",
        ]:
            if req.variantKey.startswith(comp_type):
                vp = get_variant_prompt(comp_type, req.variantKey)
                break
        if vp:
            variant_context = f"\nNEW VARIANT:\n{vp}"

    client = get_anthropic_client()

    # Extract CSS rules relevant to this section + CSS vars
    section_css = _extract_section_css(session["css"], req.sectionId, existing_section)

    # Extract :root CSS variables for design consistency
    import re as _regen_re

    root_match = _regen_re.search(r":root\s*\{([^}]+)\}", session["css"])
    css_vars = (":root {" + root_match.group(1) + "}") if root_match else ""

    # Build the brand context from session plan if available
    brand_ctx = ""
    if session.get("plan"):
        plan = session["plan"]
        if isinstance(plan, str):
            try:
                import json

                plan = json.loads(plan)
            except Exception:
                plan = {}
        brand = plan.get("brand", {})
        if brand:
            brand_ctx = f"\nBRAND: {brand.get('name', '')} — {brand.get('industry', '')} — {brand.get('tagline', '')}"

    # Detect if this is a modal/popup request → use pre-built template
    is_modal_request = False
    modal_template = None
    modal_keywords = [
        "modal",
        "popup",
        "pop-up",
        "learn more",
        "detail",
        "expand",
        "click to see",
        "more info",
        "read more",
    ]
    prompt_lower = (req.prompt or "").lower()
    if any(kw in prompt_lower for kw in modal_keywords) and section_type in (
        "services",
        "features",
        "team",
        "pricing",
        "gallery",
    ):
        is_modal_request = True
        _logger.info("🎯 Modal Request Detected → Using pre-built detail modal template")
        from app.utils.interactive_templates import get_detail_modal_prompt, get_detail_modal_template

        modal_template = get_detail_modal_template()
        # Override the system prompt to only add data attributes
        system_prompt = f"""You are an expert frontend developer. You are adding interactive detail modals to a website section.

{get_detail_modal_prompt()}

CURRENT SECTION HTML:
{existing_section}

{brand_ctx}

IMPORTANT: Output ONLY the section HTML with added data-detail-* attributes in a ```html code block. Do NOT restructure or redesign the section. Do NOT add <script> or <style> tags. ONLY add data attributes."""
    else:
        from app.utils.animations import get_animation_prompt_compact
        _anim_ref = get_animation_prompt_compact()
        system_prompt = f"""You are an expert frontend developer editing a section of a website.

TASK: Apply the user's requested changes to this {section_type} section.
- If the user asks to change STYLE, EFFECTS, or ANIMATIONS → change ONLY those. Keep ALL existing text, images, and content exactly the same.
- If the user asks to change CONTENT or TEXT → change only the text they mention.
- If the user asks to "regenerate" or "rewrite" → then write fresh content.
- DEFAULT: Keep existing content unchanged unless the user explicitly asks to change it.

{_anim_ref}

TOKEN BUDGET: You have limited output tokens. Be CONCISE:
- For modals/popups: use a SINGLE reusable modal container + JS to populate it dynamically. Do NOT create 6 separate modal HTML blocks.
- Minimize repeated HTML — use data attributes and JS to handle variations.
- Keep the section roughly the same size as the original ({len(existing_section):,} chars). If adding modals, the HTML should not exceed 2.5x the original size.

CURRENT SECTION HTML:
{existing_section}

CSS VARIABLES (use these for colors):
{css_vars if css_vars else "(see page <style> block)"}

SECTION-SPECIFIC CSS:
{section_css if section_css else "(styles are in the page <style> block)"}

PAGE CONTEXT:
Sections on this page: {", ".join(s["type"] for s in all_sections)}
{brand_ctx}
{ds_context}
{variant_context}

RULES:
- Output HTML in ```html block, CSS in ```css block
- You MUST include a ```css block with ALL CSS needed for the section — grid layouts, custom classes, animations, floating elements, etc. Without CSS the layout will be broken. This is NOT optional.
- KEEP data-section-id="{req.sectionId}" on the root element
- KEEP data-section-type="{section_type}" on the root element
- Use the SAME design system (colors, fonts, spacing, radius) as the existing section
- Use the CSS classes from the page's <style> block + CSS custom properties (var(--primary), etc.)
- Do NOT use Tailwind utility classes. Use semantic class names.
- Do NOT generate large inline SVGs or decorative clip-path shapes
- KEEP existing text/images unless the user explicitly asks to change them
- For images, keep any existing image URLs from the current section. For NEW images, use placeholder format: src="{{{{IMG:descriptive keywords}}}}" (e.g. src="{{{{IMG:modern office workspace}}}}")
- Output ONLY the section HTML (no full page, no wrappers)
- ALWAYS wrap your HTML output in ```html code fences, CSS in ```css code fences, and JavaScript in ```js code fences
- NEVER put <script> tags inside the HTML block — put all JavaScript in a separate ```js code block
- If the request involves interactive behavior (modals, popups, toggles), implement it with HTML+CSS (use hidden checkboxes, :target, or details/summary) OR put the JS functions in a separate ```js code block
- Your ```css block must include ALL CSS needed — it fully replaces previous section CSS

SECTION SIZE CONSTRAINTS (CRITICAL — prevents layout breakage):
- Hero sections: max height 80vh. NEVER make a hero taller than viewport.
- All other sections: reasonable height, no min-h-screen or min-h-[100vh] unless the current section already uses it.
- Do NOT add excessive padding or margins that make a section abnormally tall.
- Keep the section roughly the same visual size as the original.

REQUIRED ELEMENTS BY SECTION TYPE (CRITICAL — never omit these):
- HERO section MUST contain: an <h1> heading (the main page title) with PLAIN TEXT content (NOT Typed.js, NOT data-typed, NOT empty spans that rely on JavaScript to fill in text — the heading must be readable without JS), a subtitle/description paragraph, and at least one CTA button. NEVER put Typed.js or animated typing inside the H1 tag — if you want typing effects, put them in a separate element below the H1.
- HERO LAYOUT: For split heroes (.hero-split-grid), content MUST be TEXT on LEFT and IMAGE on RIGHT. Do NOT push all elements to one side leaving the other empty. Do NOT use float, margin-left:auto, text-align:right, or justify-content:flex-end to shift content to the right. Keep the existing grid structure. For centered heroes, use .hero-center-content. For background-image heroes, use .hero-bg-cover with an overlay.
- FEATURES section MUST contain: a section title (<h2>), and at least 3 feature items.
- TESTIMONIALS section MUST contain: a section title (<h2>), and at least 2 testimonial quotes.
- CTA section MUST contain: a heading, description text, and at least one button.
- CONTACT section MUST contain: a heading and a contact form or contact info.
- If the original section has an element, the regenerated version MUST also have it unless the user explicitly asked to remove it.

IMAGE HANDLING (CRITICAL — follow exactly):
- "Add background image" = use CSS background-image on the section wrapper. Do NOT also add an <img> tag.
  Example: style="background-image: url('{{{{IMG:creative workspace modern}}}}'); background-size: cover; background-position: center;"
  Add a semi-transparent overlay div (max 40% opacity) for text readability.
- "Add image" or "change image" = use an <img> tag in the layout.
- NEVER add BOTH a background-image AND a foreground <img> tag for the same visual purpose.
- Background images on hero: use background-size: cover; background-position: center; with overlay. Keep text content the SAME size.
- Image queries must be SPECIFIC to the industry (e.g. "creative design studio workspace" for portfolio, "dental clinic modern interior" for dental). NEVER use generic queries like "space earth" or "abstract technology".

CRITICAL — JS-DEPENDENT CLASS NAMES (do NOT rename these):
- Navbar: .nav-links, .nav-toggle, .nav-scrolled
- FAQ: .faq-item, .faq-question, .faq-answer
- Testimonial slider: .testimonial-slider, .testimonial-slide, .slider-dot
- Image carousel: .carousel-container, .carousel-track, .carousel-slide, .carousel-prev, .carousel-next, .carousel-dot
- Gallery: #gallery-lightbox, .gallery-item, .lightbox-image, .lightbox-close, .lightbox-prev, .lightbox-next
- Service modals: .modal-trigger, .detail-modal, .modal-close, data-modal attribute
- Stats counter: .stat-number
- Footer year: #year
- Back to top: #back-to-top, .progress-ring
- Search: .search-toggle, .search-dropdown, .search-container

USER REQUEST: {req.prompt}"""

    _logger.info(
        f"🚀 Executing Step → Sending {section_type} section + edit request to LLM ({len(system_prompt):,} chars prompt)"
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": req.prompt
                if req.prompt
                else f"Refresh this {section_type} section — keep the same layout and design but improve the content.",
            }
        ],
    )

    raw_text = response.content[0].text
    _logger.info(f"📝 Raw Response → {len(raw_text):,} chars, starts with: {raw_text[:120]!r}")

    from app.routes.generator import parse_code_blocks

    result = parse_code_blocks(raw_text)

    # Fallback: if no code blocks found, try to extract HTML directly
    if not result.get("html"):
        # Check if the response itself looks like HTML (starts with < tag)
        stripped = raw_text.strip()
        if stripped.startswith("<") and (
            "data-section" in stripped or "<section" in stripped or "<div" in stripped or "<nav" in stripped
        ):
            _logger.info("🔄 Fallback → Response is raw HTML without code fences")
            result["html"] = stripped
        else:
            _logger.error(
                f"❌ Regenerate Failed → LLM returned no HTML for {section_type} section. Raw (first 500): {raw_text[:500]!r}"
            )
            raise HTTPException(status_code=500, detail="Failed to regenerate section")

    # Debug: write raw response to file for inspection
    import os as _dbg_os

    _dbg_dir = f"/tmp/meydan_debug/regen_{req.sectionId}"
    _dbg_os.makedirs(_dbg_dir, exist_ok=True)
    async with aiofiles.open(f"{_dbg_dir}/raw_response.txt", "w") as f:
        await f.write(raw_text)
    async with aiofiles.open(f"{_dbg_dir}/parsed_html.html", "w") as f:
        await f.write(result.get("html", ""))
    async with aiofiles.open(f"{_dbg_dir}/parsed_js.js", "w") as f:
        await f.write(result.get("js", ""))

    # Extract <script> tags from HTML and move to JS result
    import re as _script_re

    script_tags = _script_re.findall(r"<script[^>]*>(.*?)</script>", result.get("html", ""), _script_re.DOTALL)
    if script_tags:
        extracted_js = "\n".join(s.strip() for s in script_tags if s.strip())
        result["html"] = _script_re.sub(
            r"<script[^>]*>.*?</script>", "", result["html"], flags=_script_re.DOTALL
        ).strip()
        if extracted_js:
            result["js"] = (result.get("js") or "") + "\n" + extracted_js
            _logger.info(
                f"🔧 Extracted {len(script_tags)} <script> tag(s) from HTML → JS ({len(extracted_js):,} chars)"
            )

    # Ensure regenerated HTML is a single complete section element
    # Find the root element's closing tag to prevent unclosed tags from swallowing other sections
    html_content = result.get("html", "")
    root_tag_match = _script_re.match(r"^<(section|div|nav|header|footer|aside|article)\b", html_content)
    if root_tag_match:
        root_tag = root_tag_match.group(1)
        # Count open/close tags to find where the root element ends
        depth = 0
        tag_pattern = _script_re.compile(rf"<(/?)({root_tag})\b[^>]*/?>")
        last_valid_end = len(html_content)
        for m in tag_pattern.finditer(html_content):
            if m.group(1) == "/":
                depth -= 1
            else:
                # Skip self-closing tags
                if not m.group(0).endswith("/>"):
                    depth += 1
            if depth == 0:
                last_valid_end = m.end()
                break
        if last_valid_end < len(html_content):
            _logger.info(f"🔧 Trimmed HTML at root element close: {len(html_content):,} → {last_valid_end:,} chars")
            result["html"] = html_content[:last_valid_end]

    _logger.info(
        f"📦 LLM Response → HTML={len(result.get('html', '')):,} chars, CSS={len(result.get('css', '')):,} chars, JS={len(result.get('js', '')):,} chars"
    )

    # Validate regenerated HTML has required attributes
    result["html"] = _validate_regen_html(result["html"], req.sectionId, section_type)

    # Resolve {{IMG:query}} placeholders to real image URLs
    if "{{IMG:" in result["html"]:
        img_count = result["html"].count("{{IMG:")
        _logger.info(f"🖼️ Resolving Images → {img_count} image placeholders in regenerated section")
        try:
            from app.utils.image_resolver import resolve_image_placeholders

            result["html"] = await resolve_image_placeholders(result["html"])
        except Exception as e:
            _logger.warning(f"❌ Image Resolution Failed → {e}")

    new_html = replace_section_html(page_html, req.sectionId, result["html"])

    # Safety check: verify section count didn't drop (broken HTML)
    original_count = len(all_sections)
    new_sections_check = parse_sections(new_html)
    if len(new_sections_check) < original_count - 1:
        _logger.error(
            f"❌ Section Count Mismatch → was {original_count}, now {len(new_sections_check)} — rejecting regeneration"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Regeneration broke page structure ({original_count} → {len(new_sections_check)} sections). Try again.",
        )

    # Merge CSS using marker-based replacement (prevents bloat)
    new_css = session["css"]
    if result.get("css"):
        new_css = _strip_section_css(new_css, req.sectionId)
        new_css = _merge_section_css(new_css, req.sectionId, result["css"])

    # If modal request, inject pre-built modal CSS (JS is injected by Preview.jsx)
    if is_modal_request and modal_template:
        new_css = new_css + "\n\n/* Detail Modal */\n" + modal_template["css"]
        _logger.info("📦 Injected pre-built detail modal CSS")

    _set_page_html(session, new_html, req.pageSlug)
    session["css"] = new_css
    if result.get("js"):
        from app.routes.generator import validate_js

        try:
            validated_js = validate_js(result["js"])
        except Exception:
            validated_js = result["js"]
        session["js"] = session.get("js", "") + "\n" + validated_js

    await redis_save_session(req.sessionId, session)

    sections = parse_sections(new_html)
    duration = int((time.time() - t0) * 1000)
    _logger.info(
        f"✅ Section Regenerate Complete → {section_type} ({req.sectionId}) in {duration}ms ({len(existing_section):,} → {len(result['html']):,} chars)"
    )

    return {
        "success": True,
        "html": new_html,
        "css": new_css,
        "js": session.get("js", ""),
        "sections": sections,
    }


@router.post("/update-text")
async def update_text(req: UpdateTextRequest, user: dict = Depends(require_auth)):
    """Update text content within a section without AI (direct string replacement).
    Sanitizes input to prevent XSS injection + content moderation.
    """
    # Check all new text for restricted content
    all_text = " ".join(c.get("newText", "") for c in req.changes)
    if all_text.strip():
        moderation = check_prompt_safety(all_text)
        if not moderation["safe"]:
            raise HTTPException(status_code=400, detail=moderation["reason"])

    session = await _verify_session_ownership(req.sessionId, user)

    html = _get_page_html(session, req.pageSlug)

    for change in req.changes:
        old_text = change.get("oldText", "")
        new_text = change.get("newText", "")
        if old_text and new_text and old_text != new_text:
            # Sanitize: strip all HTML tags from new_text to prevent XSS
            sanitized = _sanitize_text_input(new_text)
            html = html.replace(old_text, sanitized, 1)

    _set_page_html(session, html, req.pageSlug)
    await redis_save_session(req.sessionId, session)

    return {
        "success": True,
        "html": html,
        "css": session["css"],
        "js": session.get("js", ""),
    }


@router.post("/insert")
async def insert_section(req: InsertSectionRequest, user: dict = Depends(require_auth)):
    """Insert a new section before or after a reference section."""
    session = await _verify_session_ownership(req.sessionId, user)

    if req.position not in ("before", "after"):
        raise HTTPException(status_code=400, detail="position must be 'before' or 'after'")

    html = _get_page_html(session, req.pageSlug)
    new_html = insert_section_at(html, req.sectionHtml, req.referenceSectionId, req.position)

    # Merge CSS if provided
    new_css = session["css"]
    if req.sectionCss:
        new_css = session["css"] + "\n\n/* Inserted section */\n" + req.sectionCss

    _set_page_html(session, new_html, req.pageSlug)
    session["css"] = new_css
    await redis_save_session(req.sessionId, session)

    sections = parse_sections(new_html)

    return {
        "success": True,
        "html": new_html,
        "css": new_css,
        "js": session.get("js", ""),
        "sections": sections,
    }


@router.post("/toggle-visibility")
async def toggle_visibility(req: ToggleVisibilityRequest, user: dict = Depends(require_auth)):
    """Show or hide a section by toggling display:none."""
    session = await _verify_session_ownership(req.sessionId, user)

    html = _get_page_html(session, req.pageSlug)
    new_html = toggle_section_visibility(html, req.sectionId, req.visible)
    _set_page_html(session, new_html, req.pageSlug)
    await redis_save_session(req.sessionId, session)

    return {
        "success": True,
        "html": new_html,
        "css": session["css"],
        "js": session.get("js", ""),
    }


@router.post("/update-style")
async def update_style(req: UpdateStyleRequest, user: dict = Depends(require_auth)):
    """Add or update inline styles on a section's root element."""
    session = await _verify_session_ownership(req.sessionId, user)

    html = _get_page_html(session, req.pageSlug)
    new_html = update_section_style(html, req.sectionId, req.styles)
    _set_page_html(session, new_html, req.pageSlug)
    await redis_save_session(req.sessionId, session)

    return {
        "success": True,
        "html": new_html,
        "css": session["css"],
        "js": session.get("js", ""),
    }


# ── Nav / Footer / Meta / Contact Config Endpoints ────────────────────


def _find_section_by_type(html: str, section_type: str) -> tuple[str | None, str | None]:
    """Find a section's ID and HTML by its type (e.g. 'navbar', 'footer', 'contact')."""
    sections = parse_sections(html)
    for s in sections:
        if s.get("type", "").lower() == section_type.lower():
            sid = s["id"]
            section_html = extract_section_html(html, sid)
            return sid, section_html
    return None, None


@router.post("/update-nav")
async def update_nav(req: UpdateNavRequest, user: dict = Depends(require_auth)):
    """Update navbar section using AI with new nav items and settings."""
    session = await _verify_session_ownership(req.sessionId, user)

    page_html = _get_page_html(session, req.pageSlug)
    section_id, existing_html = _find_section_by_type(page_html, "navbar")
    if not section_id or not existing_html:
        raise HTTPException(status_code=404, detail="Navbar section not found")

    ds_context = ""
    if session.get("design_system"):
        ds_context = design_system_to_prompt_context(session["design_system"])

    import json

    nav_items_str = json.dumps(req.items, indent=2)
    logo_instruction = (
        f"Use this logo URL: {req.logoUrl}" if req.logoUrl else "Keep any existing logo or use a text logo."
    )
    sticky_instruction = (
        "Make the navbar sticky (fixed to top on scroll)." if req.sticky else "Do NOT make the navbar sticky."
    )

    client = get_anthropic_client()
    system_prompt = f"""You are an expert web developer. Regenerate this navbar section with updated navigation items.

CURRENT NAVBAR HTML:
{existing_html}

{ds_context}

UPDATED NAV ITEMS:
{nav_items_str}

INSTRUCTIONS:
- {sticky_instruction}
- {logo_instruction}
- Items with "isButton": true should be styled as CTA buttons
- Keep data-section-id="{section_id}" and data-section-type="navbar" on the root element
- Use the page's existing CSS classes (NO Tailwind utility classes)
- Use CSS custom properties (var(--color-primary), etc.)
- Maintain consistency with the existing website design
- Output HTML in ```html block, CSS in ```css block (if needed)
- Output ONLY the navbar section HTML (no wrappers)
{SHARED_SECTION_RULES}"""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": "Regenerate the navbar with the updated navigation items and settings."}],
    )

    from app.routes.generator import parse_code_blocks

    result = parse_code_blocks(response.content[0].text)

    if not result.get("html"):
        raise HTTPException(status_code=500, detail="Failed to regenerate navbar")

    result["html"] = _validate_regen_html(result["html"], section_id, "navbar")
    new_html = replace_section_html(page_html, section_id, result["html"])
    new_css = session["css"]
    if result.get("css"):
        new_css = _merge_section_css(new_css, section_id, result["css"])

    _set_page_html(session, new_html, req.pageSlug)
    session["css"] = new_css
    if result.get("js"):
        session["js"] = session.get("js", "") + "\n" + result["js"]
    await redis_save_session(req.sessionId, session)

    return {"success": True, "html": new_html, "css": new_css, "js": session.get("js", "")}


@router.post("/update-footer")
async def update_footer(req: UpdateFooterRequest, user: dict = Depends(require_auth)):
    """Update footer section using AI with new columns, copyright, and social links."""
    session = await _verify_session_ownership(req.sessionId, user)

    page_html = _get_page_html(session, req.pageSlug)
    section_id, existing_html = _find_section_by_type(page_html, "footer")
    if not section_id or not existing_html:
        raise HTTPException(status_code=404, detail="Footer section not found")

    ds_context = ""
    if session.get("design_system"):
        ds_context = design_system_to_prompt_context(session["design_system"])

    import json

    columns_str = json.dumps(req.columns, indent=2)
    social_str = json.dumps(req.socialLinks, indent=2)
    logo_instruction = (
        f"Use this logo URL: {req.logoUrl}" if req.logoUrl else "Keep any existing logo or use a text logo."
    )

    client = get_anthropic_client()
    system_prompt = f"""You are an expert web developer. Regenerate this footer section with updated content.

CURRENT FOOTER HTML:
{existing_html}

{ds_context}

UPDATED FOOTER COLUMNS:
{columns_str}

COPYRIGHT TEXT:
{req.copyrightText}

SOCIAL LINKS:
{social_str}

INSTRUCTIONS:
- {logo_instruction}
- Keep data-section-id="{section_id}" and data-section-type="footer" on the root element
- Use the page's existing CSS classes (NO Tailwind utility classes)
- Use CSS custom properties (var(--color-primary), etc.)
- Social links should use appropriate SVG icons for each platform
- Maintain consistency with the existing website design
- Output HTML in ```html block, CSS in ```css block (if needed)
- Output ONLY the footer section HTML (no wrappers)
- Footer copyright MUST use: &copy; <span id="year"></span> {req.copyrightText} — JS sets the year automatically
{SHARED_SECTION_RULES}"""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": "Regenerate the footer with the updated columns, copyright, and social links."}
        ],
    )

    from app.routes.generator import parse_code_blocks

    result = parse_code_blocks(response.content[0].text)

    if not result.get("html"):
        raise HTTPException(status_code=500, detail="Failed to regenerate footer")

    result["html"] = _validate_regen_html(result["html"], section_id, "footer")
    new_html = replace_section_html(page_html, section_id, result["html"])
    new_css = session["css"]
    if result.get("css"):
        new_css = _merge_section_css(new_css, section_id, result["css"])

    _set_page_html(session, new_html, req.pageSlug)
    session["css"] = new_css
    if result.get("js"):
        session["js"] = session.get("js", "") + "\n" + result["js"]
    await redis_save_session(req.sessionId, session)

    return {"success": True, "html": new_html, "css": new_css, "js": session.get("js", "")}


@router.post("/update-meta")
async def update_meta(req: UpdateMetaRequest, user: dict = Depends(require_auth)):
    """Update page title, description, keywords, favicon, and WhatsApp float button."""
    import re

    session = await _verify_session_ownership(req.sessionId, user)

    # Store meta config in session
    site_meta = session.get("site_meta", {})
    if req.title is not None:
        site_meta["title"] = req.title
    if req.description is not None:
        site_meta["description"] = req.description
    if req.keywords is not None:
        site_meta["keywords"] = req.keywords
    if req.faviconUrl is not None:
        site_meta["faviconUrl"] = req.faviconUrl
    if req.whatsappNumber is not None:
        # Strip invisible Unicode control chars (U+202A, U+202C, etc.) that
        # get copied from phone apps and break wa.me URLs
        import re
        clean_wa = re.sub(r'[^\d+\s\-()]', '', req.whatsappNumber).strip()
        site_meta["whatsappNumber"] = clean_wa
    session["site_meta"] = site_meta

    html = _get_page_html(session, req.pageSlug)

    # Build SEO meta block
    seo_lines = []
    if site_meta.get("title"):
        seo_lines.append(f"<title>{site_meta['title']}</title>")
    if site_meta.get("description"):
        seo_lines.append(f'<meta name="description" content="{site_meta["description"]}">')
    if site_meta.get("keywords"):
        seo_lines.append(f'<meta name="keywords" content="{site_meta["keywords"]}">')

    if seo_lines:
        seo_block = "<!-- SEO_META -->\n" + "\n".join(seo_lines) + "\n<!-- END_SEO_META -->"
        # Replace existing SEO block or inject before </head>
        seo_pattern = re.compile(r"<!-- SEO_META -->.*?<!-- END_SEO_META -->", re.DOTALL)
        if seo_pattern.search(html):
            html = seo_pattern.sub(seo_block, html)
        elif "</head>" in html:
            html = html.replace("</head>", seo_block + "\n</head>")
        else:
            # No <head> tag — prepend
            html = seo_block + "\n" + html

    # Favicon block
    if site_meta.get("faviconUrl"):
        favicon_block = f'<!-- FAVICON -->\n<link rel="icon" href="{site_meta["faviconUrl"]}" type="image/x-icon">\n<!-- END_FAVICON -->'
        favicon_pattern = re.compile(r"<!-- FAVICON -->.*?<!-- END_FAVICON -->", re.DOTALL)
        if favicon_pattern.search(html):
            html = favicon_pattern.sub(favicon_block, html)
        elif "</head>" in html:
            html = html.replace("</head>", favicon_block + "\n</head>")
        else:
            html = favicon_block + "\n" + html

    # WhatsApp float button
    if site_meta.get("whatsappNumber"):
        number = site_meta["whatsappNumber"].replace("+", "").replace(" ", "").replace("-", "")
        wa_block = (
            "<!-- WHATSAPP_FLOAT -->\n"
            f'<a href="https://wa.me/{number}" target="_blank" rel="noopener noreferrer" '
            'class="whatsapp-float" '
            'style="position:fixed;bottom:32px;left:32px;z-index:9990;width:56px;height:56px;'
            "background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;"
            'box-shadow:0 4px 12px rgba(0,0,0,0.15);text-decoration:none;" aria-label="Chat on WhatsApp">'
            '<svg width="28" height="28" viewBox="0 0 24 24" fill="white">'
            '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>'
            '<path d="M12 0C5.373 0 0 5.373 0 12c0 2.116.553 4.103 1.519 5.832L0 24l6.335-1.652A11.943 11.943 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-1.875 0-3.615-.525-5.107-1.434l-.366-.217-3.795.99 1.013-3.7-.238-.378A9.71 9.71 0 012.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75z"/>'
            "</svg></a>\n"
            "<!-- END_WHATSAPP_FLOAT -->"
        )
        # Remove any AI-generated WhatsApp buttons first (without our markers)
        # Match <a> tags with wa.me links that are NOT inside our markers
        ai_wa_pattern = re.compile(
            r'<a\s[^>]*href=["\']https?://wa\.me/[^"\']*["\'][^>]*>.*?</a>',
            re.DOTALL | re.IGNORECASE,
        )
        # Remove AI-generated WhatsApp buttons (those outside our markers)
        wa_marker_pattern = re.compile(r"<!-- WHATSAPP_FLOAT -->.*?<!-- END_WHATSAPP_FLOAT -->", re.DOTALL)
        marker_match = wa_marker_pattern.search(html)
        if marker_match:
            # Replace existing marked block
            html = wa_marker_pattern.sub(wa_block, html)
            # Also remove any AI-generated duplicates outside the block
            before = html[:html.index("<!-- WHATSAPP_FLOAT -->")]
            after_end = html.index("<!-- END_WHATSAPP_FLOAT -->") + len("<!-- END_WHATSAPP_FLOAT -->")
            after = html[after_end:]
            before = ai_wa_pattern.sub("", before)
            after = ai_wa_pattern.sub("", after)
            html = before + html[html.index("<!-- WHATSAPP_FLOAT -->"):after_end] + after
        else:
            # Remove any AI-generated WhatsApp buttons, then inject ours
            html = ai_wa_pattern.sub("", html)
            if "</body>" in html:
                html = html.replace("</body>", wa_block + "\n</body>")
            else:
                html = html + "\n" + wa_block
    else:
        # No WhatsApp number — remove any existing WhatsApp buttons
        wa_marker_pattern = re.compile(r"<!-- WHATSAPP_FLOAT -->.*?<!-- END_WHATSAPP_FLOAT -->\n?", re.DOTALL)
        html = wa_marker_pattern.sub("", html)

    _set_page_html(session, html, req.pageSlug)
    await redis_save_session(req.sessionId, session)

    return {"success": True, "html": html, "css": session["css"], "js": session.get("js", "")}


@router.post("/update-contact")
async def update_contact(req: UpdateContactRequest, user: dict = Depends(require_auth)):
    """Update contact form configuration and regenerate the contact section."""
    import traceback as _tb
    _log = logging.getLogger(__name__)
    try:
        return await _update_contact_impl(req, user)
    except HTTPException:
        raise
    except Exception as e:
        _log.error(f"[CONTACT] update-contact crashed: {e}\n{_tb.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


async def _update_contact_impl(req: UpdateContactRequest, user: dict):
    session = await _verify_session_ownership(req.sessionId, user)

    # Merge new contact config with whatever's already there. Each field is
    # optional — passing None for any field means "leave unchanged", passing
    # an empty string means "clear this field". This lets the settings UI
    # update WhatsApp without having to also re-send the recipient email.
    existing = session.get("contact_config") or {}
    cfg = dict(existing)  # shallow copy

    if req.recipientEmail is not None:
        cfg["recipientEmail"] = req.recipientEmail
    if req.fields is not None:
        cfg["fields"] = req.fields
    if req.successMessage is not None:
        cfg["successMessage"] = req.successMessage
    cfg.setdefault("successMessage", "Thank you! Your message has been sent.")

    # Floating widgets — WhatsApp and social media URLs.
    if req.whatsappNumber is not None:
        cfg["whatsapp"] = req.whatsappNumber
    # Social: only update keys that were actually sent (not None).
    social = dict(cfg.get("social") or {})
    if req.socialFacebook is not None:
        social["facebook"] = req.socialFacebook
    if req.socialInstagram is not None:
        social["instagram"] = req.socialInstagram
    if req.socialTiktok is not None:
        social["tiktok"] = req.socialTiktok
    if req.socialLinkedin is not None:
        social["linkedin"] = req.socialLinkedin
    if req.socialYoutube is not None:
        social["youtube"] = req.socialYoutube
    if social:
        cfg["social"] = social

    session["contact_config"] = cfg

    # Re-inject the floating widgets into every page so the change is
    # immediately visible in the editor preview. Idempotent — old widgets
    # are stripped first.
    from app.utils.contact_widgets import inject_contact_widgets

    if session.get("multipage") and session.get("pages"):
        for slug in list(session["pages"].keys()):
            pg = session["pages"][slug]
            if isinstance(pg, dict) and pg.get("html"):
                pg["html"] = inject_contact_widgets(pg["html"], cfg)
        # session["html"] always mirrors the index page in multipage mode
        if "index" in session["pages"]:
            session["html"] = session["pages"]["index"]["html"]
    elif session.get("html"):
        session["html"] = inject_contact_widgets(session["html"], cfg)

    # Store recipient email in Redis session (deploy code reads it from here)
    _log = logging.getLogger(__name__)
    if req.recipientEmail:
        session["recipient_email"] = req.recipientEmail
        try:
            await redis_save_session(req.sessionId, session)
            _log.info(f"[CONTACT] recipient_email saved to session: {req.recipientEmail}")
        except Exception as e:
            _log.warning(f"[CONTACT] Failed to save session (non-critical): {e}")

        # Also save to Site record directly (for already-deployed sites)
        try:
            from app.database import async_session as _async_session
            from app.models.site import Site
            from sqlalchemy import update as _update
            # Try matching by session_id first, then by project_id
            async with _async_session() as db:
                result = await db.execute(
                    _update(Site).where(Site.session_id == req.sessionId).values(recipient_email=req.recipientEmail)
                )
                if result.rowcount == 0:
                    # No match by session_id — try by project_id
                    project_id = session.get("project_id")
                    if project_id:
                        await db.execute(
                            _update(Site).where(Site.id == project_id).values(recipient_email=req.recipientEmail)
                        )
                await db.commit()
                _log.info(f"[CONTACT] recipient_email saved to Site record ({result.rowcount} rows updated)")
        except Exception as e:
            _log.warning(f"[CONTACT] Failed to save recipient_email to Site: {e}")

    # Just save config — no form injection or LLM regeneration
    await redis_save_session(req.sessionId, session)

    page_html = _get_page_html(session, req.pageSlug)
    return {"success": True, "html": page_html, "css": session.get("css", ""), "js": session.get("js", "")}
