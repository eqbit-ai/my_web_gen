"""
Upload routes — file upload, list, delete, download-from-URL, and image transforms.
"""

import uuid
import mimetypes
from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.auth import decode_access_token
from app.database import get_tenant_db
from app.models.media import Media
from app.utils.storage import save_file, delete_file, list_files, validate_file

router = APIRouter()
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data


# ── Schemas ──────────────────────────────────────────────────────────────

class FromUrlRequest(BaseModel):
    url: str
    project_id: str | None = None
    category: str = "image"


class TransformRequest(BaseModel):
    filename: str
    project_id: str | None = None
    crop: dict | None = None         # {x, y, width, height}
    target_width: int | None = None
    target_height: int | None = None


# ── Helpers ──────────────────────────────────────────────────────────────

def _get_image_dimensions(file_bytes: bytes) -> tuple[int | None, int | None]:
    """Try to get image dimensions using Pillow. Returns (width, height) or (None, None)."""
    try:
        from PIL import Image
        img = Image.open(BytesIO(file_bytes))
        return img.size  # (width, height)
    except Exception:
        return None, None


def _guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Form(default=""),
    category: str = Form(default="image"),
    user: dict = Depends(require_auth),
):
    """Upload a file (image, logo, favicon, or video)."""
    file_bytes = await file.read()
    original_name = file.filename or "unknown"

    # Validate
    error = validate_file(original_name, len(file_bytes), category)
    if error:
        raise HTTPException(status_code=400, detail=error)

    proj_id = project_id if project_id else None

    # Save to disk
    result = save_file.__wrapped__ if hasattr(save_file, '__wrapped__') else save_file
    saved = await save_file(file_bytes, original_name, user["user_id"], proj_id, category)

    # Get dimensions for images
    width, height = None, None
    if category in ("image", "logo", "favicon"):
        width, height = _get_image_dimensions(file_bytes)

    mime = _guess_mime(original_name)

    # Save to database
    media = Media(
        id=str(uuid.uuid4()),
        user_id=user["user_id"],
        project_id=proj_id,
        filename=saved["filename"],
        original_name=original_name,
        mime_type=mime,
        size_bytes=saved["size_bytes"],
        width=width,
        height=height,
        url=saved["url"],
        category=category,
    )

    async for db in get_tenant_db(user["db_schema"]):
        db.add(media)
        await db.commit()
        await db.refresh(media)

        return {
            "id": media.id,
            "filename": media.filename,
            "original_name": media.original_name,
            "url": media.url,
            "mime_type": media.mime_type,
            "size_bytes": media.size_bytes,
            "width": media.width,
            "height": media.height,
            "category": media.category,
            "created_at": media.created_at.isoformat() if media.created_at else None,
        }


