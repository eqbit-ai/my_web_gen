"""
Admin sub-package — aggregates all admin route modules into a single router.

Usage in main.py:
    from app.routes.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
"""

from fastapi import APIRouter

from .analytics import router as analytics_router
from .domains import router as domains_router
from .edit_logs import router as edit_logs_router
from .generations import router as generations_router
from .operations import router as operations_router
from .sites import router as sites_router
from .stats import router as stats_router
from .tokens import router as tokens_router
from .users import router as users_router

router = APIRouter()

# Include all sub-routers (no prefix — the prefix is set in main.py)
router.include_router(stats_router)
router.include_router(users_router)
router.include_router(sites_router)
router.include_router(generations_router)
router.include_router(domains_router)
router.include_router(tokens_router)
router.include_router(operations_router)
router.include_router(analytics_router)
router.include_router(edit_logs_router)
