"""Usage limits — enforces per-user generation and edit quotas."""

import logging

from sqlalchemy import text

from app.database import async_session

logger = logging.getLogger(__name__)


async def check_usage_limit(user_id: int, action: str) -> dict:
    """Check if user has remaining generations or edits.

    Args:
        action: "generation" or "edit"

    Returns:
        {"ok": bool, "message": str, "used": int, "max": int}
    """
    async with async_session() as db:
        result = await db.execute(
            text(
                "SELECT generation_count, edit_count, max_generations, max_edits, is_admin "
                "FROM users WHERE id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.first()
        if not row:
            return {"ok": False, "message": "User not found", "used": 0, "max": 0}

        gen_count, edit_count, max_gen, max_edits, is_admin = row

        # Admins bypass limits
        if is_admin:
            return {"ok": True, "message": "", "used": 0, "max": 0}

        if action == "generation":
            if gen_count >= max_gen:
                return {
                    "ok": False,
                    "message": f"Generation limit reached ({gen_count}/{max_gen}). Contact admin for more generations.",
                    "used": gen_count,
                    "max": max_gen,
                }
            return {"ok": True, "message": "", "used": gen_count, "max": max_gen}
        else:
            if edit_count >= max_edits:
                return {
                    "ok": False,
                    "message": f"Modification limit reached ({edit_count}/{max_edits}). Contact admin for more edits.",
                    "used": edit_count,
                    "max": max_edits,
                }
            return {"ok": True, "message": "", "used": edit_count, "max": max_edits}


async def increment_usage(user_id: int, action: str):
    """Increment generation_count or edit_count after successful completion."""
    col = "generation_count" if action == "generation" else "edit_count"
    try:
        async with async_session() as db:
            await db.execute(
                text(f"UPDATE users SET {col} = {col} + 1 WHERE id = :uid"),
                {"uid": user_id},
            )
            await db.commit()
            logger.info(f"[USAGE] user={user_id} {col} incremented")
    except Exception as e:
        logger.error(f"[USAGE] Failed to increment {col} for user={user_id}: {e}")


async def get_usage(user_id: int) -> dict:
    """Get user's current usage stats."""
    async with async_session() as db:
        result = await db.execute(
            text(
                "SELECT generation_count, edit_count, max_generations, max_edits "
                "FROM users WHERE id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.first()
        if not row:
            return {"generations_used": 0, "generations_max": 2, "edits_used": 0, "edits_max": 30}
        return {
            "generations_used": row[0],
            "generations_max": row[1],
            "edits_used": row[2],
            "edits_max": row[3],
        }
