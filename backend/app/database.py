import os
import re

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Cache of schemas that have had tenant tables initialized
_initialized_schemas: set[str] = set()


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


def _sanitize_schema_name(license_number: str) -> str:
    """Convert a license number to a safe schema name."""
    sanitized = re.sub(r"[^a-z0-9]", "_", license_number.lower())
    return f"tenant_{sanitized}"


async def init_tenant_tables(schema_name: str):
    """Create Project + ProjectVersion tables in a tenant schema (idempotent)."""
    if schema_name in _initialized_schemas:
        return
    from app.models.media import Media  # noqa: F401
    from app.models.project import Project, ProjectVersion  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text(f'SET search_path TO "{schema_name}", public'))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SET search_path TO public"))
    _initialized_schemas.add(schema_name)


async def create_tenant_schema(license_number: str) -> str:
    """Create an isolated PostgreSQL schema for a tenant. Returns the schema name."""
    schema_name = _sanitize_schema_name(license_number)
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    await init_tenant_tables(schema_name)
    return schema_name


async def get_tenant_db(schema_name: str):
    """Yield an async session with search_path set to the tenant's schema."""
    await init_tenant_tables(schema_name)
    async with async_session() as session:
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))
        yield session


async def init_db():
    from app.models.audit import AuditLog  # noqa: F401
    from app.models.user import User  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
