#!/usr/bin/env python3
"""
Regenerate templates using the current generation pipeline.

Usage:
    cd backend
    python -m scripts.regenerate_templates

This generates each template through the full pipeline (plan → HTML+JS → CSS → images)
and saves the output to templates_data/.

Each template takes ~60-90 seconds to generate.
"""

import asyncio
import os
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://meydan:meydan123@localhost:5432/meydan_db")

from app.utils.prompt_pipeline import (
    build_plan_prompt,
    parse_json_response,
    build_html_prompt,
    parse_single_code_block,
    extract_section_types,
)
from app.utils.llm_clients import get_anthropic_client, get_openai_client
from app.routes.generator import (
    validate_html,
    validate_css,
    _fix_url_quotes,
    _strip_comment_markers,
    _resolve_images_safe,
    _ensure_hero_has_image,
    inject_section_ids,
)
from app.utils.patterns import get_pattern_template


TEMPLATES = {
    "restaurant": {
        "prompt": "A premium Italian restaurant called 'La Dolce Vita' in Dubai. Fine dining with handmade pasta, wood-fired pizzas, and curated Italian wines. Warm, elegant ambiance with candlelit tables. Open daily 5PM-11PM. Phone: +971501234567. Email: info@ladolcevita.ae. Address: City Walk, Dubai.",
        "niche": "restaurant",
    },
    "tech_startup": {
        "prompt": "A modern SaaS tech startup called 'NexaFlow' that provides AI-powered workflow automation for businesses. Features: smart task routing, real-time analytics, team collaboration, API integrations. Founded in 2023, backed by top VCs. Free trial available. Email: hello@nexaflow.io. Based in DIFC, Dubai.",
        "niche": "tech_startup",
    },
    "real_estate": {
        "prompt": "A luxury real estate agency called 'Skyline Properties' specializing in premium Dubai properties — penthouses, villas, waterfront apartments. Over 500 properties listed, 15 years experience, 98% client satisfaction. Services: buying, selling, rental, property management. Phone: +971559876543. Email: info@skylineproperties.ae. Office: Downtown Dubai.",
        "niche": "real_estate",
    },
    "portfolio": {
        "prompt": "A creative portfolio for 'Alex Chen', a UI/UX designer and brand strategist. 8+ years experience, worked with Nike, Spotify, Airbnb. Skills: UI/UX design, brand identity, motion graphics, prototyping. Available for freelance projects. Email: hello@alexchen.design. Based in Dubai.",
        "niche": "portfolio",
    },
    "fitness": {
        "prompt": "A premium fitness studio called 'Iron & Flow' in Dubai offering personal training, group classes (HIIT, yoga, boxing, spinning), nutrition coaching. State-of-the-art equipment, certified trainers, 24/7 access. Monthly membership from AED 499. Phone: +971504567890. Email: join@ironandflow.ae. Location: JLT, Dubai.",
        "niche": "fitness",
    },
}


async def generate_one_template(name: str, config: dict) -> bool:
    """Generate a single template through the full pipeline."""
    prompt = config["prompt"]
    niche = config["niche"]

    print(f"\n{'='*60}")
    print(f"Generating: {name}")
    print(f"{'='*60}")
    t0 = time.time()

    try:
        # Stage 1: Plan
        print("  Stage 1: Planning...")
        openai = get_openai_client()
        plan_prompt = build_plan_prompt(prompt)
        plan_response = await openai.chat.completions.create(
            model="gpt-4.1",
            temperature=0.7,
            messages=[
                {"role": "system", "content": plan_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4000,
        )
        plan_text = plan_response.choices[0].message.content
        plan = parse_json_response(plan_text)
        if not plan:
            print(f"  ❌ Plan parsing failed")
            return False
        print(f"  ✅ Plan ready — {len(plan.get('sections', []))} sections")

        # Stage 2: HTML + JS
        print("  Stage 2: Generating HTML + JS...")
        anthropic = get_anthropic_client()
        html_prompt = build_html_prompt(plan)

        response = await anthropic.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            temperature=0.5,
            system=html_prompt,
            messages=[{"role": "user", "content": "Generate the complete website HTML with embedded <style> block. Include all sections, animations, and interactions."}],
        )

        raw_html = response.content[0].text
        html = parse_single_code_block(raw_html, "html")
        if not html:
            print(f"  ❌ HTML parsing failed")
            return False

        # Validate and fix
        html = validate_html(html)
        html = inject_section_ids(html)

        # Resolve images
        print("  Stage 3: Resolving images...")
        html = await _resolve_images_safe(html, niche_key=niche)

        # Final quote fix
        html = _fix_url_quotes(html)

        # Save
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "templates_data", f"{name}.html"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        duration = int(time.time() - t0)
        size = len(html)
        print(f"  ✅ Done! {size:,} chars in {duration}s → {output_path}")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("Template Regeneration Script")
    print(f"Generating {len(TEMPLATES)} templates...\n")

    results = {}
    for name, config in TEMPLATES.items():
        success = await generate_one_template(name, config)
        results[name] = success

    print(f"\n{'='*60}")
    print("RESULTS:")
    for name, success in results.items():
        print(f"  {'✅' if success else '❌'} {name}")

    succeeded = sum(1 for v in results.values() if v)
    print(f"\n{succeeded}/{len(results)} templates regenerated successfully")


if __name__ == "__main__":
    asyncio.run(main())
