"""
Admin token management endpoints.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.token_request import TokenRequest
from app.models.token_transaction import TokenTransaction
from app.models.user import User
from app.utils.audit_log import log_event_bg

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Tokens"])


# ── Schemas ──────────────────────────────────────────────────────────


class GrantTokensRequest(BaseModel):
    user_id: int
    amount: int
    reason: str = "Admin grant"
    expires_at: datetime | None = None


# ── Endpoints ────────────────────────────────────────────────────────


@router.get("/tokens/transactions")
async def list_token_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: int | None = Query(default=None),
    token_type: str | None = Query(default=None),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Paginated token transaction ledger with optional filters."""
    try:
        query = select(TokenTransaction)

        if user_id:
            query = query.where(TokenTransaction.user_id == user_id)
        if token_type:
            query = query.where(TokenTransaction.type == token_type)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(TokenTransaction.created_at.desc()).limit(limit).offset(offset)
        )
        txns = result.scalars().all()

        # Fetch user emails
        user_ids = list({t.user_id for t in txns})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        return {
            "transactions": [
                {
                    "id": str(t.id),
                    "user_id": t.user_id,
                    "user_email": user_map.get(t.user_id, ""),
                    "type": t.type,
                    "amount": t.amount,
                    "balance_after": t.balance_after,
                    "reason": t.reason,
                    "reference_id": t.reference_id,
                    "expires_at": _serialize_datetime(t.expires_at),
                    "created_at": _serialize_datetime(t.created_at),
                    "created_by": t.created_by,
                }
                for t in txns
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list token transactions: %s", e)
        return {"transactions": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.get("/tokens/transactions/{user_id}")
async def get_user_transactions(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get token transaction history for a single user."""
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        count_result = await db.execute(
            select(func.count(TokenTransaction.id)).where(TokenTransaction.user_id == user_id)
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(TokenTransaction)
            .where(TokenTransaction.user_id == user_id)
            .order_by(TokenTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        txns = result.scalars().all()

        return {
            "user_id": user_id,
            "user_email": user.email,
            "current_balance": getattr(user, "token_balance", 0),
            "transactions": [
                {
                    "id": str(t.id),
                    "type": t.type,
                    "amount": t.amount,
                    "balance_after": t.balance_after,
                    "reason": t.reason,
                    "reference_id": t.reference_id,
                    "expires_at": _serialize_datetime(t.expires_at),
                    "created_at": _serialize_datetime(t.created_at),
                }
                for t in txns
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Failed to fetch user transactions: %s", e)
        return {"error": str(e)}


@router.post("/tokens/grant")
async def grant_tokens(
    req: GrantTokensRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Grant tokens to a user with optional expiry. Creates a TokenTransaction record and updates user balance."""
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_balance = getattr(user, "token_balance", 0)
    new_balance = current_balance + req.amount

    try:
        # Update user balance
        await db.execute(
            update(User)
            .where(User.id == req.user_id)
            .values(token_balance=User.token_balance + req.amount)
        )

        # Create transaction record
        txn = TokenTransaction(
            user_id=req.user_id,
            type="grant",
            amount=req.amount,
            balance_after=new_balance,
            reason=req.reason,
            expires_at=req.expires_at,
            created_by=admin.get("user_id"),
        )
        db.add(txn)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to grant tokens: {e}") from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="admin_grant_tokens",
        resource_type="token",
        resource_id=str(req.user_id),
        details={
            "amount": req.amount,
            "new_balance": new_balance,
            "reason": req.reason,
            "email": user.email,
            "expires_at": _serialize_datetime(req.expires_at),
        },
    )

    return {
        "message": f"Granted {req.amount:,} tokens to {user.email}",
        "new_balance": new_balance,
        "transaction_id": str(txn.id),
    }


@router.get("/tokens/pool")
async def token_pool_stats(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform-wide token statistics."""
    try:
        result = await db.execute(text("""
            SELECT
                COUNT(*) as total_users,
                COALESCE(SUM(tokens_used), 0) as total_consumed,
                COALESCE(SUM(token_balance), 0) as total_remaining,
                COALESCE(AVG(tokens_used), 0) as avg_per_user
            FROM users
        """))
        row = result.first()

        # Total granted from transactions
        grant_result = await db.execute(
            select(func.coalesce(func.sum(TokenTransaction.amount), 0))
            .where(TokenTransaction.type == "grant")
        )
        total_granted = grant_result.scalar() or 0

        # Users with zero balance
        zero_result = await db.execute(
            text("SELECT COUNT(*) FROM users WHERE token_balance <= 0")
        )
        zero_balance = zero_result.scalar() or 0

        # Top consumers
        top_result = await db.execute(text("""
            SELECT id, email, full_name, company_name, tokens_used, token_balance
            FROM users ORDER BY tokens_used DESC LIMIT 10
        """))
        top_users = [
            {
                "id": r[0], "email": r[1], "full_name": r[2],
                "company_name": r[3], "tokens_used": r[4], "token_balance": r[5],
            }
            for r in top_result.fetchall()
        ]

        # Burn rate (last 7 days)
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        burn_result = await db.execute(
            select(func.coalesce(func.sum(TokenTransaction.amount), 0))
            .where(
                TokenTransaction.type == "deduction",
                TokenTransaction.created_at >= seven_days_ago,
            )
        )
        weekly_burn = abs(burn_result.scalar() or 0)

        return {
            "total_users": row[0] or 0,
            "total_granted": total_granted,
            "total_consumed": row[1] or 0,
            "total_remaining": row[2] or 0,
            "avg_per_user": round(row[3] or 0),
            "users_zero_balance": zero_balance,
            "weekly_burn_rate": weekly_burn,
            "daily_burn_rate": round(weekly_burn / 7) if weekly_burn else 0,
            "top_consumers": top_users,
        }
    except Exception as e:
        logger.warning("Failed to get token pool stats: %s", e)
        return {"error": str(e)}


@router.get("/tokens/expiring")
async def expiring_tokens(
    days: int = Query(default=30, ge=1, le=365),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List token grants expiring within N days."""
    try:
        cutoff = datetime.now(UTC) + timedelta(days=days)

        result = await db.execute(
            select(TokenTransaction)
            .where(
                TokenTransaction.type == "grant",
                TokenTransaction.expires_at.isnot(None),
                TokenTransaction.expires_at <= cutoff,
                TokenTransaction.expires_at >= datetime.now(UTC),
            )
            .order_by(TokenTransaction.expires_at.asc())
        )
        txns = result.scalars().all()

        # Fetch user emails
        user_ids = list({t.user_id for t in txns})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_map = {r[0]: r[1] for r in user_result.fetchall()}

        return {
            "expiring_within_days": days,
            "count": len(txns),
            "grants": [
                {
                    "id": str(t.id),
                    "user_id": t.user_id,
                    "user_email": user_map.get(t.user_id, ""),
                    "amount": t.amount,
                    "reason": t.reason,
                    "expires_at": _serialize_datetime(t.expires_at),
                    "created_at": _serialize_datetime(t.created_at),
                }
                for t in txns
            ],
        }
    except Exception as e:
        logger.warning("Failed to fetch expiring tokens: %s", e)
        return {"expiring_within_days": days, "count": 0, "grants": [], "error": str(e)}


# ── Token Requests (user → admin) ───────────────────────────────────


class ReviewTokenRequest(BaseModel):
    action: str  # approve / reject
    admin_note: str | None = None
    grant_amount: int | None = None  # override requested amount


@router.get("/tokens/requests")
async def list_token_requests(
    status_filter: str | None = Query(default="pending", alias="status"),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List token requests from users."""
    query = select(TokenRequest).order_by(TokenRequest.created_at.desc())
    if status_filter:
        query = query.where(TokenRequest.status == status_filter)

    result = await db.execute(query.limit(100))
    requests = result.scalars().all()

    user_ids = list({r.user_id for r in requests})
    user_map = {}
    if user_ids:
        user_result = await db.execute(
            select(User.id, User.email, User.full_name, User.token_balance).where(User.id.in_(user_ids))
        )
        user_map = {r[0]: {"email": r[1], "full_name": r[2], "token_balance": r[3]} for r in user_result.fetchall()}

    return {
        "total": len(requests),
        "requests": [
            {
                "id": str(r.id),
                "user_id": r.user_id,
                "user_email": user_map.get(r.user_id, {}).get("email", ""),
                "user_name": user_map.get(r.user_id, {}).get("full_name", ""),
                "user_balance": user_map.get(r.user_id, {}).get("token_balance", 0),
                "amount": r.amount,
                "reason": r.reason,
                "status": r.status,
                "admin_note": r.admin_note,
                "created_at": _serialize_datetime(r.created_at),
                "reviewed_at": _serialize_datetime(r.reviewed_at),
            }
            for r in requests
        ],
    }


@router.post("/tokens/requests/{request_id}/review")
async def review_token_request(
    request_id: str,
    req: ReviewTokenRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a token request. Approving auto-grants the tokens."""
    result = await db.execute(select(TokenRequest).where(TokenRequest.id == request_id))
    token_req = result.scalar_one_or_none()
    if not token_req:
        raise HTTPException(status_code=404, detail="Token request not found")
    if token_req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request already {token_req.status}")

    if req.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    now = datetime.now(UTC)
    token_req.status = "approved" if req.action == "approve" else "rejected"
    token_req.admin_note = req.admin_note
    token_req.reviewed_by = admin.get("user_id")
    token_req.reviewed_at = now

    if req.action == "approve":
        grant_amount = req.grant_amount if req.grant_amount and req.grant_amount > 0 else token_req.amount

        # Grant tokens to user
        await db.execute(
            update(User)
            .where(User.id == token_req.user_id)
            .values(token_balance=User.token_balance + grant_amount)
        )

        # Get new balance for transaction record
        user_result = await db.execute(select(User.token_balance).where(User.id == token_req.user_id))
        new_balance = user_result.scalar() or 0

        # Record in transaction ledger
        txn = TokenTransaction(
            user_id=token_req.user_id,
            type="grant",
            amount=grant_amount,
            balance_after=new_balance,
            reason=f"Token request approved: {token_req.reason or 'No reason'}",
            created_by=admin.get("user_id"),
        )
        db.add(txn)

    await db.commit()

    # Fetch user email for response
    user_result = await db.execute(select(User.email).where(User.id == token_req.user_id))
    email = user_result.scalar() or ""

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action=f"token_request_{req.action}",
        resource_type="token_request",
        resource_id=request_id,
        details={"user_email": email, "amount": token_req.amount, "action": req.action},
    )

    return {"message": f"Token request {req.action}d for {email}"}
