"""
Shared admin dependencies — authentication and helpers.
"""

from datetime import datetime

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.auth import decode_access_token

security = HTTPBearer()


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify the caller has admin privileges."""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


def _safe_getattr(obj, attr, default=None):
    """Get attribute from SQLAlchemy model, returning default if column doesn't exist."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def _user_to_dict(user) -> dict:
    """Convert User model to dict, handling missing columns gracefully."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "company_name": user.company_name,
        "license_number": user.license_number,
        "mobile": _safe_getattr(user, "mobile"),
        "db_schema": user.db_schema,
        "created_at": _safe_getattr(user, "created_at"),
        "last_login": _safe_getattr(user, "last_login"),
        "generation_count": _safe_getattr(user, "generation_count", 0),
        "edit_count": _safe_getattr(user, "edit_count", 0),
        "max_generations": _safe_getattr(user, "max_generations", 2),
        "max_edits": _safe_getattr(user, "max_edits", 30),
        "is_active": _safe_getattr(user, "is_active", True),
        "is_admin": _safe_getattr(user, "is_admin", False),
        "is_approved": _safe_getattr(user, "is_approved", False),
        "approved_at": _serialize_datetime(_safe_getattr(user, "approved_at")),
        "email_verified": _safe_getattr(user, "email_verified", False),
        "email_verification_sent_at": _serialize_datetime(_safe_getattr(user, "email_verification_sent_at")),
        "token_balance": _safe_getattr(user, "token_balance", 0),
        "tokens_used": _safe_getattr(user, "tokens_used", 0),
    }


def _serialize_datetime(dt) -> str | None:
    """Safely serialize a datetime to ISO string."""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return None
