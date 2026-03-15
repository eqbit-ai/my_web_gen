"""
Admin platform operations: templates, audit logs, announcements, prompts, system health.
"""

import logging
import os
import platform
import sys

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db
from app.models.announcement import Announcement
from app.models.audit import AuditLog
from app.models.user import User
from app.models.prompt_version import PromptVersion
from app.utils.audit_log import log_event_bg
from app.utils.circuit_breaker import get_circuit_status, reset_circuit
from app.utils.metrics import get_metrics
from app.utils.redis_client import get_redis

from .deps import _serialize_datetime, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin - Operations"])


# ── Schemas ──────────────────────────────────────────────────────────


class AnnouncementCreateRequest(BaseModel):
    title: str
    message: str
    type: str = "info"  # info/warning/maintenance/success
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class AnnouncementUpdateRequest(BaseModel):
    title: str | None = None
    message: str | None = None
    type: str | None = None
    is_active: bool | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class PromptSaveRequest(BaseModel):
    content: str


class TemplateUpdateRequest(BaseModel):
    enabled: bool | None = None
    metadata: dict | None = None


class MessageResponse(BaseModel):
    message: str


# ── Templates ────────────────────────────────────────────────────────


TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "app", "templates_data",
)


@router.get("/templates")
async def list_templates(
    admin=Depends(require_admin),
):
    """List available templates with their enabled status."""
    try:
        # Import the template catalog from the templates route
        from app.routes.templates import TEMPLATE_CATALOG

        templates = []
        for t in TEMPLATE_CATALOG:
            template_file = os.path.join(TEMPLATES_DIR, f"{t['id']}.html")
            templates.append({
                **t,
                "file_exists": os.path.exists(template_file),
                "enabled": True,  # All templates enabled by default
            })

        return {"templates": templates, "total": len(templates)}
    except Exception as e:
        logger.warning("Failed to list templates: %s", e)
        return {"templates": [], "total": 0, "error": str(e)}


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: str,
    req: TemplateUpdateRequest,
    admin=Depends(require_admin),
):
    """Toggle template enabled status or update metadata (placeholder -- stored in memory/config)."""
    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="update_template",
        resource_type="template",
        resource_id=template_id,
        details={"enabled": req.enabled, "metadata": req.metadata},
    )

    return {
        "message": f"Template '{template_id}' configuration updated",
        "template_id": template_id,
    }


