from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.server.dependencies import get_http_headers
from pydantic import Field

from src.auth import resolve_workspace_id
from src.engine import filesystem as fs

mcp = FastMCP("Bossa")


async def get_workspace_id() -> str:
    """Resolve workspace from API key in request headers."""
    headers = get_http_headers(include={"authorization", "x-api-key"})
    api_key = headers.get("x-api-key")
    if not api_key and headers.get("authorization", "").startswith("Bearer "):
        api_key = headers["authorization"][7:].strip()
    return await resolve_workspace_id(api_key)


@mcp.tool(annotations={
    "readOnlyHint": True,
    "idempotentHint": True,
    "openWorldHint": False,
})
async def ls(
    path: Annotated[str, Field(description="Absolute directory path to list. Defaults to root.")] = "/",
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """List immediate children (files and directories) at the given path. Returns one entry per line; directories end with `/`. Returns empty string if path has no children."""
    return await fs.ls(workspace_id, path)


@mcp.tool(annotations={
    "readOnlyHint": True,
    "idempotentHint": True,
    "openWorldHint": False,
})
async def read_file(
    path: Annotated[str, Field(description="Absolute path to the file to read.")],
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Return the full contents of a file with numbered lines (e.g. `1: line text`). Returns an error string if the file does not exist."""
    return await fs.read_file(workspace_id, path)


@mcp.tool(annotations={
    "idempotentHint": True,
    "openWorldHint": False,
})
async def write_file(
    path: Annotated[str, Field(description="Absolute path for the file to create or overwrite.")],
    content: Annotated[str, Field(description="Full file content to write.")],
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Create a new file or overwrite an existing file at the given path with the provided content."""
    return await fs.write_file(workspace_id, path, content)


@mcp.tool(annotations={
    "openWorldHint": False,
})
async def edit_file(
    path: Annotated[str, Field(description="Absolute path to the file to edit.")],
    old_string: Annotated[str, Field(description="Exact substring to find in the file (must match including whitespace).")],
    new_string: Annotated[str, Field(description="Replacement string. Use empty string to delete old_string.")],
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Replace the first occurrence of old_string with new_string in a file. old_string must match exactly. Fails if the file does not exist or old_string is not found."""
    return await fs.edit_file(workspace_id, path, old_string, new_string)


@mcp.tool(annotations={
    "readOnlyHint": True,
    "idempotentHint": True,
    "openWorldHint": False,
})
async def grep(
    pattern: Annotated[str | None, Field(description="Literal text or regex pattern to search for.")] = None,
    path: Annotated[str, Field(description="Directory or file path to scope the search.")] = "/",
    regex: Annotated[bool, Field(description="Treat pattern as a regular expression.")] = False,
    case_sensitive: Annotated[bool, Field(description="Enable case-sensitive matching.")] = False,
    whole_word: Annotated[bool, Field(description="Match whole words only.")] = False,
    max_matches: Annotated[int, Field(description="Maximum number of results to return.", ge=1)] = 100,
    offset: Annotated[int, Field(description="Number of results to skip for pagination.", ge=0)] = 0,
    output_mode: Annotated[
        Literal["matches", "files_with_matches", "count"],
        Field(description="'matches' returns matching lines with context, 'files_with_matches' returns only file paths, 'count' returns match count."),
    ] = "matches",
    all_of: Annotated[list[str] | None, Field(description="All terms must match on the same line (AND logic).")] = None,
    any_of: Annotated[list[str] | None, Field(description="At least one term must match on the line (OR logic).")] = None,
    none_of: Annotated[list[str] | None, Field(description="Exclude lines matching any of these terms.")] = None,
    context_before: Annotated[int, Field(description="Number of lines to include before each match.", ge=0)] = 0,
    context_after: Annotated[int, Field(description="Number of lines to include after each match.", ge=0)] = 0,
    workspace_id: str = Depends(get_workspace_id),
) -> dict:
    """Search file contents without reading whole files. Supports literal or regex patterns, boolean inclusion/exclusion (all_of, any_of, none_of), and three output modes. Prefer output_mode='files_with_matches' to discover candidate files first, then read_file to inspect closely."""
    result = await fs.grep(
        workspace_id,
        pattern=pattern,
        path=path,
        regex=regex,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        max_matches=max_matches,
        offset=offset,
        output_mode=output_mode,
        all_of=all_of,
        any_of=any_of,
        none_of=none_of,
        context_before=context_before,
        context_after=context_after,
    )
    return result.model_dump()


@mcp.tool(annotations={
    "readOnlyHint": True,
    "idempotentHint": True,
    "openWorldHint": False,
})
async def glob_search(
    pattern: Annotated[str, Field(description="Glob pattern to match file paths (e.g. '**/*.py', 'src/*.ts').")],
    path: Annotated[str, Field(description="Directory to scope the search to.")] = "/",
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Find files whose paths match a glob pattern. Returns matching absolute file paths, one per line."""
    return await fs.glob_search(workspace_id, pattern, path)


@mcp.tool(annotations={
    "destructiveHint": True,
    "idempotentHint": True,
    "openWorldHint": False,
})
async def delete_file(
    path: Annotated[str, Field(description="Absolute path to the file to delete.")],
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Permanently delete a file at the given path."""
    return await fs.delete_file(workspace_id, path)
