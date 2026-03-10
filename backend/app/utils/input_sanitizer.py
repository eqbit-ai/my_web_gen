"""
Input sanitization utilities — prompt cleaning, filename safety, ID validation.
"""

import re
import uuid

# HTML tag pattern
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Null bytes
_NULL_BYTE_RE = re.compile(r"\x00")

# Multiple whitespace
_MULTI_WHITESPACE_RE = re.compile(r"\s+")

# Valid filename characters
_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]")

# License number: alphanumeric + hyphens
_LICENSE_RE = re.compile(r"^[a-zA-Z0-9\-]{5,50}$")


def sanitize_prompt(prompt: str, max_length: int = 2000) -> str:
    """
    Sanitize a user prompt:
    - Truncate to max_length characters
    - Strip HTML tags
    - Remove null bytes
    - Normalize whitespace
    - Strip leading/trailing whitespace
    """
    if not prompt:
        return ""

    # Remove null bytes
    prompt = _NULL_BYTE_RE.sub("", prompt)

    # Strip HTML tags
    prompt = _HTML_TAG_RE.sub("", prompt)

    # Normalize whitespace (collapse multiple spaces/newlines)
    prompt = _MULTI_WHITESPACE_RE.sub(" ", prompt)

    # Strip leading/trailing whitespace
    prompt = prompt.strip()

    # Truncate to max length
    if len(prompt) > max_length:
        prompt = prompt[:max_length]

    return prompt


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename:
    - Allow only alphanumeric characters, hyphens, dots, and underscores
    - Truncate to max_length characters
    - Prevent directory traversal
    """
    if not filename:
        return ""

    # Remove any path components (prevent directory traversal)
    filename = filename.replace("/", "").replace("\\", "")

    # Replace unsafe characters
    filename = _SAFE_FILENAME_RE.sub("_", filename)

    # Remove leading dots (prevent hidden files)
    filename = filename.lstrip(".")

    # Truncate
    if len(filename) > max_length:
        filename = filename[:max_length]

    return filename


def validate_session_id(session_id: str) -> bool:
    """
    Validate that a session ID is a valid UUID format.
    Returns True if valid, False otherwise.
    """
    if not session_id:
        return False
    try:
        uuid.UUID(session_id, version=4)
        return True
    except (ValueError, AttributeError):
        return False


def validate_license_number(license_number: str) -> str:
    """
    Validate a license number:
    - Must be alphanumeric + hyphens
    - Must be 5-50 characters
    Returns the cleaned license number.
    Raises ValueError if invalid.
    """
    if not license_number:
        raise ValueError("License number is required")

    license_number = license_number.strip()

    if not _LICENSE_RE.match(license_number):
        raise ValueError("License number must be 5-50 characters and contain only letters, numbers, and hyphens")

    return license_number
