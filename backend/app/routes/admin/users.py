"""
Admin user management endpoints.
"""

import csv
import io
import logging
import secrets
from datetime import UTC, datetime, timedelta  # noqa: F811

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit import AuditLog
from app.models.login_event import LoginEvent
from app.models.user import User
from app.utils.audit_log import log_event_bg
from app.utils.auth import hash_password

from .deps import _safe_getattr, _serialize_datetime, _user_to_dict, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Users"])


# ── Schemas ──────────────────────────────────────────────────────────


class GrantTokensRequest(BaseModel):
    amount: int


class BulkActionRequest(BaseModel):
    action: str  # grant_tokens, disable, enable
    user_ids: list[int]
    params: dict = {}


class LicenceVerifyRequest(BaseModel):
    licence_verified: bool


class MessageResponse(BaseModel):
    message: str


# ── Endpoints ────────────────────────────────────────────────────────


@router.get("/users")
async def list_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=None),
    is_active: bool | None = Query(default=None),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination and optional filters."""
    query = select(User)

    if search:
        like = f"%{search}%"
        query = query.where(
            (User.email.ilike(like))
            | (User.full_name.ilike(like))
            | (User.company_name.ilike(like))
            | (User.license_number.ilike(like))
        )

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    result = await db.execute(
        query.order_by(User.id.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()

    return {
        "users": [_user_to_dict(u) for u in users],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/users/export")
async def export_users_csv(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Export all users as a CSV file."""
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "email", "full_name", "company_name", "license_number",
            "mobile", "is_active", "is_admin", "token_balance", "tokens_used",
            "generation_count", "created_at", "last_login",
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for u in users:
            writer.writerow([
                u.id, u.email, u.full_name, u.company_name, u.license_number,
                _safe_getattr(u, "mobile"),
                _safe_getattr(u, "is_active", True),
                _safe_getattr(u, "is_admin", False),
                _safe_getattr(u, "token_balance", 0),
                _safe_getattr(u, "tokens_used", 0),
                _safe_getattr(u, "generation_count", 0),
                _serialize_datetime(_safe_getattr(u, "created_at")),
                _serialize_datetime(_safe_getattr(u, "last_login")),
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"},
    )


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info for a specific user, including sites, domains, token transactions, and login events."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = _user_to_dict(user)

    # Projects count from tenant schema
    projects_count = 0
    if user.db_schema:
        try:
            result = await db.execute(
                text("""
                    SELECT count(*) FROM information_schema.tables
                    WHERE table_schema = :schema AND table_name = 'projects'
                """),
                {"schema": user.db_schema},
            )
            has_table = (result.scalar() or 0) > 0
            if has_table:
                result = await db.execute(
                    text(f'SELECT count(*) FROM "{user.db_schema}".projects')
                )
                projects_count = result.scalar() or 0
        except Exception as e:
            logger.warning("Failed to get projects count for schema %s: %s", user.db_schema, e)
            await db.rollback()
    user_data["projects_count"] = projects_count

    # Sites
    from app.models.site import Site

    try:
        result = await db.execute(
            select(Site).where(Site.user_id == user_id, Site.deleted_at.is_(None)).order_by(Site.created_at.desc()).limit(20)
        )
        sites = result.scalars().all()
        user_data["sites"] = [
            {
                "id": str(s.id),
                "name": s.name,
                "domain": s.domain,
                "deployed_url": s.deployed_url,
                "status": s.status,
                "is_multipage": s.is_multipage,
                "created_at": _serialize_datetime(s.created_at),
            }
            for s in sites
        ]
    except Exception as e:
        logger.warning("Failed to fetch sites for user %s: %s", user_id, e)
        user_data["sites"] = []

    # Domains
    from app.models.domain import Domain

    try:
        result = await db.execute(
            select(Domain).where(Domain.user_id == user_id).order_by(Domain.created_at.desc()).limit(20)
        )
        domains = result.scalars().all()
        user_data["domains"] = [
            {
                "id": str(d.id),
                "domain_name": d.domain_name,
                "status": d.status,
                "ssl_status": d.ssl_status,
                "expires_at": _serialize_datetime(d.expires_at),
            }
            for d in domains
        ]
    except Exception as e:
        logger.warning("Failed to fetch domains for user %s: %s", user_id, e)
        user_data["domains"] = []

    # Recent token transactions
    from app.models.token_transaction import TokenTransaction

    try:
        result = await db.execute(
            select(TokenTransaction)
            .where(TokenTransaction.user_id == user_id)
            .order_by(TokenTransaction.created_at.desc())
            .limit(20)
        )
        txns = result.scalars().all()
        user_data["token_transactions"] = [
            {
                "id": str(t.id),
                "type": t.type,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "reason": t.reason,
                "created_at": _serialize_datetime(t.created_at),
            }
            for t in txns
        ]
    except Exception as e:
        logger.warning("Failed to fetch token transactions for user %s: %s", user_id, e)
        user_data["token_transactions"] = []

    # Recent login events
    try:
        result = await db.execute(
            select(LoginEvent)
            .where(LoginEvent.user_id == user_id)
            .order_by(LoginEvent.created_at.desc())
            .limit(20)
        )
        events = result.scalars().all()
        user_data["login_events"] = [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "created_at": _serialize_datetime(e.created_at),
            }
            for e in events
        ]
    except Exception as e:
        logger.warning("Failed to fetch login events for user %s: %s", user_id, e)
        user_data["login_events"] = []

    return user_data


