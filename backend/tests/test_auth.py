"""Tests for authentication endpoints (signup, login, /me)."""

import pytest
from app.utils.auth import hash_password


SIGNUP_DATA = {
    "email": "test@meydan.ae",
    "password": "SecureP@ss123",
    "full_name": "Test User",
    "company_name": "Test Corp",
    "license_number": "MFZ-TEST-001",
}


@pytest.mark.asyncio
async def test_signup_success(client, db_session):
    """Successful signup returns 200 with token and user data."""
    from unittest.mock import AsyncMock, patch

    # Mock create_tenant_schema since we use SQLite (no PG schemas)
    with patch("app.routes.auth.create_tenant_schema", new_callable=AsyncMock) as mock_schema:
        mock_schema.return_value = "tenant_mfz_test_001"
        response = await client.post("/api/auth/signup", json=SIGNUP_DATA)

    assert response.status_code == 200, response.text
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == SIGNUP_DATA["email"]
    assert data["user"]["full_name"] == SIGNUP_DATA["full_name"]
    assert data["user"]["company_name"] == SIGNUP_DATA["company_name"]
    assert data["user"]["license_number"] == SIGNUP_DATA["license_number"]


@pytest.mark.asyncio
async def test_signup_duplicate_license_returns_409(client, db_session):
    """Signing up with an already-registered email returns 409."""
    from unittest.mock import AsyncMock, patch

    with patch("app.routes.auth.create_tenant_schema", new_callable=AsyncMock) as mock_schema:
        mock_schema.return_value = "tenant_dup_test"

        # First signup should succeed
        data1 = {**SIGNUP_DATA, "email": "dup1@meydan.ae", "license_number": "MFZ-DUP-001"}
        resp1 = await client.post("/api/auth/signup", json=data1)
        assert resp1.status_code == 200

        # Same email should fail
        data2 = {**SIGNUP_DATA, "email": "dup1@meydan.ae", "license_number": "MFZ-DUP-002"}
        resp2 = await client.post("/api/auth/signup", json=data2)
        assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    """Login with correct credentials returns token and user data."""
    from unittest.mock import AsyncMock, patch

    signup_data = {
        **SIGNUP_DATA,
        "email": "login@meydan.ae",
        "license_number": "MFZ-LOGIN-001",
    }

    with patch("app.routes.auth.create_tenant_schema", new_callable=AsyncMock) as mock_schema:
        mock_schema.return_value = "tenant_login"
        await client.post("/api/auth/signup", json=signup_data)

    login_data = {"email": "login@meydan.ae", "password": "SecureP@ss123"}
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "login@meydan.ae"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client, db_session):
    """Login with wrong password returns 401."""
    from unittest.mock import AsyncMock, patch

    signup_data = {
        **SIGNUP_DATA,
        "email": "wrongpw@meydan.ae",
        "license_number": "MFZ-WRONGPW-001",
    }

    with patch("app.routes.auth.create_tenant_schema", new_callable=AsyncMock) as mock_schema:
        mock_schema.return_value = "tenant_wrongpw"
        await client.post("/api/auth/signup", json=signup_data)

    login_data = {"email": "wrongpw@meydan.ae", "password": "WrongPassword"}
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user_info(client, db_session):
    """GET /me with valid token returns user info."""
    from unittest.mock import AsyncMock, patch

    signup_data = {
        **SIGNUP_DATA,
        "email": "metest@meydan.ae",
        "license_number": "MFZ-ME-001",
    }

    with patch("app.routes.auth.create_tenant_schema", new_callable=AsyncMock) as mock_schema:
        mock_schema.return_value = "tenant_me"
        resp = await client.post("/api/auth/signup", json=signup_data)

    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "metest@meydan.ae"
    assert data["full_name"] == SIGNUP_DATA["full_name"]


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    """GET /me without Authorization header returns 401/403."""
    response = await client.get("/api/auth/me")
    assert response.status_code in (401, 403)
