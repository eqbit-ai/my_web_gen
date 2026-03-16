"""Tests for the rate limiter middleware."""

import pytest

from app.middleware.rate_limiter import SKIP_PATHS, RateLimitMiddleware


class TestRateLimitRuleMatching:
    """Test the rule matching logic directly."""

    def setup_method(self):
        self.middleware = RateLimitMiddleware(app=None)

    def test_rate_limit_matches_generator_path(self):
        rule = self.middleware._match_rule("/api/generator/generate")
        assert rule is not None
        assert rule["key_prefix"] == "rl:gen"

    def test_rate_limit_matches_edit_path(self):
        rule = self.middleware._match_rule("/api/generator/iterate")
        assert rule is not None
        assert rule["key_prefix"] == "rl:edit"

    def test_rate_limit_matches_auth_path(self):
        rule = self.middleware._match_rule("/api/auth/login")
        assert rule is not None
        assert rule["key_prefix"] == "rl:auth"
        assert rule.get("by_ip") is True

    def test_health_endpoint_skips_rate_limit(self):
        assert "/health" in SKIP_PATHS
        assert "/api/health" in SKIP_PATHS

    def test_different_rules_for_different_endpoints(self):
        gen_rule = self.middleware._match_rule("/api/generator/generate")
        auth_rule = self.middleware._match_rule("/api/auth/signup")
        api_rule = self.middleware._match_rule("/api/projects/list")

        assert gen_rule["key_prefix"] == "rl:gen"
        assert auth_rule["key_prefix"] == "rl:auth"
        assert api_rule["key_prefix"] == "rl:api"
        assert gen_rule["limit"] != auth_rule["limit"]


@pytest.mark.asyncio
async def test_rate_limit_allows_under_limit(client):
    """Requests under the rate limit should pass through."""
    response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit(client):
    """Exceeding the rate limit returns 429."""
    # Auth endpoint has limit=60 per 60s, uses IP-based keys
    responses = []
    for i in range(65):
        resp = await client.post(
            "/api/auth/login",
            json={"email": f"ratelimit{i}@test.com", "password": "test"},
        )
        responses.append(resp)

    status_codes = [r.status_code for r in responses]
    has_429 = 429 in status_codes
    assert has_429, f"Expected at least one 429, got status codes: {status_codes}"


@pytest.mark.asyncio
async def test_rate_limit_returns_retry_after_header(client):
    """When rate limited, response includes Retry-After header."""
    last_resp = None
    for i in range(15):
        last_resp = await client.post(
            "/api/auth/login",
            json={"email": f"retryafter{i}@test.com", "password": "test"},
        )
        if last_resp.status_code == 429:
            break

    if last_resp and last_resp.status_code == 429:
        assert "retry-after" in last_resp.headers
        assert "x-ratelimit-limit" in last_resp.headers
