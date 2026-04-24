import asyncio
import logging
import os
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
from app.utils.input_sanitizer import validate_license_number, validate_password_strength

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
            logger.warning("Failed to log login event %s: %s", event_type, e)

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
    company_name: str | None = None
    license_number: str | None = None
    mobile: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company_name: str | None = None
    license_number: str | None = None
    mobile: str | None = None
    db_schema: str | None = None
    token_balance: int = 0
    tokens_used: int = 0
    is_admin: bool = False
    is_approved: bool = False
    email_verified: bool = False
    generation_count: int = 0
    max_generations: int = 2
    edit_count: int = 0
    max_edits: int = 30


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
    force_password_reset: bool = False


class SignupResponse(BaseModel):
    message: str
    email: str
    email_verified: bool = False


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# --- Routes ---


@router.post("/signup", response_model=SignupResponse)
async def signup(data: SignupRequest, request: Request, db: AsyncSession = Depends(get_db)):
    import uuid

    # Validate license number format (only if provided)
    if data.license_number:
        try:
            data.license_number = validate_license_number(data.license_number)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            ) from e

    try:
        validate_password_strength(data.password)
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

    # Check if license number already exists (only if provided)
    if data.license_number:
        result = await db.execute(select(User).where(User.license_number == data.license_number))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="License number already registered",
            )

    # Create isolated tenant schema (tied to email)
    schema_name = await create_tenant_schema(data.email)

    verification_token = uuid.uuid4().hex

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name or "",
        company_name=data.company_name or "",
        license_number=data.license_number if data.license_number else None,
        mobile=data.mobile or "",
        db_schema=schema_name,
        is_approved=False,
        token_balance=0,
        email_verified=False,
        email_verification_token=verification_token,
        email_verification_sent_at=datetime.now(UTC),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Audit log (fire-and-forget)
    log_event_bg(
        user_id=str(user.id),
        action="signup",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "company": user.company_name},
        ip_address=request.client.host if request.client else None,
    )

    # Send verification email (fire-and-forget). Admin notification is deferred
    # until the user actually confirms their email address.
    try:
        from app.utils.email import send_email_verification
        send_email_verification(user.email, verification_token, user.full_name)
    except Exception as e:
        logger.warning(f"[AUTH] Failed to send verification email: {e}")

    return SignupResponse(
        message="Account created. Please check your email to confirm your address before signing in.",
        email=user.email,
        email_verified=False,
    )


