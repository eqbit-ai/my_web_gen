import os
import re

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool_size = int(os.getenv("DB_POOL_SIZE", "80"))
_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "120"))

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=_pool_size,
    max_overflow=_max_overflow,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Cache of schemas that have had tenant tables initialized
_initialized_schemas: set[str] = set()


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


def _sanitize_schema_name(identifier: str) -> str:
    """Convert an email or license number to a safe schema name."""
    sanitized = re.sub(r"[^a-z0-9]", "_", identifier.lower())
    return f"tenant_{sanitized}"


def _validate_schema_name(schema_name: str) -> str:
    """Validate that a schema name contains only safe characters.

    Prevents SQL injection via double-quote breakout in SET search_path
    and CREATE SCHEMA statements. Only alphanumeric and underscore allowed.
    Raises ValueError if the name is invalid.
    """
    if not schema_name or not re.fullmatch(r"[a-zA-Z0-9_]+", schema_name):
        raise ValueError(f"Invalid schema name: {schema_name!r}")
    return schema_name


async def init_tenant_tables(schema_name: str):
    """Create Project + ProjectVersion tables in a tenant schema (idempotent)."""
    schema_name = _validate_schema_name(schema_name)
    if schema_name in _initialized_schemas:
        return
    from app.models.media import Media  # noqa: F401
    from app.models.project import Project, ProjectVersion  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text(f'SET search_path TO "{schema_name}", public'))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SET search_path TO public"))
    _initialized_schemas.add(schema_name)


async def create_tenant_schema(identifier: str) -> str:
    """Create an isolated PostgreSQL schema for a tenant. Returns the schema name."""
    schema_name = _validate_schema_name(_sanitize_schema_name(identifier))
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    await init_tenant_tables(schema_name)
    return schema_name


async def get_tenant_db(schema_name: str):
    """Yield an async session with search_path set to the tenant's schema."""
    schema_name = _validate_schema_name(schema_name)
    await init_tenant_tables(schema_name)
    async with async_session() as session:
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))
        yield session


async def init_db():
    from app.models.announcement import Announcement  # noqa: F401
    from app.models.audit import AuditLog  # noqa: F401
    from app.models.domain import Domain  # noqa: F401
    from app.models.generation_log import GenerationLog  # noqa: F401
    from app.models.login_event import LoginEvent  # noqa: F401
    from app.models.password_reset import PasswordResetToken  # noqa: F401
    from app.models.prompt_version import PromptVersion  # noqa: F401
    from app.models.site import Site  # noqa: F401
    from app.models.token_request import TokenRequest  # noqa: F401
    from app.models.token_transaction import TokenTransaction  # noqa: F401
    from app.models.user import User  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
