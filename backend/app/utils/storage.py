"""
File storage — S3 for production (ECS), local disk as fallback.

Uploaded files go to S3 bucket and return a public URL.
Falls back to local /uploads/ directory if S3 is not configured.
"""

import logging
import os
import uuid
from io import BytesIO
from pathlib import Path

import aiofiles
import aiofiles.os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# Base upload directory (local fallback)
UPLOAD_DIR = (Path(__file__).resolve().parent.parent.parent / "uploads").resolve()


def _resolve_within_upload_dir(rel_path: str) -> Path | None:
    """Resolve a user-supplied relative path against UPLOAD_DIR and ensure the
    result stays inside UPLOAD_DIR. Returns None if the path escapes the
    upload directory (via .. or an absolute path component)."""
    if not rel_path:
        return None
    candidate = (UPLOAD_DIR / rel_path).resolve()
    try:
        candidate.relative_to(UPLOAD_DIR)
    except ValueError:
        return None
    return candidate

# S3 config
S3_UPLOAD_BUCKET = os.getenv("AWS_S3_UPLOAD_BUCKET", os.getenv("AWS_S3_DEPLOY_BUCKET", ""))
S3_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
S3_UPLOAD_PREFIX = "user-uploads"

# Allowed extensions by category
ALLOWED_EXTENSIONS = {
    "image": {"jpg", "jpeg", "png", "webp", "svg", "gif", "ico"},
    "logo": {"jpg", "jpeg", "png", "webp", "svg", "gif", "ico"},
    "favicon": {"jpg", "jpeg", "png", "webp", "svg", "gif", "ico"},
    "video": {"mp4", "webm"},
}

# Size limits in bytes
SIZE_LIMITS = {
    "image": 5 * 1024 * 1024,  # 5 MB
    "logo": 5 * 1024 * 1024,  # 5 MB
    "favicon": 5 * 1024 * 1024,  # 5 MB
    "video": 50 * 1024 * 1024,  # 50 MB
}

# MIME type mapping for S3 content type
EXT_TO_MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "webp": "image/webp", "gif": "image/gif", "svg": "image/svg+xml",
    "ico": "image/x-icon", "mp4": "video/mp4", "webm": "video/webm",
}


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _use_s3() -> bool:
    return bool(S3_UPLOAD_BUCKET)


def _s3_client():
    return boto3.client("s3", region_name=S3_REGION)


def validate_file(filename: str, size: int, category: str) -> str | None:
    ext = _get_extension(filename)
    allowed = ALLOWED_EXTENSIONS.get(category)
    if allowed is None:
        return f"Unknown category: {category}"
    if ext not in allowed:
        return f"File type .{ext} not allowed for category '{category}'. Allowed: {', '.join(sorted(allowed))}"
    limit = SIZE_LIMITS.get(category, 5 * 1024 * 1024)
    if size > limit:
        limit_mb = limit / (1024 * 1024)
        return f"File too large ({size / (1024 * 1024):.1f} MB). Limit for '{category}' is {limit_mb:.0f} MB."
    return None


async def save_file(
    file_bytes: bytes,
    filename: str,
    user_id: int,
    project_id: str | None,
    category: str = "image",
) -> dict:
    ext = _get_extension(filename)
    stored_name = f"{uuid.uuid4()}.{ext}"

    if _use_s3():
        return await _save_to_s3(file_bytes, stored_name, ext, user_id, project_id, filename, category)
    else:
        return await _save_to_disk(file_bytes, stored_name, ext, user_id, project_id, filename, category)


