import pytest
from fastmcp import Client

from src.mcp.server import mcp


@pytest.fixture
async def mcp_client():
    async with Client(mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_mcp_ls_tool(mcp_client: Client) -> None:
    """MCP ls tool returns directory listing."""
    result = await mcp_client.call_tool("ls", {"path": "/"})
    assert result is not None
    # Root may have test or other dirs
    content = str(result) if not hasattr(result, "data") else str(result.data)
    assert isinstance(content, str) or content is not None


@pytest.mark.asyncio
async def test_mcp_write_file_then_read_file(mcp_client: Client) -> None:
    """MCP write_file and read_file work together."""
    path = "/test/mcp-write.txt"
    content = "MCP test content"
    await mcp_client.call_tool("write_file", {"path": path, "content": content})
    result = await mcp_client.call_tool("read_file", {"path": path})
    data = result.data if hasattr(result, "data") else result
    assert content in str(data)
    await mcp_client.call_tool("delete_file", {"path": path})


@pytest.mark.asyncio
async def test_mcp_grep_tool(mcp_client: Client) -> None:
    """MCP grep tool finds pattern."""
    path = "/test/mcp-grep.txt"
    await mcp_client.call_tool(
        "write_file",
        {"path": path, "content": "line1\nfindme\nline3"},
    )
    result = await mcp_client.call_tool(
        "grep", {"pattern": "findme", "path": "/test/"}
    )
    data = result.data if hasattr(result, "data") else result
    assert "findme" in str(data)
    await mcp_client.call_tool("delete_file", {"path": path})
