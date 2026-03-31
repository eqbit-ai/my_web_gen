"""
File parser — extracts text from uploaded documents and handles image uploads.

Supports: PDF, TXT, DOCX, DOC, RTF, and common image formats.
Images are uploaded to S3 for use in website generation.
"""

import io
import logging
import os
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_DEPLOYED_BUCKET", "meydan-dev-deployed-sites")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
UPLOAD_PREFIX = "uploads/user-images"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
TEXT_EXTENSIONS = {".txt", ".md", ".rtf", ".csv"}
ZIP_EXTENSIONS = {".zip"}
MAX_TEXT_LENGTH = 10000  # Max chars to extract from documents
MAX_ZIP_FILES = 50  # Max files to extract from a ZIP
MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50MB total uncompressed


def _s3_client():
    return boto3.client("s3", region_name=S3_REGION)


def extract_text(filename: str, content: bytes) -> str | None:
    """Extract text from a document file. Returns None for non-text files."""
    ext = os.path.splitext(filename.lower())[1]

    try:
        if ext == ".pdf":
            return _parse_pdf(content)
        elif ext in (".docx",):
            return _parse_docx(content)
        elif ext in TEXT_EXTENSIONS:
            return content.decode("utf-8", errors="ignore")[:MAX_TEXT_LENGTH]
    except Exception as e:
        logger.warning(f"[FILE_PARSER] Failed to parse {filename}: {e}")

    return None


def _parse_pdf(content: bytes) -> str:
    """Extract text from PDF bytes."""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages[:20]:  # Max 20 pages
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    result = "\n\n".join(text_parts)
    return result[:MAX_TEXT_LENGTH] if result else ""


def _parse_docx(content: bytes) -> str:
    """Extract text from DOCX bytes."""
    from docx import Document

    doc = Document(io.BytesIO(content))
    text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
    result = "\n".join(text_parts)
    return result[:MAX_TEXT_LENGTH] if result else ""


def is_image(filename: str) -> bool:
    """Check if a file is an image based on extension."""
    ext = os.path.splitext(filename.lower())[1]
    return ext in IMAGE_EXTENSIONS


def is_zip(filename: str) -> bool:
    """Check if a file is a ZIP archive."""
    ext = os.path.splitext(filename.lower())[1]
    return ext in ZIP_EXTENSIONS


def extract_zip(content: bytes) -> list[tuple[str, bytes]]:
    """Extract files from a ZIP archive.

    Returns list of (filename, content_bytes) tuples.
    Skips hidden files, __MACOSX, and oversized files.
    """
    import zipfile

    files = []
    total_size = 0

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for info in zf.infolist():
                # Skip directories, hidden files, macOS resource forks
                if info.is_dir():
                    continue
                name = info.filename
                if name.startswith("__MACOSX") or name.startswith(".") or "/." in name:
                    continue

                # Size check
                if info.file_size > 10 * 1024 * 1024:  # 10MB per file
                    logger.warning(f"[FILE_PARSER] Skipping oversized file in ZIP: {name} ({info.file_size} bytes)")
                    continue
                total_size += info.file_size
                if total_size > MAX_ZIP_SIZE:
                    logger.warning("[FILE_PARSER] ZIP total size exceeded limit")
                    break

                if len(files) >= MAX_ZIP_FILES:
                    break

                # Use just the filename, not the full path
                basename = os.path.basename(name)
                if not basename:
                    continue

                file_content = zf.read(info)
                files.append((basename, file_content))

    except zipfile.BadZipFile:
        logger.warning("[FILE_PARSER] Invalid ZIP file")
    except Exception as e:
        logger.warning(f"[FILE_PARSER] ZIP extraction failed: {e}")

    return files


async def upload_image_to_s3(filename: str, content: bytes, user_id: int) -> dict:
    """Upload an image to S3 and return its URL + metadata.

    Returns: {"url": "https://...", "key": "uploads/...", "filename": "original.jpg"}
    """
    ext = os.path.splitext(filename.lower())[1]
    unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
    s3_key = f"{UPLOAD_PREFIX}/{user_id}/{unique_name}"

    content_type_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif", ".svg": "image/svg+xml",
    }
    content_type = content_type_map.get(ext, "application/octet-stream")

    try:
        _s3_client().put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=content_type,
            CacheControl="public, max-age=31536000",
        )
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"[FILE_PARSER] Uploaded image {filename} → {s3_key}")
        return {
            "url": url,
            "key": s3_key,
            "filename": filename,
            "original_name": os.path.splitext(filename)[0].replace("-", " ").replace("_", " ").lower(),
        }
    except (BotoCoreError, ClientError) as e:
        logger.error(f"[FILE_PARSER] S3 upload failed for {filename}: {e}")
        raise
