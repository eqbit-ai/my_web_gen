"""
File storage abstraction — local disk now, S3/R2 later.
Handles save, delete, list operations for uploaded media.
"""

import uuid
from pathlib import Path

import aiofiles
import aiofiles.os

# Base upload directory
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

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


def _get_extension(filename: str) -> str:
    """Extract lowercase extension from filename."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_file(filename: str, size: int, category: str) -> str | None:
    """
    Validate file extension and size.
    Returns error message string or None if valid.
    """
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
    """
    Save a file to local disk.
    Returns dict with url, stored_filename, size, etc.
    """
    ext = _get_extension(filename)
    stored_name = f"{uuid.uuid4()}.{ext}"

    # Build path: uploads/{user_id}/{project_id}/{uuid}.{ext}
    rel_parts = [str(user_id)]
    if project_id:
        rel_parts.append(project_id)
    rel_dir = Path(*rel_parts)
    abs_dir = UPLOAD_DIR / rel_dir

    await aiofiles.os.makedirs(str(abs_dir), exist_ok=True)

    abs_path = abs_dir / stored_name
    async with aiofiles.open(str(abs_path), "wb") as f:
        await f.write(file_bytes)

    # URL path served by StaticFiles mount
    url = f"/uploads/{rel_dir}/{stored_name}"

    return {
        "filename": stored_name,
        "original_name": filename,
        "url": url,
        "size_bytes": len(file_bytes),
        "category": category,
        "ext": ext,
    }


async def delete_file(file_url: str) -> bool:
    """
    Delete a file given its URL path (e.g. /uploads/1/proj/uuid.png).
    Returns True if deleted, False if not found.
    """
    # Strip leading /uploads/ to get relative path
    rel = file_url.lstrip("/")
    if rel.startswith("uploads/"):
        rel = rel[len("uploads/") :]
    abs_path = UPLOAD_DIR / rel

    if await aiofiles.os.path.exists(str(abs_path)):
        await aiofiles.os.remove(str(abs_path))
        return True
    return False


async def list_files(user_id: int, project_id: str | None = None) -> list[dict]:
    """
    List all uploaded files for a user (and optionally a project).
    Returns list of dicts with filename, url, size_bytes.
    """
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
            results.append(
                {
                    "filename": entry,
                    "url": f"/uploads/{rel}",
                    "size_bytes": stat.st_size,
                }
            )
        elif await aiofiles.os.path.isdir(str(entry_path)):
            # Recurse one level for project subdirectories
            sub_entries = await aiofiles.os.listdir(str(entry_path))
            for sub in sub_entries:
                sub_path = entry_path / sub
                if await aiofiles.os.path.isfile(str(sub_path)):
                    stat = await aiofiles.os.stat(str(sub_path))
                    rel = str(sub_path.relative_to(UPLOAD_DIR))
                    results.append(
                        {
                            "filename": sub,
                            "url": f"/uploads/{rel}",
                            "size_bytes": stat.st_size,
                        }
                    )

    return results