# ── Audit Logs ───────────────────────────────────────────────────────


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Full audit log viewer with pagination and filters."""
    try:
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        )
        logs = result.scalars().all()

        # Fetch user emails
        user_ids = list({log.user_id for log in logs if log.user_id})
        user_map = {}
        if user_ids:
            user_result = await db.execute(
                select(User.id, User.email).where(User.id.in_([int(uid) for uid in user_ids if str(uid).isdigit()]))
            )
            user_map = {str(r[0]): r[1] for r in user_result.fetchall()}

        return {
            "audit_logs": [
                {
                    "id": str(log.id),
                    "user_id": log.user_id,
                    "user_email": user_map.get(str(log.user_id), ""),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "created_at": _serialize_datetime(log.created_at),
                }
                for log in logs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list audit logs: %s", e)
        return {"audit_logs": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


# ── Announcements ────────────────────────────────────────────────────


@router.get("/announcements")
async def list_announcements(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all announcements (including inactive)."""
    try:
        count_result = await db.execute(select(func.count(Announcement.id)))
        total = count_result.scalar() or 0

        result = await db.execute(
            select(Announcement)
            .order_by(Announcement.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = result.scalars().all()

        return {
            "announcements": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "message": a.message,
                    "type": a.type,
                    "is_active": a.is_active,
                    "starts_at": _serialize_datetime(a.starts_at),
                    "expires_at": _serialize_datetime(a.expires_at),
                    "created_by": a.created_by,
                    "created_at": _serialize_datetime(a.created_at),
                    "updated_at": _serialize_datetime(a.updated_at),
                }
                for a in items
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.warning("Failed to list announcements: %s", e)
        return {"announcements": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.post("/announcements")
async def create_announcement(
    req: AnnouncementCreateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new announcement."""
    valid_types = {"info", "warning", "maintenance", "success"}
    if req.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")

    try:
        announcement = Announcement(
            title=req.title,
            message=req.message,
            type=req.type,
            starts_at=req.starts_at,
            expires_at=req.expires_at,
            created_by=admin.get("user_id"),
        )
        db.add(announcement)
        await db.commit()
        await db.refresh(announcement)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create announcement: {e}") from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="create_announcement",
        resource_type="announcement",
        resource_id=str(announcement.id),
        details={"title": req.title, "type": req.type},
    )

    return {
        "message": "Announcement created",
        "id": str(announcement.id),
    }


@router.get("/announcements/active")
async def active_announcements(
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint (no admin auth) returning currently active announcements."""
    try:
        now = datetime.now(UTC)
        query = select(Announcement).where(Announcement.is_active == True)

        result = await db.execute(query.order_by(Announcement.created_at.desc()))
        items = result.scalars().all()

        active = []
        for a in items:
            # Filter by time window if set
            if a.starts_at and a.starts_at > now:
                continue
            if a.expires_at and a.expires_at < now:
                continue
            active.append({
                "id": str(a.id),
                "title": a.title,
                "message": a.message,
                "type": a.type,
            })

        return {"announcements": active}
    except Exception as e:
        logger.warning("Failed to fetch active announcements: %s", e)
        return {"announcements": []}


@router.patch("/announcements/{announcement_id}")
async def update_announcement(
    announcement_id: str,
    req: AnnouncementUpdateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update or deactivate an announcement."""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updates = {}
    if req.title is not None:
        updates["title"] = req.title
    if req.message is not None:
        updates["message"] = req.message
    if req.type is not None:
        valid_types = {"info", "warning", "maintenance", "success"}
        if req.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")
        updates["type"] = req.type
    if req.is_active is not None:
        updates["is_active"] = req.is_active
    if req.starts_at is not None:
        updates["starts_at"] = req.starts_at
    if req.expires_at is not None:
        updates["expires_at"] = req.expires_at

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    await db.execute(
        update(Announcement).where(Announcement.id == announcement_id).values(**updates)
    )
    await db.commit()

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="update_announcement",
        resource_type="announcement",
        resource_id=str(announcement_id),
        details=updates,
    )

    return {"message": "Announcement updated", "id": str(announcement_id)}


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an announcement."""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    await db.delete(announcement)
    await db.commit()

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="delete_announcement",
        resource_type="announcement",
        resource_id=str(announcement_id),
        details={"title": announcement.title},
    )

    return {"message": f"Announcement '{announcement.title}' deleted"}


# ── Prompt Versioning ────────────────────────────────────────────────


@router.get("/prompts")
async def list_prompts(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List prompt versions grouped by key."""
    try:
        result = await db.execute(
            select(PromptVersion).order_by(PromptVersion.prompt_key, PromptVersion.version.desc())
        )
        versions = result.scalars().all()

        # Group by key
        grouped = {}
        for v in versions:
            key = v.prompt_key
            if key not in grouped:
                grouped[key] = []
            grouped[key].append({
                "id": str(v.id),
                "version": v.version,
                "is_active": v.is_active,
                "content": v.content or "",
                "published_by": v.published_by,
                "created_at": _serialize_datetime(v.created_at),
            })

        return {"prompts": grouped, "total_keys": len(grouped)}
    except Exception as e:
        logger.warning("Failed to list prompts: %s", e)
        return {"prompts": {}, "total_keys": 0, "error": str(e)}


@router.post("/prompts/{key}")
async def save_prompt_version(
    key: str,
    req: PromptSaveRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Save a new version of a prompt."""
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Content must not be empty")

    try:
        # Get next version number
        max_result = await db.execute(
            select(func.max(PromptVersion.version)).where(PromptVersion.prompt_key == key)
        )
        max_version = max_result.scalar() or 0
        new_version = max_version + 1

        prompt = PromptVersion(
            prompt_key=key,
            version=new_version,
            content=req.content,
            is_active=False,
            published_by=admin.get("user_id"),
        )
        db.add(prompt)
        await db.commit()
        await db.refresh(prompt)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save prompt version: {e}") from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="save_prompt_version",
        resource_type="prompt",
        resource_id=key,
        details={"version": new_version},
    )

    return {
        "message": f"Saved {key} v{new_version}",
        "id": str(prompt.id),
        "key": key,
        "version": new_version,
    }


@router.post("/prompts/{key}/{version}/publish")
async def publish_prompt_version(
    key: str,
    version: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Set a specific version as the active prompt."""
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_key == key,
            PromptVersion.version == version,
        )
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt {key} v{version} not found")

    try:
        # Deactivate all versions for this key
        await db.execute(
            update(PromptVersion)
            .where(PromptVersion.prompt_key == key)
            .values(is_active=False)
        )
        # Activate the target version
        await db.execute(
            update(PromptVersion)
            .where(PromptVersion.prompt_key == key, PromptVersion.version == version)
            .values(is_active=True)
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to publish prompt: {e}") from e

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="publish_prompt_version",
        resource_type="prompt",
        resource_id=key,
        details={"version": version},
    )

    return {"message": f"Published {key} v{version} as active"}


# ── System Health ────────────────────────────────────────────────────


@router.get("/system")
async def system_info(admin=Depends(require_admin)):
    """Enhanced system health and resource usage."""
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "uptime_seconds": get_metrics().get("uptime_seconds", 0),
    }

    # CPU and memory via psutil (optional)
    try:
        import psutil

        info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total_mb": round(mem.total / (1024 * 1024), 1),
            "used_mb": round(mem.used / (1024 * 1024), 1),
            "percent": mem.percent,
        }
        proc = psutil.Process()
        info["process_memory_mb"] = round(proc.memory_info().rss / (1024 * 1024), 1)
    except ImportError:
        info["memory"] = {"error": "psutil not installed"}

    # Redis info
    try:
        r = await get_redis()
        redis_info = await r.info(section="memory")
        info["redis"] = {
            "used_memory_mb": round(int(redis_info.get("used_memory", 0)) / (1024 * 1024), 2),
            "connected_clients": redis_info.get("connected_clients", "unknown"),
        }
        info["redis"]["queue_generate"] = await r.llen("queue:generate")
    except Exception as e:
        info["redis"] = {"error": str(e)}

    # Database connection pool stats
    try:
        pool = engine.pool
        info["database_pool"] = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    except Exception as e:
        info["database_pool"] = {"error": str(e)}

    # Circuit breaker states
    info["circuit_breakers"] = get_circuit_status()

    # Metrics summary
    metrics = get_metrics()
    info["metrics"] = metrics

    # Error rates from metrics
    total_requests = metrics.get("counters", {}).get("requests_total", 0)
    info["error_rates"] = {
        "total_requests": total_requests,
    }

    return info


# ── Circuit Breaker Management ───────────────────────────────────────


@router.post("/circuit/{provider}/reset", response_model=MessageResponse)
async def reset_circuit_breaker(
    provider: str,
    admin=Depends(require_admin),
):
    """Manually reset a circuit breaker to closed state."""
    success = await reset_circuit(provider)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No circuit breaker found for provider '{provider}'",
        )

    log_event_bg(
        user_id=str(admin.get("user_id")),
        action="reset_circuit_breaker",
        resource_type="circuit_breaker",
        resource_id=provider,
    )

    return {"message": f"Circuit breaker for '{provider}' reset to CLOSED"}


# ── Moderation (moved from old admin.py) ─────────────────────────────


@router.get("/moderation")
async def moderation_queue(
    limit: int = Query(default=50, ge=1, le=200),
    admin=Depends(require_admin),
):
    """List flagged prompts from the moderation queue."""
    try:
        r = await get_redis()
        items = await r.zrevrange("moderation:flagged", 0, limit - 1, withscores=True)

        flagged = []
        for item_json, score in items:
            try:
                import json

                item = json.loads(item_json)
                item["flagged_at"] = score
                flagged.append(item)
            except Exception:
                flagged.append({"raw": item_json, "flagged_at": score})

        return {"flagged": flagged, "total": await r.zcard("moderation:flagged")}
    except Exception as e:
        logger.warning("Failed to fetch moderation queue: %s", e)
        return {"flagged": [], "total": 0, "error": str(e)}


@router.post("/moderation/{action}")
async def moderation_action(
    action: str,
    item_id: str = Query(...),
    admin=Depends(require_admin),
):
    """Moderate a flagged item: approve, reject, or ban."""
    if action not in ("approve", "reject", "ban"):
        raise HTTPException(status_code=400, detail="Action must be: approve, reject, or ban")

    try:
        r = await get_redis()

        if action in ("approve", "reject"):
            items = await r.zrange("moderation:flagged", 0, -1)
            for item in items:
                if item_id in item:
                    await r.zrem("moderation:flagged", item)
                    break
            return {"message": f"Item {item_id} {action}d and removed from queue"}

        elif action == "ban":
            items = await r.zrange("moderation:flagged", 0, -1)
            for item in items:
                if item_id in item:
                    try:
                        import json

                        data = json.loads(item)
                        banned_user = data.get("user_id")
                        if banned_user:
                            await r.sadd("moderation:banned_users", str(banned_user))
                    except Exception:
                        pass
                    await r.zrem("moderation:flagged", item)
                    break
            return {"message": f"Item {item_id} removed, user banned"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moderation action failed: {e}") from e
