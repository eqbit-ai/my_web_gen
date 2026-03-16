"""
Background worker — processes generation jobs from the Redis queue.

Uses the 3-stage pipeline:
  Stage 1: Plan  → LLM → JSON structure + content + layout patterns
  Stage 2: HTML  → LLM → HTML with Tailwind CSS + <style> block
  Stage 3: JS    → LLM → Interactions/animations

Run separately: python -m app.worker
"""

import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app.utils.logging_config import setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

from app.routes.generator import extract_style_block, stage_1_plan, stage_2_html, stage_3_js
from app.utils.redis_client import get_job, get_redis, update_job
from app.utils.section_parser import inject_section_ids, parse_sections


async def process_generate_job(job_id: str, payload: dict):
    """Run the 3-stage pipeline for a job."""
    prompt = payload["prompt"]

    # ── Stage 1: Plan ─────────────────────────────────────────────────
    await update_job(job_id, status="processing", progress=5, progress_message="Stage 1/3: Analyzing your request...")

    plan = await stage_1_plan(prompt, job_id)

    # ── Stage 2: HTML + Tailwind CSS ──────────────────────────────────
    await update_job(job_id, progress=30, progress_message="Stage 2/3: Building page with styles...")

    html = await stage_2_html(plan, job_id)

    if not html:
        raise Exception("Failed to generate HTML from AI")

    # Extract CSS from the <style> block
    css, html = extract_style_block(html)

    # ── Stage 3: JS ───────────────────────────────────────────────────
    await update_job(job_id, progress=70, progress_message="Stage 3/3: Adding interactions...")

    js = await stage_3_js(html, job_id)

    # ── Quality polish ────────────────────────────────────────────────
    await update_job(job_id, progress=85, progress_message="Optimizing images & SEO...")

    try:
        from app.utils.responsive_check import auto_fix_responsive

        html, css = auto_fix_responsive(html, css)
    except Exception:
        pass

    try:
        from app.utils.image_optimizer import optimize_image_tags

        html = optimize_image_tags(html)
    except Exception:
        pass

    try:
        from app.utils.form_handler import has_contact_form, inject_form_handler

        if has_contact_form(html):
            html, js = inject_form_handler(html, js)
    except Exception:
        pass

    try:
        from app.utils.seo_checker import generate_seo_tags, inject_seo_into_html

        seo_tags = generate_seo_tags(plan)
        html = inject_seo_into_html(html, seo_tags)
    except Exception:
        pass

    try:
        from app.utils.lighthouse_check import auto_fix_performance

        html, css, js = auto_fix_performance(html, css, js)
    except Exception:
        pass

    # ── Finalize ─────────────────────────────────────────────────────
    await update_job(job_id, progress=95, progress_message="Finalizing...")

    html = inject_section_ids(html)
    sections = parse_sections(html)

    # Quality scores (informational)
    quality = {}
    try:
        from app.utils.lighthouse_check import check_performance

        perf = check_performance(html, css, js)
        quality["performance_score"] = perf["score"]
        quality["issues_fixed"] = len(perf["auto_fixable"])
    except Exception:
        pass
    try:
        from app.utils.seo_checker import check_seo

        seo = check_seo(html, plan)
        quality["seo_score"] = seo["score"]
    except Exception:
        pass

    result = {
        "success": True,
        "website": {
            "html": html,
            "css": css,
            "js": js,
        },
        "sections": sections,
        "pipelineStages": ["plan", "html+css", "js", "quality"],
        "quality": quality,
    }

    await update_job(job_id, status="completed", progress=100, progress_message="Done!", result=result)

    return result


WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "1"))


async def _handle_job(job_id: str, semaphore: asyncio.Semaphore):
    """Process a single job within the concurrency semaphore."""
    async with semaphore:
        job = await get_job(job_id)
        if not job:
            logger.warning("job_not_found", extra={"job_id": job_id})
            return
        if job["status"] != "pending":
            logger.info("job_skipped", extra={"job_id": job_id, "status": job["status"]})
            return

        payload = job["payload"] if isinstance(job["payload"], dict) else json.loads(job["payload"])

        try:
            await process_generate_job(job_id, payload)
            logger.info("job_completed", extra={"job_id": job_id})
        except Exception as e:
            logger.error("job_failed", extra={"job_id": job_id, "error": str(e)}, exc_info=True)
            await update_job(job_id, status="failed", progress=0, progress_message="Failed", error=str(e))


async def worker_loop():
    """Main worker loop — processes up to WORKER_CONCURRENCY jobs in parallel."""
    r = await get_redis()
    concurrency = max(1, WORKER_CONCURRENCY)
    semaphore = asyncio.Semaphore(concurrency)
    active_tasks: set[asyncio.Task] = set()

    logger.info("worker_started", extra={
        "pipeline": "Plan → HTML+Tailwind → JS",
        "queue": "queue:generate",
        "concurrency": concurrency,
    })

    while True:
        try:
            # Clean up finished tasks
            done = {t for t in active_tasks if t.done()}
            for t in done:
                if t.exception():
                    logger.error("task_exception", extra={"error": str(t.exception())})
            active_tasks -= done

            # Wait for a slot before pulling next job
            if len(active_tasks) >= concurrency:
                await asyncio.sleep(0.5)
                continue

            item = await r.brpop("queue:generate", timeout=5)
            if item is None:
                continue

            _, job_id = item
            logger.info("job_received", extra={"job_id": job_id, "active_jobs": len(active_tasks)})

            task = asyncio.create_task(_handle_job(job_id, semaphore))
            active_tasks.add(task)

        except asyncio.CancelledError:
            logger.info("worker_shutdown — waiting for %d active jobs", len(active_tasks))
            for t in active_tasks:
                t.cancel()
            await asyncio.gather(*active_tasks, return_exceptions=True)
            break
        except Exception as e:
            logger.error("worker_loop_error", extra={"error": str(e)})
            await asyncio.sleep(2)


def main():
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
