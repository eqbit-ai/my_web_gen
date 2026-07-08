"""
Seed an admin user who can sign in immediately — bypasses email verification
and admin approval so you have a working account to log in with.

Run: cd backend && python -m scripts.seed_admin
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.database import async_session
from app.models.user import User
from app.utils.auth import hash_password

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")


async def seed():
    async with async_session() as db:
        existing = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        user = existing.scalar_one_or_none()

        if user:
            user.is_admin = True
            user.is_active = True
            user.is_approved = True
            user.email_verified = True
            user.licence_verified = True
            user.hashed_password = hash_password(ADMIN_PASSWORD)
            print(f"  UPDATE existing user '{ADMIN_EMAIL}' -> admin, verified, approved")
        else:
            user = User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                full_name="Admin",
                company_name="Admin",
                mobile="",
                is_admin=True,
                is_active=True,
                is_approved=True,
                email_verified=True,
                licence_verified=True,
                token_balance=1_000_000,
                max_generations=999999,
                max_edits=999999,
            )
            db.add(user)
            print(f"  CREATE new admin user '{ADMIN_EMAIL}'")

        await db.commit()
        print(f"\nDone. Login with:\n  email:    {ADMIN_EMAIL}\n  password: {ADMIN_PASSWORD}")
        print("\n⚠️  Change this password after first login.")


if __name__ == "__main__":
    asyncio.run(seed())