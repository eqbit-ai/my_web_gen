"""
Shared pytest fixtures for the Meydan backend test suite.

Uses SQLite async for database tests and a dict-based Redis mock
to avoid requiring external services during testing.
"""

import os
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Environment setup — must happen BEFORE any app imports
# ---------------------------------------------------------------------------
os.environ["DEV_MODE"] = "true"  # Allow unauthenticated deep health checks in tests
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
# Keep a PG-like URL so app.database module-level code doesn't crash
# We'll override the engine/session after import
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

# ---------------------------------------------------------------------------
# Create a test-compatible SQLite engine
# Register JSONB -> JSON adapter so PG-specific column types work in SQLite
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

# Teach SQLite compiler to handle PG-specific types (JSONB, UUID)
if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):

    def _visit_jsonb(self, type_, **kw):
        return "JSON"

    SQLiteTypeCompiler.visit_JSONB = _visit_jsonb

if not hasattr(SQLiteTypeCompiler, "visit_UUID"):

    def _visit_uuid(self, type_, **kw):
        return "VARCHAR(36)"

    SQLiteTypeCompiler.visit_UUID = _visit_uuid

_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)

# ---------------------------------------------------------------------------
# Now import app.database — it will create a PG engine (that we'll never use)
# Then immediately replace with our test engine
# ---------------------------------------------------------------------------
import app.database as _db_mod

# Store reference to the original Base (models are already bound to it)
Base = _db_mod.Base

# Replace engine and session factory with test versions
_db_mod.engine = _test_engine
_db_mod.async_session = _test_session_factory

# Provide a no-op create_tenant_schema
import re as _re


async def _noop_create_tenant_schema(license_number: str) -> str:
    sanitized = _re.sub(r"[^a-z0-9]", "_", license_number.lower())
    return f"tenant_{sanitized}"


_db_mod.create_tenant_schema = _noop_create_tenant_schema


# Replace init_db to use our test engine with the real Base
async def _test_init_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


_db_mod.init_db = _test_init_db

# Import models to register them with Base.metadata
from app.database import get_db
from app.models.user import User  # noqa: F401
from app.utils.auth import create_access_token

# ---------------------------------------------------------------------------
# Fake Redis (dict-backed)
# ---------------------------------------------------------------------------


class FakeRedisPipeline:
    """Minimal pipeline that collects operations and executes them."""

    def __init__(self, store: dict):
        self._store = store
        self._ops = []

    def zremrangebyscore(self, key, min_score, max_score):
        self._ops.append(("zremrangebyscore", key, min_score, max_score))
        return self

    def zadd(self, key, mapping):
        self._ops.append(("zadd", key, mapping))
        return self

    def zcard(self, key):
        self._ops.append(("zcard", key))
        return self

    def expire(self, key, ttl):
        self._ops.append(("expire", key, ttl))
        return self

    async def execute(self):
        results = []
        for op in self._ops:
            if op[0] == "zremrangebyscore":
                results.append(0)
            elif op[0] == "zadd":
                key, mapping = op[1], op[2]
                if key not in self._store:
                    self._store[key] = []
                for member, score in mapping.items():
                    self._store[key].append((member, score))
                results.append(len(mapping))
            elif op[0] == "zcard":
                key = op[1]
                results.append(len(self._store.get(key, [])))
            elif op[0] == "expire":
                results.append(True)
        self._ops.clear()
        return results


class FakeRedis:
    """Dict-backed async Redis mock for testing."""

    def __init__(self):
        self._store: dict = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value, ex=None):
        self._store[key] = value
        return True

    async def delete(self, *keys):
        for k in keys:
            self._store.pop(k, None)
        return len(keys)

    async def incr(self, key: str):
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    async def zrange(self, key, start, stop, withscores=False):
        items = self._store.get(key, [])
        sliced = items[start : stop + 1] if stop >= 0 else items[start:]
        if withscores:
            return sliced
        return [item[0] for item in sliced]

    def pipeline(self):
        return FakeRedisPipeline(self._store)

    async def close(self):
        pass


# ---------------------------------------------------------------------------
# Patch Redis globally before app.main is imported
# ---------------------------------------------------------------------------
_session_fake_redis = FakeRedis()


async def _fake_get_redis():
    return _session_fake_redis


async def _fake_close_redis():
    pass


patch("app.utils.redis_client.get_redis", _fake_get_redis).start()
patch("app.utils.redis_client.close_redis", _fake_close_redis).start()
patch("app.middleware.rate_limiter.get_redis", _fake_get_redis).start()


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def test_engine():
    """Create only the tables we need for testing (skip PG-specific ones)."""
    # Only create tables that are compatible with SQLite
    # (skip audit_logs which uses PG UUID/JSONB)
    tables_to_create = [User.__table__]
    async with _test_engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=tables_to_create,
        )
    yield _test_engine


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """Provide a fresh database session per test, rolled back after each test."""
    async with _test_session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Redis fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def redis_mock():
    """Provide a fresh FakeRedis instance per test."""
    return FakeRedis()


# ---------------------------------------------------------------------------
# FastAPI app + client fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def app(test_engine):
    """Create the FastAPI app with overridden dependencies."""

    async def override_get_db():
        async with _test_session_factory() as session:
            yield session

    from app.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app):
    """Provide an async HTTP client for the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


# ---------------------------------------------------------------------------
# Auth fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def auth_token():
    """Generate a JWT token for a test user."""
    return create_access_token(
        user_id=1,
        license_number="TEST-LICENSE-001",
        db_schema="tenant_test_license_001",
    )


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Provide Authorization headers with a Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}
