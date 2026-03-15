"""Token budget tracking — deducts tokens from user balance after each LLM call."""

import logging
import uuid
from sqlalchemy import text
from app.database import async_session

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_BUDGET = 1_000_000


async def check_budget(user_id: int) -> dict:
    """Check if user has remaining token budget. Returns {ok, balance, used}."""
    async with async_session() as db:
        result = await db.execute(
            text("SELECT token_balance, tokens_used FROM users WHERE id = :uid"),
            {"uid": user_id},
        )
        row = result.first()
        if not row:
            return {"ok": False, "balance": 0, "used": 0}
        return {"ok": row[0] > 0, "balance": row[0], "used": row[1]}


async def deduct_tokens(user_id: int, input_tokens: int, output_tokens: int,
                         provider: str, model: str, operation: str):
    """Atomically deduct tokens from user balance and record in transaction ledger."""
    total = input_tokens + output_tokens
    if total <= 0:
        return
    try:
        async with async_session() as db:
            # Deduct from user balance
            result = await db.execute(
                text("""
                    UPDATE users
                    SET token_balance = GREATEST(token_balance - :amount, 0),
                        tokens_used = tokens_used + :amount
                    WHERE id = :uid
                    RETURNING token_balance
                """),
                {"amount": total, "uid": user_id},
            )
            row = result.first()
            balance_after = row[0] if row else 0

            # Record in transaction ledger
            await db.execute(
                text("""
                    INSERT INTO token_transactions (id, user_id, type, amount, balance_after, reason)
                    VALUES (:id, :uid, 'deduction', :amount, :balance, :reason)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "uid": user_id,
                    "amount": -total,
                    "balance": balance_after,
                    "reason": f"{provider}/{model} — {operation} ({input_tokens}in + {output_tokens}out)",
                },
            )
            await db.commit()
            logger.info(f"[TOKENS] user={user_id} deducted={total} provider={provider} model={model} op={operation}")
    except Exception as e:
        logger.error(f"[TOKENS] Failed to deduct for user={user_id}: {e}")


async def grant_tokens(user_id: int, amount: int):
    """Add tokens to a user's balance (admin action)."""
    async with async_session() as db:
        await db.execute(
            text("UPDATE users SET token_balance = token_balance + :amount WHERE id = :uid"),
            {"amount": amount, "uid": user_id},
        )
        await db.commit()


async def get_balance(user_id: int) -> dict:
    """Get user's current token balance and usage."""
    return await check_budget(user_id)
