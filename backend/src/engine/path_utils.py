def escape_for_like(s: str) -> str:
    """Escape % and _ for use as literal in SQL LIKE pattern."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def glob_to_sql_like(pattern: str) -> str:
    """Convert glob pattern to SQL LIKE pattern. * -> %, ? -> _."""
    # Escape SQL LIKE special chars: % and _
    result = pattern.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    # Convert glob to LIKE
    result = result.replace("*", "%").replace("?", "_")
    return result


def normalize_path(path: str) -> str:
    """Ensure path starts with / and has consistent slashes."""
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    return path.replace("//", "/")
