from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.server.dependencies import get_http_headers

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


@mcp.tool()
async def ls(path: str = "/", workspace_id: str = Depends(get_workspace_id)) -> str:
    """List files and directories at the given path."""
    return await fs.ls(workspace_id, path)


@mcp.tool()
async def read_file(path: str, workspace_id: str = Depends(get_workspace_id)) -> str:
    """Read the contents of a file."""
    return await fs.read_file(workspace_id, path)


@mcp.tool()
async def write_file(
    path: str, content: str, workspace_id: str = Depends(get_workspace_id)
) -> str:
    """Create or overwrite a file."""
    return await fs.write_file(workspace_id, path, content)


@mcp.tool()
async def edit_file(
    path: str,
    old_string: str,
    new_string: str,
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Replace a string in a file."""
    return await fs.edit_file(workspace_id, path, old_string, new_string)


@mcp.tool()
async def grep(
    pattern: str | None = None,
    path: str = "/",
    regex: bool = False,
    case_sensitive: bool = False,
    whole_word: bool = False,
    max_matches: int = 100,
    offset: int = 0,
    output_mode: str = "matches",
    all_of: list[str] | None = None,
    any_of: list[str] | None = None,
    none_of: list[str] | None = None,
    context_before: int = 0,
    context_after: int = 0,
    workspace_id: str = Depends(get_workspace_id),
) -> dict:
    """Search file contents without reading whole files. Use this to find text by path, literal or regex pattern, inclusion/exclusion criteria, counts, filenames only, or paginated matches. Prefer `output_mode="files_with_matches"` to discover candidate files first, then use `read_file` only on files you need to inspect closely."""
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


@mcp.tool()
async def glob_search(
    pattern: str,
    path: str = "/",
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Find files matching a glob pattern. path scopes the search to that directory."""
    return await fs.glob_search(workspace_id, pattern, path)


@mcp.tool()
async def delete_file(path: str, workspace_id: str = Depends(get_workspace_id)) -> str:
    """Delete a file."""
    return await fs.delete_file(workspace_id, path)
