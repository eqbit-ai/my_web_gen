"""
Audit logging — fire-and-forget event logging to PostgreSQL.

Usage:
    await log_event(
        user_id="123",
        action="generate_website",
        resource_type="website",
        resource_id="session-uuid",
        details={"prompt": "build me a ..."},
        ip_address="1.2.3.4",
    )
"""

import asyncio
import traceback

from app.database import async_session
from app.models.audit import AuditLog

# Set to prevent premature garbage collection of fire-and-forget tasks
_background_tasks: set = set()


async def log_event(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None,
):
    """
    Log an audit event to the database.

    Fire-and-forget: errors are printed but never raised to the caller.

    Actions:
        - generate_website
        - edit_website
        - save_project
        - delete_project
        - login
        - signup
        - download
    """
    try:
        async with async_session() as session:
            entry = AuditLog(
                user_id=str(user_id),
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
            )
            session.add(entry)
            await session.commit()
    except Exception as e:
        # Fire-and-forget: never crash the request
        print(f"[AuditLog] Failed to log event ({action}): {e}", flush=True)
        traceback.print_exc()


def log_event_bg(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None,
):
    """
    Schedule an audit log event as a background task (non-blocking).
    Safe to call from sync or async context — will not slow down the request.
    """
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(
            log_event(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
            )
        )
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
    except RuntimeError:
        # No running loop — skip logging silently
        pass
