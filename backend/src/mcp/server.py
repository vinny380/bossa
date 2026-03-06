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
    pattern: str, path: str = "/", workspace_id: str = Depends(get_workspace_id)
) -> str:
    """Search file contents for a pattern."""
    return await fs.grep(workspace_id, pattern, path)


@mcp.tool()
async def glob_search(
    pattern: str, workspace_id: str = Depends(get_workspace_id)
) -> str:
    """Find files matching a glob pattern."""
    return await fs.glob_search(workspace_id, pattern)


@mcp.tool()
async def delete_file(path: str, workspace_id: str = Depends(get_workspace_id)) -> str:
    """Delete a file."""
    return await fs.delete_file(workspace_id, path)
