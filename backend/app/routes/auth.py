import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import create_tenant_schema, get_db
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


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


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

    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            license_number=user.license_number,
            db_schema=user.db_schema,
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
    )