async def _save_to_s3(file_bytes, stored_name, ext, user_id, project_id, original_name, category):
    """Save file to S3 and return public URL."""
    parts = [S3_UPLOAD_PREFIX, str(user_id)]
    if project_id:
        parts.append(project_id)
    parts.append(stored_name)
    s3_key = "/".join(parts)

    content_type = EXT_TO_MIME.get(ext, "application/octet-stream")

    try:
        s3 = _s3_client()
        s3.put_object(
            Bucket=S3_UPLOAD_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
        )

        # Build URL — use S3 website endpoint or direct URL
        url = f"https://{S3_UPLOAD_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"[STORAGE] Uploaded to S3: {s3_key} ({len(file_bytes)} bytes)")

        return {
            "filename": stored_name,
            "original_name": original_name,
            "url": url,
            "size_bytes": len(file_bytes),
            "category": category,
            "ext": ext,
        }
    except (BotoCoreError, ClientError) as e:
        logger.error(f"[STORAGE] S3 upload failed: {e}")
        # Fallback to local disk
        return await _save_to_disk(file_bytes, stored_name, ext, int(str(user_id)), None, original_name, category)


async def _save_to_disk(file_bytes, stored_name, ext, user_id, project_id, original_name, category):
    """Save file to local disk (development/fallback)."""
    rel_parts = [str(user_id)]
    if project_id:
        rel_parts.append(project_id)
    rel_dir = Path(*rel_parts)
    abs_dir = UPLOAD_DIR / rel_dir

    await aiofiles.os.makedirs(str(abs_dir), exist_ok=True)

    abs_path = abs_dir / stored_name
    async with aiofiles.open(str(abs_path), "wb") as f:
        await f.write(file_bytes)

    url = f"/uploads/{rel_dir}/{stored_name}"

    return {
        "filename": stored_name,
        "original_name": original_name,
        "url": url,
        "size_bytes": len(file_bytes),
        "category": category,
        "ext": ext,
    }


async def delete_file(file_url: str) -> bool:
    """Delete a file given its URL."""
    if file_url.startswith("https://") and S3_UPLOAD_BUCKET in file_url:
        # S3 file — extract key from URL
        try:
            # URL format: https://{bucket}.s3.{region}.amazonaws.com/{key}
            key = file_url.split(f"{S3_UPLOAD_BUCKET}.s3.{S3_REGION}.amazonaws.com/", 1)[1]
            _s3_client().delete_object(Bucket=S3_UPLOAD_BUCKET, Key=key)
            logger.info(f"[STORAGE] Deleted from S3: {key}")
            return True
        except Exception as e:
            logger.warning(f"[STORAGE] S3 delete failed: {e}")
            return False
    else:
        # Local file — reject any path that tries to escape UPLOAD_DIR.
        rel = file_url.lstrip("/")
        if rel.startswith("uploads/"):
            rel = rel[len("uploads/"):]
        abs_path = _resolve_within_upload_dir(rel)
        if abs_path is None:
            logger.warning("[STORAGE] Rejected path traversal in delete: %s", file_url)
            return False
        if await aiofiles.os.path.exists(str(abs_path)):
            await aiofiles.os.remove(str(abs_path))
            return True
        return False


async def list_files(user_id: int, project_id: str | None = None) -> list[dict]:
    """List all uploaded files for a user (local disk only — S3 uses DB queries)."""
    parts = [str(user_id)]
    if project_id:
        parts.append(project_id)
    target_dir = UPLOAD_DIR / Path(*parts)

    if not await aiofiles.os.path.exists(str(target_dir)):
        return []

    results = []
    entries = await aiofiles.os.listdir(str(target_dir))
    for entry in entries:
        entry_path = target_dir / entry
        if await aiofiles.os.path.isfile(str(entry_path)):
            stat = await aiofiles.os.stat(str(entry_path))
            rel = str(entry_path.relative_to(UPLOAD_DIR))
            results.append({
                "filename": entry,
                "url": f"/uploads/{rel}",
                "size_bytes": stat.st_size,
            })
        elif await aiofiles.os.path.isdir(str(entry_path)):
            sub_entries = await aiofiles.os.listdir(str(entry_path))
            for sub in sub_entries:
                sub_path = entry_path / sub
                if await aiofiles.os.path.isfile(str(sub_path)):
                    stat = await aiofiles.os.stat(str(sub_path))
                    rel = str(sub_path.relative_to(UPLOAD_DIR))
                    results.append({
                        "filename": sub,
                        "url": f"/uploads/{rel}",
                        "size_bytes": stat.st_size,
                    })

    return results
