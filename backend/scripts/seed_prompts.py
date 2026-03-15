"""
Seed the prompt_versions table with current hardcoded prompts from the codebase.
Run: cd backend && python -m scripts.seed_prompts
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, get_db, async_session
from app.models.prompt_version import PromptVersion
from sqlalchemy import select, func


# Import prompts from codebase
from app.utils.prompt_pipeline import (
    PROMPT_ENHANCE_SYSTEM,
    PLAN_SYSTEM_PROMPT,
    TEMPLATE_CUSTOMIZE_PROMPT,
    ADD_PAGE_HTML_PROMPT,
    JS_GEN_SYSTEM_PROMPT,
    ITERATION_SYSTEM_PROMPT,
    COMPONENT_ROUTER_PROMPT,
    COMPONENT_EDIT_PROMPT,
    STYLE_EDIT_PROMPT,
    APPEND_SECTION_PROMPT,
)

PROMPTS = {
    "enhance_system": PROMPT_ENHANCE_SYSTEM,
    "plan_system": PLAN_SYSTEM_PROMPT,
    "template_customize": TEMPLATE_CUSTOMIZE_PROMPT,
    "add_page_html": ADD_PAGE_HTML_PROMPT,
    "js_gen_system": JS_GEN_SYSTEM_PROMPT,
    "iteration_system": ITERATION_SYSTEM_PROMPT,
    "component_router": COMPONENT_ROUTER_PROMPT,
    "component_edit": COMPONENT_EDIT_PROMPT,
    "style_edit": STYLE_EDIT_PROMPT,
    "append_section": APPEND_SECTION_PROMPT,
}


async def seed():
    async with async_session() as db:
        for key, content in PROMPTS.items():
            # Check if already seeded
            existing = await db.execute(
                select(func.count()).select_from(PromptVersion).where(PromptVersion.prompt_key == key)
            )
            if existing.scalar() > 0:
                print(f"  SKIP {key} (already exists)")
                continue

            prompt = PromptVersion(
                prompt_key=key,
                version=1,
                content=content.strip(),
                is_active=True,
            )
            db.add(prompt)
            print(f"  SEED {key} v1")

        await db.commit()
        print(f"\nDone — seeded {len(PROMPTS)} prompt keys.")


if __name__ == "__main__":
    asyncio.run(seed())
