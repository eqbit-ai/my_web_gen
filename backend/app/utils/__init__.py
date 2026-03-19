def sanitize_log(value) -> str:
    """Sanitize user input for safe logging (prevents log injection S5145)."""
    if not isinstance(value, str):
        value = str(value)
    return value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
