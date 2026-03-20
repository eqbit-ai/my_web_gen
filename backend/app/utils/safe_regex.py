"""
Safe regex utilities — prevents ReDoS by limiting input size before regex processing.

All regex operations on untrusted or large input should use these wrappers
instead of raw `re.sub()` / `re.search()` / `re.findall()`.
"""

import re

# Maximum input size for regex operations (500KB — generous for any HTML page)
MAX_REGEX_INPUT = 512_000


def safe_sub(pattern: str, repl, string: str, count: int = 0, flags: int = 0, max_len: int = MAX_REGEX_INPUT) -> str:
    """re.sub with input length limit to prevent ReDoS."""
    if len(string) > max_len:
        string = string[:max_len]
    return re.sub(pattern, repl, string, count=count, flags=flags)


def safe_search(pattern: str, string: str, flags: int = 0, max_len: int = MAX_REGEX_INPUT):
    """re.search with input length limit to prevent ReDoS."""
    if len(string) > max_len:
        string = string[:max_len]
    return re.search(pattern, string, flags=flags)


def safe_findall(pattern: str, string: str, flags: int = 0, max_len: int = MAX_REGEX_INPUT) -> list:
    """re.findall with input length limit to prevent ReDoS."""
    if len(string) > max_len:
        string = string[:max_len]
    return re.findall(pattern, string, flags=flags)


def safe_finditer(pattern: str, string: str, flags: int = 0, max_len: int = MAX_REGEX_INPUT):
    """re.finditer with input length limit to prevent ReDoS."""
    if len(string) > max_len:
        string = string[:max_len]
    return re.finditer(pattern, string, flags=flags)
