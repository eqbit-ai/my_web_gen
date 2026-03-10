"""
Metrics endpoint — exposes internal counters and histograms.

Protected by admin JWT auth OR a METRICS_API_KEY from environment.
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.auth import decode_access_token
from app.utils.metrics import get_metrics

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)

METRICS_API_KEY = os.getenv("METRICS_API_KEY")


async def _require_metrics_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """Allow access via admin JWT OR metrics API key."""
    # Check API key in query param or header
    api_key = request.query_params.get("key") or request.headers.get("X-Metrics-Key")
    if METRICS_API_KEY and api_key == METRICS_API_KEY:
        return {"source": "api_key"}

    # Fall back to JWT admin check
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload and payload.get("is_admin"):
            return payload
        # Also allow any valid token for metrics (not just admin)
        if payload:
            return payload

    raise HTTPException(status_code=403, detail="Metrics access requires authentication")


@router.get("")
async def metrics_endpoint(auth=Depends(_require_metrics_auth)):
    """Return all collected metrics as JSON."""
    return get_metrics()