@router.get("/users/{user_id}/audit")
async def get_user_audit(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get audit trail for a specific user."""
    try:
        count_result = await db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.user_id == str(user_id))
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == str(user_id))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        logs = result.scalars().all()

        return {
            "audit_logs": [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": _serialize_datetime(log.created_at),
                }
                for log in logs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to fetch user audit logs: %s", e)
        return {"audit_logs": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/users/{user_id}/logins")
async def get_user_logins(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get login event history for a specific user."""
    try:
        count_result = await db.execute(
            select(func.count(LoginEvent.id)).where(LoginEvent.user_id == user_id)
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(LoginEvent)
            .where(LoginEvent.user_id == user_id)
            .order_by(LoginEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        events = result.scalars().all()

        return {
            "login_events": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "ip_address": e.ip_address,
                    "user_agent": e.user_agent,
                    "created_at": _serialize_datetime(e.created_at),
                }
                for e in events
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to fetch login events: %s", e)
        return {"login_events": [], "total": 0, "limit": limit, "offset": offset}


@router.post("/users/{user_id}/impersonate")
async def impersonate_user(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a read-only JWT for impersonating a user (30 min expiry)."""
    from jose import jwt as jose_jwt

    from app.utils.auth import JWT_ALGORITHM, JWT_SECRET

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    expire = datetime.now(UTC) + timedelta(minutes=30)
    payload = {
        "sub": str(user.id),
        "exp": expire,
        "license_number": user.license_number,
        "db_schema": user.db_schema,
        "impersonating": True,
        "read_only": True,
        "impersonated_by": admin.get("user_id"),
    }
    token = jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="impersonate_user",
        resource_type="user",
        resource_id=str(user_id),
        details={"target_email": user.email},
    )

    return {
        "token": token,
        "user": _user_to_dict(user),
        "expires_in_minutes": 30,
        "read_only": True,
    }


@router.post("/users/bulk")
async def bulk_user_action(
    req: BulkActionRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Perform bulk actions on multiple users: grant_tokens, disable, enable."""
    if not req.user_ids:
        raise HTTPException(status_code=400, detail="user_ids must not be empty")

    if req.action == "grant_tokens":
        amount = req.params.get("amount", 0)
        if not isinstance(amount, int) or amount <= 0:
            raise HTTPException(status_code=400, detail="params.amount must be a positive integer")

        await db.execute(
            update(User)
            .where(User.id.in_(req.user_ids))
            .values(token_balance=User.token_balance + amount)
        )

        # Record each grant in token ledger
        from app.models.token_transaction import TokenTransaction
        for uid in req.user_ids:
            # Fetch updated balance
            bal_result = await db.execute(select(User.token_balance).where(User.id == uid))
            bal = bal_result.scalar() or 0
            txn = TokenTransaction(
                user_id=uid,
                type="grant",
                amount=amount,
                balance_after=bal,
                reason="Bulk admin grant",
                created_by=admin.get("user_id"),
            )
            db.add(txn)
        await db.commit()

        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="bulk_grant_tokens",
            resource_type="user",
            details={"user_ids": req.user_ids, "amount": amount},
        )
        return {"message": f"Granted {amount:,} tokens to {len(req.user_ids)} users"}

    elif req.action == "disable":
        await db.execute(
            update(User).where(User.id.in_(req.user_ids)).values(is_active=False)
        )
        await db.commit()

        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="bulk_disable_users",
            resource_type="user",
            details={"user_ids": req.user_ids},
        )
        return {"message": f"Disabled {len(req.user_ids)} users"}

    elif req.action == "enable":
        await db.execute(
            update(User).where(User.id.in_(req.user_ids)).values(is_active=True)
        )
        await db.commit()

        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="bulk_enable_users",
            resource_type="user",
            details={"user_ids": req.user_ids},
        )
        return {"message": f"Enabled {len(req.user_ids)} users"}

    elif req.action == "approve":
        await db.execute(
            update(User)
            .where(User.id.in_(req.user_ids))
            .values(
                is_approved=True,
                approved_at=datetime.now(UTC),
                approved_by=admin.get("user_id"),
                token_balance=300_000,
                is_active=True,
            )
        )
        await db.commit()

        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="bulk_approve_users",
            resource_type="user",
            details={"user_ids": req.user_ids},
        )
        return {"message": f"Approved {len(req.user_ids)} users with 1,000,000 tokens each"}

    elif req.action == "set_limits":
        max_gen = req.params.get("max_generations")
        max_ed = req.params.get("max_edits")
        updates = {}
        if isinstance(max_gen, int) and max_gen >= 0:
            updates["max_generations"] = max_gen
        if isinstance(max_ed, int) and max_ed >= 0:
            updates["max_edits"] = max_ed
        if not updates:
            raise HTTPException(status_code=400, detail="params must include max_generations and/or max_edits")
        await db.execute(update(User).where(User.id.in_(req.user_ids)).values(**updates))
        await db.commit()
        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="bulk_set_limits",
            resource_type="user",
            details={"user_ids": req.user_ids, **updates},
        )
        return {"message": f"Updated limits for {len(req.user_ids)} users: {updates}"}

    elif req.action == "reset_usage":
        await db.execute(
            update(User).where(User.id.in_(req.user_ids)).values(generation_count=0, edit_count=0)
        )
        await db.commit()
        log_event_bg(
            user_id=str(admin.get("user_id")),
            action="bulk_reset_usage",
            resource_type="user",
            details={"user_ids": req.user_ids},
        )
        return {"message": f"Reset usage counters for {len(req.user_ids)} users"}

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action '{req.action}'. Supported: grant_tokens, disable, enable, approve, set_limits, reset_usage",
        )


