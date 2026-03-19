"""
Upload routes — file upload, list, delete, download-from-URL, and image transforms.
"""

import ipaddress
import mimetypes
import uuid
from io import BytesIO
import urllib.parse
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete
from sqlalchemy import select

from app.database import get_tenant_db
from app.models.media import Media
from app.utils.auth import decode_access_token
from app.utils.storage import delete_file, save_file, validate_file

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
    crop: dict | None = None  # {x, y, width, height}
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
        result = await db.execute(select(Media).where(Media.filename == filename, Media.user_id == user["user_id"]))
        media = result.scalar_one_or_none()
        if not media:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete from disk
        await delete_file(media.url)

        # Delete from DB
        await db.execute(sa_delete(Media).where(Media.id == media.id))
        await db.commit()

        return {"success": True, "filename": filename}


@router.post("/from-url")
async def upload_from_url(req: FromUrlRequest, user: dict = Depends(require_auth)):
    """Download an image from a URL and save it locally."""
    # SSRF protection: validate URL before fetching
    try:
        parsed = urlparse(req.url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL") from None

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are allowed")

    hostname = parsed.hostname or ""
    # Block private/internal IPs and metadata endpoints
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise HTTPException(status_code=400, detail="URLs pointing to internal networks are not allowed")
    except ValueError:
        # It's a hostname, not an IP — block known internal hostnames
        blocked = {"localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal", "169.254.169.254"}
        if hostname.lower() in blocked or hostname.endswith(".internal") or hostname.endswith(".local"):
            raise HTTPException(status_code=400, detail="URLs pointing to internal networks are not allowed") from None

    # Reconstruct URL from validated components to prevent injection
    safe_url = parsed._replace(
        path="/".join(urllib.parse.quote(seg, safe="") for seg in parsed.path.split("/")),
    ).geturl()

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False, max_redirects=0) as client:
            resp = await client.get(safe_url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to download: {str(e)}") from e

    file_bytes = resp.content

    # Try to determine filename from URL (sanitize to prevent path traversal)
    url_path = req.url.split("?")[0].split("#")[0]
    original_name = os.path.basename(url_path.rsplit("/", 1)[-1]) or "downloaded.jpg"
    # Strip any remaining path separators or traversal attempts
    original_name = original_name.replace("/", "").replace("\\", "").replace("..", "")
    if "." not in original_name:
        # Try to get extension from content-type
        ct = resp.headers.get("content-type", "image/jpeg")
        ext_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
            "image/svg+xml": "svg",
        }
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
    except ImportError as e:
        raise HTTPException(status_code=500, detail="Pillow is not installed. Cannot transform images.") from e

    # Find the media record
    async for db in get_tenant_db(user["db_schema"]):
        result = await db.execute(select(Media).where(Media.filename == req.filename, Media.user_id == user["user_id"]))
        media = result.scalar_one_or_none()
        if not media:
            raise HTTPException(status_code=404, detail="File not found")

        # Read the file from disk
        from app.utils.storage import UPLOAD_DIR

        rel = media.url.lstrip("/")
        if rel.startswith("uploads/"):
            rel = rel[len("uploads/") :]
        abs_path = UPLOAD_DIR / rel

        try:
            import aiofiles

            async with aiofiles.open(str(abs_path), "rb") as f:
                file_bytes = await f.read()
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail="File not found on disk") from e

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
