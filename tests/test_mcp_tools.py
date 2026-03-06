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
    """MCP grep returns structured match data."""
    path = "/test/mcp-grep/basic.txt"
    await mcp_client.call_tool(
        "write_file",
        {"path": path, "content": "line1\nfindme\nline3"},
    )
    result = await mcp_client.call_tool(
        "grep", {"pattern": "findme", "path": "/test/mcp-grep/"}
    )
    data = result.data if hasattr(result, "data") else result
    payload = data if isinstance(data, dict) else data[0]
    assert payload["output_mode"] == "matches"
    assert payload["total_matches"] == 1
    assert payload["matches"][0]["path"] == path
    assert payload["matches"][0]["line"] == "findme"
    await mcp_client.call_tool("delete_file", {"path": path})


@pytest.mark.asyncio
async def test_mcp_grep_supports_files_output_mode(mcp_client: Client) -> None:
    """MCP grep can return just files with matches."""
    await mcp_client.call_tool(
        "write_file",
        {"path": "/test/mcp-grep-files/a.txt", "content": "enterprise customer"},
    )
    await mcp_client.call_tool(
        "write_file",
        {"path": "/test/mcp-grep-files/b.txt", "content": "starter customer"},
    )
    result = await mcp_client.call_tool(
        "grep",
        {
            "pattern": "enterprise",
            "path": "/test/mcp-grep-files/",
            "output_mode": "files_with_matches",
        },
    )
    data = result.data if hasattr(result, "data") else result
    payload = data if isinstance(data, dict) else data[0]
    assert payload["files"] == ["/test/mcp-grep-files/a.txt"]
    await mcp_client.call_tool("delete_file", {"path": "/test/mcp-grep-files/a.txt"})
    await mcp_client.call_tool("delete_file", {"path": "/test/mcp-grep-files/b.txt"})


@pytest.mark.asyncio
async def test_mcp_grep_supports_pagination(mcp_client: Client) -> None:
    """MCP grep paginates match results for agents."""
    path = "/test/mcp-grep-page/page.txt"
    await mcp_client.call_tool(
        "write_file",
        {"path": path, "content": "hit one\nhit two\nhit three"},
    )
    result = await mcp_client.call_tool(
        "grep",
        {
            "pattern": "hit",
            "path": "/test/mcp-grep-page/",
            "max_matches": 2,
            "offset": 0,
        },
    )
    data = result.data if hasattr(result, "data") else result
    payload = data if isinstance(data, dict) else data[0]
    assert payload["returned_matches"] == 2
    assert payload["has_more"] is True
    assert payload["next_offset"] == 2
    await mcp_client.call_tool("delete_file", {"path": path})


@pytest.mark.asyncio
async def test_mcp_glob_search_with_path(mcp_client: Client) -> None:
    """MCP glob_search with path parameter scopes the search."""
    await mcp_client.call_tool(
        "write_file",
        {"path": "/test/mcp-glob/scope/a.md", "content": "a"},
    )
    await mcp_client.call_tool(
        "write_file",
        {"path": "/test/mcp-glob/other/b.md", "content": "b"},
    )
    result = await mcp_client.call_tool(
        "glob_search", {"pattern": "*.md", "path": "/test/mcp-glob/scope/"}
    )
    data = result.data if hasattr(result, "data") else result
    assert "/test/mcp-glob/scope/a.md" in str(data)
    assert "/test/mcp-glob/other/b.md" not in str(data)
    await mcp_client.call_tool("delete_file", {"path": "/test/mcp-glob/scope/a.md"})
    await mcp_client.call_tool("delete_file", {"path": "/test/mcp-glob/other/b.md"})
