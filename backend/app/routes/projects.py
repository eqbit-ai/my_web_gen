"""
Projects routes — CRUD + version history for saved website projects.
Supports undo/redo/rollback via versioned snapshots.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.exc import ProgrammingError

logger = logging.getLogger(__name__)

from sqlalchemy import text as sa_text

from app.database import get_tenant_db
from app.models.project import Project, ProjectVersion
from app.utils.auth import decode_access_token

# Cache which tenant schemas already have deleted_at column
_schemas_with_deleted_at: set[str] = set()

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return token_data


# ── Schemas ──────────────────────────────────────────────────────────────


class SaveProjectRequest(BaseModel):
    project_id: str | None = None
    name: str = "Untitled Project"
    html: str
    css: str
    js: str = ""
    prompt: str = ""
    metadata: str = "{}"


class RollbackRequest(BaseModel):
    version_number: int


# ── Endpoints ────────────────────────────────────────────────────────────


async def _ensure_deleted_at(db, schema: str):
    """Ensure deleted_at column exists on the projects table for this tenant schema."""
    if schema in _schemas_with_deleted_at:
        return
    try:
        await db.execute(sa_text(
            f'ALTER TABLE "{schema}".projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ'
        ))
        await db.commit()
    except Exception:
        await db.rollback()
    _schemas_with_deleted_at.add(schema)


@router.get("/")
async def list_projects(user: dict = Depends(require_auth)):
    """List all projects for the current user."""
    async for db in get_tenant_db(user["db_schema"]):
        await _ensure_deleted_at(db, user["db_schema"])
        result = await db.execute(
            select(Project).where(
                Project.user_id == user["user_id"],
                Project.deleted_at.is_(None),
            ).order_by(Project.updated_at.desc())
        )
        projects = result.scalars().all()

        items = []
        for p in projects:
            # Get version count
            count_result = await db.execute(select(func.count()).where(ProjectVersion.project_id == p.id))
            version_count = count_result.scalar() or 0

            # Parse metadata JSON safely
            try:
                parsed_meta = json.loads(p.project_metadata) if p.project_metadata else {}
            except (json.JSONDecodeError, TypeError):
                parsed_meta = {}

            items.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "current_version": p.current_version,
                    "total_versions": version_count,
                    "has_content": bool(p.current_html),
                    "html": p.current_html or "",
                    "css": p.current_css or "",
                    "metadata": parsed_meta,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
            )

        return {"projects": items}


@router.get("/{project_id}")
async def get_project(project_id: str, user: dict = Depends(require_auth)):
    """Get a project with its current code."""
    async for db in get_tenant_db(user["db_schema"]):
        await _ensure_deleted_at(db, user["db_schema"])
        result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user["user_id"], Project.deleted_at.is_(None)))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Parse metadata JSON safely
        try:
            parsed_meta = json.loads(project.project_metadata) if project.project_metadata else {}
        except (json.JSONDecodeError, TypeError):
            parsed_meta = {}

        return {
            "id": project.id,
            "name": project.name,
            "html": project.current_html,
            "css": project.current_css,
            "js": project.current_js,
            "metadata": parsed_meta,
            "current_version": project.current_version,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }


@router.post("/save")
async def save_project(req: SaveProjectRequest, user: dict = Depends(require_auth)):
    """Save or update a project. Creates a new version snapshot each time."""
    async for db in get_tenant_db(user["db_schema"]):
        if req.project_id:
            # Update existing project
            result = await db.execute(
                select(Project).where(Project.id == req.project_id, Project.user_id == user["user_id"])
            )
            project = result.scalar_one_or_none()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            project.current_html = req.html
            project.current_css = req.css
            project.current_js = req.js
            project.project_metadata = req.metadata
            project.current_version += 1
            if req.name and req.name != "Untitled Project":
                project.name = req.name
        else:
            # Create new project
            project = Project(
                user_id=user["user_id"],
                name=req.name,
                current_html=req.html,
                current_css=req.css,
                current_js=req.js,
                project_metadata=req.metadata,
                current_version=1,
            )
            db.add(project)
            await db.flush()

        # Create version snapshot
        version = ProjectVersion(
            project_id=project.id,
            version_number=project.current_version,
            html=req.html,
            css=req.css,
            js=req.js,
            prompt=req.prompt,
        )
        db.add(version)
        await db.commit()

        return {
            "project_id": project.id,
            "version": project.current_version,
            "name": project.name,
        }


@router.get("/{project_id}/versions")
async def list_versions(project_id: str, user: dict = Depends(require_auth)):
    """List all version snapshots for a project (for history/undo/redo)."""
    async for db in get_tenant_db(user["db_schema"]):
        # Verify ownership
        result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user["user_id"]))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        result = await db.execute(
            select(ProjectVersion)
            .where(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number.desc())
        )
        versions = result.scalars().all()

        return {
            "current_version": project.current_version,
            "versions": [
                {
                    "version_number": v.version_number,
                    "prompt": v.prompt,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in versions
            ],
        }


@router.get("/{project_id}/versions/{version_number}")
async def get_version(project_id: str, version_number: int, user: dict = Depends(require_auth)):
    """Get a specific version's code (for rollback preview)."""
    async for db in get_tenant_db(user["db_schema"]):
        # Verify ownership
        result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user["user_id"]))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Project not found")

        result = await db.execute(
            select(ProjectVersion).where(
                ProjectVersion.project_id == project_id,
                ProjectVersion.version_number == version_number,
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        return {
            "version_number": version.version_number,
            "html": version.html,
            "css": version.css,
            "js": version.js,
            "prompt": version.prompt,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }


@router.post("/{project_id}/rollback")
async def rollback_project(
    project_id: str,
    req: RollbackRequest,
    user: dict = Depends(require_auth),
):
    """Rollback a project to a specific version."""
    async for db in get_tenant_db(user["db_schema"]):
        result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user["user_id"]))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        result = await db.execute(
            select(ProjectVersion).where(
                ProjectVersion.project_id == project_id,
                ProjectVersion.version_number == req.version_number,
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        # Update current code to the rollback version
        project.current_html = version.html
        project.current_css = version.css
        project.current_js = version.js
        project.current_version = req.version_number

        await db.commit()

        return {
            "success": True,
            "version": req.version_number,
            "html": version.html,
            "css": version.css,
            "js": version.js,
        }


@router.put("/{project_id}/name")
async def rename_project(project_id: str, user: dict = Depends(require_auth), name: str = ""):
    """Rename a project."""
    async for db in get_tenant_db(user["db_schema"]):
        result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user["user_id"]))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.name = name or "Untitled Project"
        await db.commit()

        return {"success": True, "name": project.name}


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(require_auth)):
    """Soft-delete a project (can be restored by admin). Falls back to hard delete if column missing."""
    from datetime import datetime, timezone

    async for db in get_tenant_db(user["db_schema"]):
        await _ensure_deleted_at(db, user["db_schema"])
        result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user["user_id"]))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.deleted_at = datetime.now(timezone.utc)
        await db.commit()

        return {"success": True}
