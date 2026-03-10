"""
Sentry error tracking setup.

Only activates if the SENTRY_DSN environment variable is set.
If sentry-sdk is not installed, logs a warning and continues gracefully.
"""

import os
import logging

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry if SENTRY_DSN is configured."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("SENTRY_DSN not set — Sentry disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            send_default_pii=False,
        )
        logger.info("Sentry initialized successfully")
    except ImportError:
        logger.warning("sentry-sdk not installed — Sentry disabled")