@router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Confirm a user's email address using the token sent at signup.

    On success, marks the user as email-verified and notifies the admin so the
    account becomes visible in the admin approval queue.
    """
    if not data.token:
        raise HTTPException(status_code=400, detail="Missing verification token")

    result = await db.execute(
        select(User).where(User.email_verification_token == data.token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    if getattr(user, "email_verified", False):
        # Idempotent — link already used
        return {"message": "Email already verified. You can sign in.", "email": user.email}

    # Keep the token on the row so a second click on the same link is
    # idempotent (returns the "already verified" message above) instead of
    # surfacing an "invalid link" error to the user.
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(email_verified=True)
    )
    await db.commit()

    log_event_bg(
        user_id=str(user.id),
        action="verify_email",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
    )

    # Now that the email is confirmed, send the welcome email and notify admin
    # so the user shows up in the approval queue.
    try:
        from app.utils.email import send_admin_new_signup, send_welcome
        send_welcome(user.email, user.full_name)
        admin_email = os.getenv("ADMIN_EMAIL", "meydan.ai.center@gmail.com")
        send_admin_new_signup(admin_email, user.email, user.full_name, user.company_name)
    except Exception as e:
        logger.warning(f"[AUTH] Failed to send post-verification emails: {e}")

    return {
        "message": "Email confirmed. Your account is now pending admin approval.",
        "email": user.email,
    }


@router.post("/resend-verification")
async def resend_verification(data: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    """Resend the email verification link. Always returns success to prevent enumeration."""
    import uuid

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    generic = {"message": "If an unverified account exists for that email, a new confirmation link has been sent."}

    if not user or getattr(user, "email_verified", False):
        return generic

    new_token = uuid.uuid4().hex
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            email_verification_token=new_token,
            email_verification_sent_at=datetime.now(UTC),
        )
    )
    await db.commit()

    try:
        from app.utils.email import send_email_verification
        send_email_verification(user.email, new_token, user.full_name)
    except Exception as e:
        logger.warning(f"[AUTH] Failed to resend verification email: {e}")

    return generic


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

    # Block login until the user has confirmed their email address.
    # Admins are exempt so they can never be locked out by this check.
    if not getattr(user, "is_admin", False) and not getattr(user, "email_verified", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please confirm your email address before signing in. Check your inbox for the confirmation link.",
        )

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

    force_reset = getattr(user, "force_password_reset", False) or False

    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            license_number=user.license_number,
            mobile=getattr(user, 'mobile', None),
            db_schema=user.db_schema,
            token_balance=getattr(user, 'token_balance', 0),
            tokens_used=getattr(user, 'tokens_used', 0),
            is_admin=getattr(user, 'is_admin', False),
            is_approved=getattr(user, 'is_approved', False),
            email_verified=getattr(user, 'email_verified', False),
            generation_count=getattr(user, 'generation_count', 0),
            max_generations=getattr(user, 'max_generations', 2),
            edit_count=getattr(user, 'edit_count', 0),
            max_edits=getattr(user, 'max_edits', 30),
        ),
        force_password_reset=force_reset,
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
        mobile=getattr(user, 'mobile', None),
        db_schema=user.db_schema,
        token_balance=getattr(user, 'token_balance', 0),
        tokens_used=getattr(user, 'tokens_used', 0),
        is_admin=getattr(user, 'is_admin', False),
        is_approved=getattr(user, 'is_approved', False),
        generation_count=getattr(user, 'generation_count', 0),
        max_generations=getattr(user, 'max_generations', 2),
        edit_count=getattr(user, 'edit_count', 0),
        max_edits=getattr(user, 'max_edits', 30),
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

    # Generate reset token — store only the SHA-256 hash in the DB so a
    # backup leak or read-only DB compromise can't be used to reset passwords.
    # The plaintext token goes only to the user's email.
    import hashlib
    reset_token = uuid.uuid4().hex
    token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    expires = datetime.now(UTC) + timedelta(hours=1)

    token_record = PasswordResetToken(
        user_id=user.id,
        token=token_hash,
        expires_at=expires,
    )
    db.add(token_record)
    await db.commit()

    logger.info(f"[AUTH] Password reset token generated for user {user.email}")

    # Send reset email via SES
    try:
        from app.utils.email import send_password_reset
        send_password_reset(user.email, reset_token)
    except Exception as e:
        logger.warning(f"[AUTH] Failed to send reset email: {e}")

    # In dev mode, also return token directly for testing
    import os
    response = {"message": "If an account with that email exists, a reset link has been sent."}
    if os.getenv("DEV_MODE", "false").lower() == "true":
        response["reset_token"] = reset_token
        response["reset_url"] = f"/reset-password?token={reset_token}"

    return response


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using a valid reset token."""
    import hashlib

    from app.models.password_reset import PasswordResetToken

    # Compare on the hashed form — the plaintext token is never in the DB.
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token_hash,
            PasswordResetToken.used.is_(False),
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if token_record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    try:
        validate_password_strength(data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

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

    try:
        validate_password_strength(data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.execute(
        update(User).where(User.id == user.id).values(
            hashed_password=hash_password(data.new_password),
            force_password_reset=False,
        )
    )
    await db.commit()

    return {"message": "Password changed successfully"}


# --- Token Requests ---


class TokenRequestModel(BaseModel):
    amount: int
    reason: str | None = None


@router.post("/token-request")
async def request_tokens(
    data: TokenRequestModel,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """User requests more tokens. Creates a pending request for admin review."""
    from app.models.token_request import TokenRequest

    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Check for existing pending request
    result = await db.execute(
        select(TokenRequest)
        .where(TokenRequest.user_id == token_data["user_id"], TokenRequest.status == "pending")
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have a pending token request")

    req = TokenRequest(
        user_id=token_data["user_id"],
        amount=data.amount,
        reason=data.reason,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    log_event_bg(
        user_id=str(token_data["user_id"]),
        action="token_request",
        resource_type="token",
        resource_id=str(req.id),
        details={"amount": data.amount, "reason": data.reason},
    )

    return {"message": "Token request submitted", "request_id": str(req.id)}


@router.get("/token-requests")
async def my_token_requests(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's token requests."""
    from app.models.token_request import TokenRequest

    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(
        select(TokenRequest)
        .where(TokenRequest.user_id == token_data["user_id"])
        .order_by(TokenRequest.created_at.desc())
        .limit(10)
    )
    requests = result.scalars().all()

    return {
        "requests": [
            {
                "id": str(r.id),
                "amount": r.amount,
                "reason": r.reason,
                "status": r.status,
                "admin_note": r.admin_note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
            for r in requests
        ]
    }
