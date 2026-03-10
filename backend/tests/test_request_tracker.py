"""Tests for the request tracker middleware (graceful shutdown)."""

import pytest

import app.middleware.request_tracker as tracker_mod
from app.middleware.request_tracker import (
    HEALTH_CHECK_PATHS,
    get_inflight_count,
    is_shutting_down,
)


@pytest.fixture(autouse=True)
def reset_tracker_state():
    """Reset module-level state before each test."""
    tracker_mod._inflight_count = 0
    tracker_mod._shutting_down = False
    tracker_mod._inflight_lock = None
    yield
    tracker_mod._inflight_count = 0
    tracker_mod._shutting_down = False
    tracker_mod._inflight_lock = None


@pytest.mark.asyncio
async def test_inflight_count_increments_and_decrements(client):
    """In-flight count goes up during request processing and back down after."""
    assert get_inflight_count() == 0
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert get_inflight_count() == 0


@pytest.mark.asyncio
async def test_shutdown_rejects_new_requests(client):
    """During shutdown, non-health requests are rejected with 503."""
    tracker_mod._shutting_down = True

    response = await client.get("/api/templates/")
    assert response.status_code == 503, f"Expected 503 during shutdown, got {response.status_code}"


@pytest.mark.asyncio
async def test_health_check_allowed_during_shutdown(client):
    """Health check endpoints still work during shutdown."""
    tracker_mod._shutting_down = True

    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "draining"


def test_health_check_paths_defined():
    """Verify the expected paths are in the health check set."""
    assert "/health" in HEALTH_CHECK_PATHS
    assert "/healthz" in HEALTH_CHECK_PATHS
    assert "/api/health" in HEALTH_CHECK_PATHS


def test_is_shutting_down_reflects_state():
    """is_shutting_down() returns the module-level flag."""
    assert is_shutting_down() is False
    tracker_mod._shutting_down = True
    assert is_shutting_down() is True