@router.patch("/users/{user_id}/licence")
async def set_licence_verified(
    user_id: int,
    req: LicenceVerifyRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Set licence verification status for a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(licence_verified=req.licence_verified)
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update licence status (column may not exist): {e}",
        ) from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="set_licence_verified",
        resource_type="user",
        resource_id=str(user_id),
        details={"licence_verified": req.licence_verified, "email": user.email},
    )

    return {"message": f"Licence verified={req.licence_verified} for {user.email}"}


@router.post("/users/{user_id}/approve", response_model=MessageResponse)
async def approve_user(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve a user account — grants 1M tokens and unlocks the app."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if _safe_getattr(user, "is_approved", False):
        raise HTTPException(status_code=400, detail="User is already approved")

    try:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                is_approved=True,
                approved_at=datetime.now(UTC),
                approved_by=admin.get("user_id"),
                token_balance=300_000,
                is_active=True,
            )
        )

        # Record approval grant in token ledger
        from app.models.token_transaction import TokenTransaction
        txn = TokenTransaction(
            user_id=user_id,
            type="grant",
            amount=300_000,
            balance_after=300_000,
            reason="Account approval grant",
            created_by=admin.get("user_id"),
        )
        db.add(txn)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to approve user: {e}") from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="approve_user",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": user.email, "tokens_granted": 300_000},
    )

    # Send approval notification email (fire-and-forget)
    try:
        from app.utils.email import send_approval_notification
        send_approval_notification(user.email, _safe_getattr(user, "full_name", ""))
    except Exception as e:
        logger.warning(f"[ADMIN] Failed to send approval email: {e}")

    return {"message": f"User {user.email} has been approved with 300,000 tokens"}