@router.get("/list/{project_id}")
async def list_uploads(project_id: str, user: dict = Depends(require_auth)):
    """List all uploads for a project."""
    async for db in get_tenant_db(user["db_schema"]):
        result = await db.execute(
            select(Media)
            .where(Media.user_id == user["user_id"], Media.project_id == project_id)
            .order_by(Media.created_at.desc())
        )
        items = result.scalars().all()

        return {
            "files": [
                {
                    "id": m.id,
                    "filename": m.filename,
                    "original_name": m.original_name,
                    "url": m.url,
                    "mime_type": m.mime_type,
                    "size_bytes": m.size_bytes,
                    "width": m.width,
                    "height": m.height,
                    "category": m.category,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in items
            ]
        }


@router.delete("/{filename}")
async def delete_upload(filename: str, user: dict = Depends(require_auth)):
    """Delete an uploaded file by filename."""
    async for db in get_tenant_db(user["db_schema"]):
        result = await db.execute(
            select(Media).where(Media.filename == filename, Media.user_id == user["user_id"])
        )
        media = result.scalar_one_or_none()
        if not media:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete from disk
        await delete_file(media.url)

        # Delete from DB
        await db.execute(
            sa_delete(Media).where(Media.id == media.id)
        )
        await db.commit()

        return {"success": True, "filename": filename}


@router.post("/from-url")
async def upload_from_url(req: FromUrlRequest, user: dict = Depends(require_auth)):
    """Download an image from a URL and save it locally."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(req.url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to download: {str(e)}")

    file_bytes = resp.content

    # Try to determine filename from URL
    url_path = req.url.split("?")[0].split("#")[0]
    original_name = url_path.rsplit("/", 1)[-1] or "downloaded.jpg"
    if "." not in original_name:
        # Try to get extension from content-type
        ct = resp.headers.get("content-type", "image/jpeg")
        ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif", "image/svg+xml": "svg"}
        ext = ext_map.get(ct.split(";")[0].strip(), "jpg")
        original_name = f"downloaded.{ext}"

    error = validate_file(original_name, len(file_bytes), req.category)
    if error:
        raise HTTPException(status_code=400, detail=error)

    saved = await save_file(file_bytes, original_name, user["user_id"], req.project_id, req.category)

    width, height = None, None
    if req.category in ("image", "logo", "favicon"):
        width, height = _get_image_dimensions(file_bytes)

    mime = _guess_mime(original_name)

    media = Media(
        id=str(uuid.uuid4()),
        user_id=user["user_id"],
        project_id=req.project_id,
        filename=saved["filename"],
        original_name=original_name,
        mime_type=mime,
        size_bytes=saved["size_bytes"],
        width=width,
        height=height,
        url=saved["url"],
        category=req.category,
    )

    async for db in get_tenant_db(user["db_schema"]):
        db.add(media)
        await db.commit()
        await db.refresh(media)

        return {
            "id": media.id,
            "filename": media.filename,
            "original_name": media.original_name,
            "url": media.url,
            "mime_type": media.mime_type,
            "size_bytes": media.size_bytes,
            "width": media.width,
            "height": media.height,
            "category": media.category,
            "created_at": media.created_at.isoformat() if media.created_at else None,
        }


@router.post("/transform")
async def transform_image(req: TransformRequest, user: dict = Depends(require_auth)):
    """Crop and/or resize an uploaded image using Pillow."""
    try:
        from PIL import Image
    except ImportError:
        raise HTTPException(status_code=500, detail="Pillow is not installed. Cannot transform images.")

    # Find the media record
    async for db in get_tenant_db(user["db_schema"]):
        result = await db.execute(
            select(Media).where(Media.filename == req.filename, Media.user_id == user["user_id"])
        )
        media = result.scalar_one_or_none()
        if not media:
            raise HTTPException(status_code=404, detail="File not found")

        # Read the file from disk
        from app.utils.storage import UPLOAD_DIR
        rel = media.url.lstrip("/")
        if rel.startswith("uploads/"):
            rel = rel[len("uploads/"):]
        abs_path = UPLOAD_DIR / rel

        try:
            import aiofiles
            async with aiofiles.open(str(abs_path), "rb") as f:
                file_bytes = await f.read()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found on disk")

        img = Image.open(BytesIO(file_bytes))

        # Crop
        if req.crop:
            x = req.crop.get("x", 0)
            y = req.crop.get("y", 0)
            w = req.crop.get("width", img.width)
            h = req.crop.get("height", img.height)
            img = img.crop((x, y, x + w, y + h))

        # Resize
        if req.target_width or req.target_height:
            tw = req.target_width or img.width
            th = req.target_height or img.height
            img = img.resize((tw, th), Image.LANCZOS)

        # Save transformed image as new file
        buf = BytesIO()
        fmt = img.format or "PNG"
        if fmt.upper() == "JPEG":
            img = img.convert("RGB")
        img.save(buf, format=fmt, quality=90)
        transformed_bytes = buf.getvalue()

        saved = await save_file(
            transformed_bytes,
            f"transformed_{req.filename}",
            user["user_id"],
            req.project_id,
            media.category,
        )

        new_media = Media(
            id=str(uuid.uuid4()),
            user_id=user["user_id"],
            project_id=req.project_id,
            filename=saved["filename"],
            original_name=f"transformed_{media.original_name}",
            mime_type=media.mime_type,
            size_bytes=saved["size_bytes"],
            width=img.width,
            height=img.height,
            url=saved["url"],
            category=media.category,
        )

        db.add(new_media)
        await db.commit()
        await db.refresh(new_media)

        return {
            "id": new_media.id,
            "filename": new_media.filename,
            "original_name": new_media.original_name,
            "url": new_media.url,
            "mime_type": new_media.mime_type,
            "size_bytes": new_media.size_bytes,
            "width": new_media.width,
            "height": new_media.height,
            "category": new_media.category,
            "created_at": new_media.created_at.isoformat() if new_media.created_at else None,
        }
