from fastmcp import FastMCP

from src.config import settings
from src.engine import filesystem as fs

mcp = FastMCP("Bossa")


@mcp.tool()
async def ls(path: str = "/") -> str:
    """List files and directories at the given path."""
    return await fs.ls(settings.default_workspace_id, path)


@mcp.tool()
async def read_file(path: str) -> str:
    """Read the contents of a file."""
    return await fs.read_file(settings.default_workspace_id, path)


@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """Create or overwrite a file."""
    return await fs.write_file(settings.default_workspace_id, path, content)


@mcp.tool()
async def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Replace a string in a file."""
    return await fs.edit_file(
        settings.default_workspace_id, path, old_string, new_string
    )


@mcp.tool()
async def grep(pattern: str, path: str = "/") -> str:
    """Search file contents for a pattern."""
    return await fs.grep(settings.default_workspace_id, pattern, path)


@mcp.tool()
async def glob_search(pattern: str, path: str = "/") -> str:
    """Find files matching a glob pattern."""
    return await fs.glob_search(settings.default_workspace_id, pattern)


@mcp.tool()
async def delete_file(path: str) -> str:
    """Delete a file."""
    return await fs.delete_file(settings.default_workspace_id, path)
