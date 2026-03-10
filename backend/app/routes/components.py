"""
Component variant routes — browse and generate individual section components.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.utils.auth import decode_access_token
from app.utils.components import (
    get_all_components_summary,
    get_variant_detail,
    get_variant_prompt,
    get_component_types,
    COMPONENT_VARIANTS,
)
from app.utils.design_system import design_system_to_prompt_context, design_system_to_css_vars
from app.utils.llm_clients import get_anthropic_client
from app.utils.section_parser import replace_section_html, parse_sections
from app.utils.session_store import get_session as redis_get_session, save_session as redis_save_session

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


# ── Schemas ─────────────────────────────────────────────────────────────

class GenerateComponentRequest(BaseModel):
    sessionId: str
    componentType: str
    variantKey: str
    content: str | None = None  # Optional custom content instructions
    designSystem: dict | None = None


class SwapComponentRequest(BaseModel):
    sessionId: str
    sectionId: str
    componentType: str
    variantKey: str


# ── Endpoints ───────────────────────────────────────────────────────────

@router.get("/")
async def list_components(user: dict = Depends(require_auth)):
    """List all component types with their variants."""
    return {"components": get_all_components_summary()}


@router.get("/types")
async def list_component_types(user: dict = Depends(require_auth)):
    """List component type keys."""
    return {"types": get_component_types()}


@router.get("/{component_type}")
async def get_component_variants(component_type: str, user: dict = Depends(require_auth)):
    """Get all variants for a specific component type."""
    comp = COMPONENT_VARIANTS.get(component_type)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Component type '{component_type}' not found")
    variants = []
    for key, var in comp["variants"].items():
        variants.append({"key": key, "name": var["name"], "description": var["description"]})
    return {"component_type": component_type, "name": comp["name"], "variants": variants}


@router.post("/generate")
async def generate_component(req: GenerateComponentRequest, user: dict = Depends(require_auth)):
    """Generate a single section HTML using a specific component variant."""
    variant_prompt = get_variant_prompt(req.componentType, req.variantKey)
    if not variant_prompt:
        raise HTTPException(status_code=404, detail="Variant not found")

    session = await redis_get_session(req.sessionId) if req.sessionId else None

    # Build design system context
    ds_context = ""
    if req.designSystem:
        ds_context = design_system_to_prompt_context(req.designSystem)
    elif session and session.get("design_system"):
        ds_context = design_system_to_prompt_context(session["design_system"])

    # Build content context
    content_hint = ""
    if req.content:
        content_hint = f"\nCONTENT: {req.content}"
    elif session:
        content_hint = f"\nEXISTING SITE CONTEXT: The website is about: {session.get('niche', 'business')}"

    client = get_anthropic_client()

    system_prompt = f"""You are an expert web developer. Generate a SINGLE HTML section component with its CSS.

{variant_prompt}
{ds_context}
{content_hint}

