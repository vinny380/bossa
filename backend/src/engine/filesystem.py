from src.db import fetch_one, fetch_all, execute
from src.engine.path_utils import glob_to_sql_like, normalize_path


async def ls(workspace_id: str, path: str = "/") -> str:
    """List files and directories at the given path."""
    path = normalize_path(path)
    if not path.endswith("/"):
        path = path + "/"

    rows = await fetch_all(
        """
        SELECT path FROM files
        WHERE workspace_id = $1 AND path LIKE $2
        """,
        workspace_id,
        path + "%",
    )

    if not rows:
        return ""

    seen: set[str] = set()
    entries: list[str] = []
    for row in rows:
        rest = row["path"][len(path) :]
        if not rest:
            continue
        parts = rest.split("/")
        name = parts[0]
        if name in seen:
            continue
        seen.add(name)
        if len(parts) > 1:
            entries.append(name + "/")
        else:
            entries.append(name)

    return "\n".join(sorted(entries)) if entries else ""


async def read_file(workspace_id: str, path: str) -> str:
    """Read the contents of a file. Returns content with line numbers (LangChain convention)."""
    path = normalize_path(path)
    row = await fetch_one(
        "SELECT content FROM files WHERE workspace_id = $1 AND path = $2",
        workspace_id,
        path,
    )
    if not row:
        return f"Error: File not found: {path}"
    content = row["content"]
    lines = content.split("\n")
    return "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))


async def write_file(workspace_id: str, path: str, content: str) -> str:
    """Create or overwrite a file."""
    path = normalize_path(path)
    await execute(
        """
        INSERT INTO files (workspace_id, path, content)
        VALUES ($1, $2, $3)
        ON CONFLICT (workspace_id, path) DO UPDATE SET
            content = EXCLUDED.content,
            updated_at = NOW()
        """,
        workspace_id,
        path,
        content,
    )
    return f"Wrote {path}"


async def edit_file(
    workspace_id: str, path: str, old_string: str, new_string: str
) -> str:
    """Replace old_string with new_string in a file."""
    path = normalize_path(path)
    row = await fetch_one(
        "SELECT content FROM files WHERE workspace_id = $1 AND path = $2",
        workspace_id,
        path,
    )
    if not row:
        return f"Error: File not found: {path}"
    content = row["content"]
    if old_string not in content:
        return f"Error: old_string not found in {path}"
    new_content = content.replace(old_string, new_string, 1)
    await write_file(workspace_id, path, new_content)
    return f"Edited {path}"


async def grep(workspace_id: str, pattern: str, path_glob: str = "/") -> str:
    """Search file contents for a pattern."""
    path_glob = normalize_path(path_glob)
    if path_glob.endswith("/"):
        like_pattern = path_glob + "%"
    elif "*" in path_glob or "?" in path_glob:
        like_pattern = glob_to_sql_like(path_glob)
    else:
        like_pattern = path_glob + "%"

    rows = await fetch_all(
        """
        SELECT path, content FROM files
        WHERE workspace_id = $1 AND path LIKE $2 AND content ILIKE $3
        """,
        workspace_id,
        like_pattern,
        f"%{pattern}%",
    )

    results: list[str] = []
    for row in rows:
        path = row["path"]
        content = row["content"]
        for i, line in enumerate(content.split("\n")):
            if pattern.lower() in line.lower():
                results.append(f"{path}:{i + 1}:{line}")
    return "\n".join(results) if results else ""


async def glob_search(workspace_id: str, pattern: str, base_path: str = "/") -> str:
    """Find files matching a glob pattern."""
    pattern = normalize_path(pattern)
    like_pattern = glob_to_sql_like(pattern)

    rows = await fetch_all(
        """
        SELECT path FROM files
        WHERE workspace_id = $1 AND path LIKE $2
        ORDER BY path
        """,
        workspace_id,
        like_pattern,
    )
    return "\n".join(r["path"] for r in rows)


async def delete_file(workspace_id: str, path: str) -> str:
    """Delete a file."""
    path = normalize_path(path)
    await execute(
        "DELETE FROM files WHERE workspace_id = $1 AND path = $2",
        workspace_id,
        path,
    )
    return f"Deleted {path}"