@router.post("/users/{user_id}/reset-usage", response_model=MessageResponse)
async def reset_user_usage(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reset a user's generation and edit counts to 0."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        update(User).where(User.id == user_id).values(generation_count=0, edit_count=0)
    )
    await db.commit()

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="reset_user_usage",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": user.email},
    )
    return {"message": f"Usage reset for {user.email}"}


@router.post("/users/{user_id}/toggle-admin", response_model=MessageResponse)
async def toggle_admin(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Toggle admin status for a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_status = not _safe_getattr(user, "is_admin", False)
    await db.execute(
        update(User).where(User.id == user_id).values(is_admin=new_status)
    )
    await db.commit()

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="toggle_admin",
        resource_type="user",
        resource_id=str(user_id),
        details={"is_admin": new_status, "email": user.email},
    )

    return {"message": f"{'Granted' if new_status else 'Revoked'} admin for {user.email}"}


@router.post("/users/{user_id}/disable", response_model=MessageResponse)
async def disable_user(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Disable a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await db.execute(update(User).where(User.id == user_id).values(is_active=False))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disable user: {e}",
        ) from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="disable_user",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": user.email},
    )

    return {"message": f"User {user.email} has been disabled"}


@router.post("/users/{user_id}/enable", response_model=MessageResponse)
async def enable_user(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Re-enable a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await db.execute(update(User).where(User.id == user_id).values(is_active=True))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enable user: {e}",
        ) from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="enable_user",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": user.email},
    )

    return {"message": f"User {user.email} has been re-enabled"}


@router.post("/users/{user_id}/grant-tokens", response_model=MessageResponse)
async def grant_tokens(
    user_id: int,
    req: GrantTokensRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Grant additional tokens to a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    try:
        new_balance = _safe_getattr(user, "token_balance", 0) + req.amount
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(token_balance=User.token_balance + req.amount)
        )

        # Record in token ledger
        from app.models.token_transaction import TokenTransaction
        txn = TokenTransaction(
            user_id=user_id,
            type="grant",
            amount=req.amount,
            balance_after=new_balance,
            reason="Admin grant",
            created_by=admin.get("user_id"),
        )
        db.add(txn)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to grant tokens: {e}") from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="grant_tokens",
        resource_type="user",
        resource_id=str(user_id),
        details={"amount": req.amount, "new_balance": new_balance, "email": user.email},
    )

    return {"message": f"Granted {req.amount:,} tokens to {user.email}. New balance: {new_balance:,}"}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-initiated password reset -- generates a temporary password."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    temp_password = secrets.token_urlsafe(12)

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            hashed_password=hash_password(temp_password),
            force_password_reset=True,
        )
    )
    await db.commit()

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="admin_reset_password",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": user.email},
    )

    return {
        "message": f"Password reset for {user.email}",
        "temporary_password": temp_password,
    }
