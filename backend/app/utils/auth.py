import os
from datetime import UTC, datetime, timedelta

import bcrypt
from dotenv import load_dotenv
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    user_id: int,
    license_number: str | None = None,
    db_schema: str | None = None,
    is_admin: bool = False,
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    if license_number:
        payload["license_number"] = license_number
    if db_schema:
        payload["db_schema"] = db_schema
    if is_admin:
        payload["is_admin"] = True
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Returns dict with user_id, license_number, db_schema, is_admin — or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": int(payload["sub"]),
            "license_number": payload.get("license_number"),
            "db_schema": payload.get("db_schema"),
            "is_admin": payload.get("is_admin", False),
        }
    except (JWTError, KeyError, ValueError):
        return None
