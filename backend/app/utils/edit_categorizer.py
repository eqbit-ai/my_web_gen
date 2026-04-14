"""
Phase B — auto-categorize edit prompts. Cheap (~$0.0001/prompt with Haiku).
Run from `POST /api/admin/edit-logs/categorize` or as a periodic worker.

Categories chosen to be useful for prompt-routing analysis:
    rebrand          — change business identity (name, niche, type)
    color_change     — global colors / palette / theme
    copy_edit        — change text in one section
    image_swap       — change/replace an image
    add_section      — add new section (testimonials, pricing, etc.)
    remove_section   — remove an existing section
    layout_change    — change layout/structure of a section
    style_change     — fonts, spacing, button shapes (visual but not color)
    deploy_settings  — about deploying, domains, SEO meta
    ambiguous        — anything else / classifier not confident
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.edit_log import EditLog

logger = logging.getLogger(__name__)


CATEGORIES = [
    "rebrand", "color_change", "copy_edit", "image_swap",
    "add_section", "remove_section", "layout_change", "style_change",
    "deploy_settings", "ambiguous",
]

SYSTEM = (
    "You are a classifier. Given a single user prompt that asked the AI website "
    "builder to make an edit, return ONLY one of these labels with no other text:\n"
    + "\n".join(f"- {c}" for c in CATEGORIES)
    + "\nIf the prompt could plausibly be more than one, pick the dominant one. "
    "If genuinely unclear, return 'ambiguous'."
)


async def _classify(prompt: str) -> str:
    from app.utils.llm_clients import get_anthropic_client
    client = get_anthropic_client()
    msg = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8,
        temperature=0,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt[:2000]}],
    )
    parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
    out = "".join(parts).strip().lower().split()[0] if parts else "ambiguous"
    out = out.strip(".,'\"")
    return out if out in CATEGORIES else "ambiguous"


async def categorize_pending(db: AsyncSession, batch: int = 50) -> int:
    """Tag up to `batch` uncategorized rows. Returns rows updated."""
    result = await db.execute(
        select(EditLog.id, EditLog.prompt)
        .where(EditLog.category.is_(None))
        .order_by(EditLog.created_at.desc())
        .limit(batch)
    )
    rows = result.all()
    updated = 0
    for row_id, prompt in rows:
        try:
            cat = await _classify(prompt or "")
        except Exception:
            logger.exception("[categorize] failed on row %s", row_id)
            continue
        await db.execute(
            update(EditLog).where(EditLog.id == row_id).values(category=cat)
        )
        updated += 1
    if updated:
        await db.commit()
    logger.info(f"[categorize] tagged {updated}/{len(rows)} rows")
    return updated
