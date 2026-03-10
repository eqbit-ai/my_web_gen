"""Tests for health check endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_check_returns_ok(client):
    """GET /api/health returns status ok when not shutting down."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "meydan-website-generator"


@pytest.mark.asyncio
async def test_deep_health_check_returns_all_checks(client):
    """GET /api/health/deep returns checks dict with api, redis, database keys."""
    response = await client.get("/api/health/deep")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "api" in data["checks"]
    assert data["checks"]["api"] == "ok"
    assert "inflight_requests" in data
    assert "circuits" in data
