import asyncio
import logging
import traceback
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, create_tenant_schema, get_db
from app.models.login_event import LoginEvent
from app.models.user import User
from app.utils.audit_log import log_event_bg
from app.utils.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.utils.input_sanitizer import validate_license_number

logger = logging.getLogger(__name__)


def _log_login_event_bg(user_id: int, event_type: str, ip_address: str, user_agent: str | None = None):
    """Fire-and-forget login event insert."""
    async def _insert():
        try:
            async with async_session() as session:
                session.add(LoginEvent(
                    user_id=user_id,
                    event_type=event_type,
                    ip_address=ip_address or "unknown",
                    user_agent=user_agent,
                ))
                await session.commit()
        except Exception as e:
            print(f"[LoginEvent] Failed to log {event_type}: {e}", flush=True)
            traceback.print_exc()

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_insert())
    except RuntimeError:
        pass

router = APIRouter()
security = HTTPBearer()


# --- Schemas ---


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str
    license_number: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company_name: str
    license_number: str
    db_schema: str | None = None
    token_balance: int = 1_000_000
    tokens_used: int = 0
    is_admin: bool = False


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# --- Routes ---


@router.post("/signup", response_model=AuthResponse)
async def signup(data: SignupRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Validate license number format
    try:
        data.license_number = validate_license_number(data.license_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Check if license number already exists
    result = await db.execute(select(User).where(User.license_number == data.license_number))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="License number already registered",
        )

    # Create isolated tenant schema
    schema_name = await create_tenant_schema(data.license_number)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        company_name=data.company_name,
        license_number=data.license_number,
        db_schema=schema_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.license_number, user.db_schema)

    # Audit log (fire-and-forget)
    log_event_bg(
        user_id=str(user.id),
        action="signup",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "company": user.company_name},
        ip_address=request.client.host if request.client else None,
    )

    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            license_number=user.license_number,
            db_schema=user.db_schema,
            token_balance=getattr(user, 'token_balance', 1_000_000),
            tokens_used=getattr(user, 'tokens_used', 0),
            is_admin=getattr(user, 'is_admin', False),
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if user is active
    try:
        if hasattr(user, "is_active") and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been disabled. Contact support.",
            )
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        pass  # Column may not exist yet

    # Include is_admin flag in token if the user is an admin
    is_admin = getattr(user, "is_admin", False) or False
    token = create_access_token(user.id, user.license_number, user.db_schema, is_admin=is_admin)

    # Update last_login timestamp (best-effort)
    try:
        await db.execute(update(User).where(User.id == user.id).values(last_login=datetime.now(UTC)))
        await db.commit()
    except Exception:
        await db.rollback()  # Column may not exist yet

    # Audit log (fire-and-forget)
    # Note: login rate limiting is handled by RateLimitMiddleware
    log_event_bg(
        user_id=str(user.id),
        action="login",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
        ip_address=request.client.host if request.client else None,
    )

    # Login event for admin dashboard (fire-and-forget)
    _log_login_event_bg(
        user_id=user.id,
        event_type="login_success",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
    )

    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            license_number=user.license_number,
            db_schema=user.db_schema,
            token_balance=getattr(user, 'token_balance', 1_000_000),
            tokens_used=getattr(user, 'tokens_used', 0),
            is_admin=getattr(user, 'is_admin', False),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await db.execute(select(User).where(User.id == token_data["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        company_name=user.company_name,
        license_number=user.license_number,
        db_schema=user.db_schema,
        token_balance=getattr(user, 'token_balance', 1_000_000),
        tokens_used=getattr(user, 'tokens_used', 0),
        is_admin=getattr(user, 'is_admin', False),
    )


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset token."""
    import uuid
    from datetime import timedelta
    from app.models.password_reset import PasswordResetToken

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If an account with that email exists, a reset link has been generated."}

    # Generate reset token
    reset_token = uuid.uuid4().hex
    expires = datetime.now(UTC) + timedelta(hours=1)

    token_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires,
    )
    db.add(token_record)
    await db.commit()

    logger.info(f"[AUTH] Password reset token generated for user {user.email}")

    # In development, return the token directly. In production, send email.
    import os
    response = {"message": "If an account with that email exists, a reset link has been generated."}
    if os.getenv("DEV_MODE", "true").lower() == "true":
        response["reset_token"] = reset_token
        response["reset_url"] = f"/reset-password?token={reset_token}"

    return response


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using a valid reset token."""
    from app.models.password_reset import PasswordResetToken

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == data.token,
            PasswordResetToken.used == False,
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if token_record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # Update password
    await db.execute(
        update(User).where(User.id == token_record.user_id).values(
            hashed_password=hash_password(data.new_password)
        )
    )

    # Mark token as used
    token_record.used = True
    await db.commit()

    logger.info(f"[AUTH] Password reset completed for user_id={token_record.user_id}")
    return {"message": "Password has been reset successfully. Please log in with your new password."}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the authenticated user."""
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == token_data["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    await db.execute(
        update(User).where(User.id == user.id).values(
            hashed_password=hash_password(data.new_password)
        )
    )
    await db.commit()

    return {"message": "Password changed successfully"}