RULES:
- Output the HTML in a ```html block
- Output the CSS in a ```css block
- Use semantic HTML5
- Make it fully responsive
- Use CSS custom properties (var(--color-primary), etc.) if a design system is provided
- Include real-looking placeholder content
- Images: use Pexels URLs (https://images.pexels.com/photos/...) in <img> tags, NOT as CSS backgrounds
- Include relevant JavaScript in a ```js block if the component needs interactivity (tabs, toggles, accordions)
- Output ONLY the section HTML (no <html>, <head>, <body> wrappers)"""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Generate a {req.variantKey} component"}],
    )

    from app.routes.generator import parse_code_blocks
    result = parse_code_blocks(response.content[0].text)

    return {
        "success": True,
        "html": result.get("html", ""),
        "css": result.get("css", ""),
        "js": result.get("js", ""),
        "componentType": req.componentType,
        "variantKey": req.variantKey,
    }


@router.post("/preview-swap")
async def preview_swap(req: SwapComponentRequest, user: dict = Depends(require_auth)):
    """Generate preview of a variant swap WITHOUT saving to session."""
    session = await redis_get_session(req.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    variant_prompt = get_variant_prompt(req.componentType, req.variantKey)
    if not variant_prompt:
        raise HTTPException(status_code=404, detail="Variant not found")

    from app.utils.section_parser import extract_section_html
    existing_section = extract_section_html(session["html"], req.sectionId)
    if not existing_section:
        raise HTTPException(status_code=404, detail="Section not found in HTML")

    ds_context = ""
    if session.get("design_system"):
        ds_context = design_system_to_prompt_context(session["design_system"])

    # Include logo if available
    logo_context = ""
    if session.get("logo_url"):
        logo_context = f'\nUse this logo image: <img src="{session["logo_url"]}" alt="Logo" class="h-8">'

    client = get_anthropic_client()

    system_prompt = f"""You are an expert web developer. Replace a website section with a new layout variant while PRESERVING the existing content.

CURRENT SECTION HTML:
{existing_section}

NEW VARIANT TO USE:
{variant_prompt}
{ds_context}
{logo_context}

RULES:
- Keep the same text content, headings, and images from the existing section
- Apply the new layout/variant structure
- Output HTML in ```html block, CSS in ```css block
- Use semantic HTML5 and CSS custom properties
- Add data-section-id="{req.sectionId}" to the root element
- Output ONLY the section HTML (no wrappers)"""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Swap to {req.variantKey} variant"}],
    )

    from app.routes.generator import parse_code_blocks
    result = parse_code_blocks(response.content[0].text)

    return {
        "success": True,
        "html": result.get("html", ""),
        "css": result.get("css", ""),
        "js": result.get("js", ""),
        "currentHtml": existing_section,
        "currentCss": session.get("css", ""),
    }


@router.post("/swap")
async def swap_component(req: SwapComponentRequest, user: dict = Depends(require_auth)):
    """Replace a section in the current website with a new component variant."""
    session = await redis_get_session(req.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    variant_prompt = get_variant_prompt(req.componentType, req.variantKey)
    if not variant_prompt:
        raise HTTPException(status_code=404, detail="Variant not found")

    # Get the existing section's content
    from app.utils.section_parser import extract_section_html
    existing_section = extract_section_html(session["html"], req.sectionId)
    if not existing_section:
        raise HTTPException(status_code=404, detail="Section not found in HTML")

    ds_context = ""
    if session.get("design_system"):
        ds_context = design_system_to_prompt_context(session["design_system"])

    client = get_anthropic_client()

    system_prompt = f"""You are an expert web developer. Replace a website section with a new layout variant while PRESERVING the existing content.

CURRENT SECTION HTML:
{existing_section}

NEW VARIANT TO USE:
{variant_prompt}
{ds_context}

RULES:
- Keep the same text content, headings, and images from the existing section
- Apply the new layout/variant structure
- Output HTML in ```html block, CSS in ```css block
- Use semantic HTML5 and CSS custom properties
- Add data-section-id="{req.sectionId}" to the root element
- Output ONLY the section HTML (no wrappers)"""

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Swap to {req.variantKey} variant"}],
    )

    from app.routes.generator import parse_code_blocks
    result = parse_code_blocks(response.content[0].text)

    if not result.get("html"):
        raise HTTPException(status_code=500, detail="Failed to generate new component")

    # Replace the section in the full HTML
    new_html = replace_section_html(session["html"], req.sectionId, result["html"])

    # Merge CSS (append new styles)
    new_css = session["css"]
    if result.get("css"):
        new_css = session["css"] + "\n\n/* Swapped: " + req.variantKey + " */\n" + result["css"]

    # Update session
    session["html"] = new_html
    session["css"] = new_css
    if result.get("js"):
        session["js"] = session.get("js", "") + "\n\n" + result["js"]

    await redis_save_session(req.sessionId, session)

    return {
        "success": True,
        "html": new_html,
        "css": new_css,
        "js": session.get("js", ""),
    }
