"""End-to-end: write via REST, read via MCP, grep across both."""
import pytest
from fastmcp import Client
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.mcp.server import mcp


@pytest.mark.asyncio
async def test_write_via_rest_read_via_mcp() -> None:
    """Write a file via REST API, read it back via MCP."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        await http_client.post(
            "/api/v1/files",
            json={"path": "/integration/shared.txt", "content": "shared content"},
        )

    async with Client(mcp) as mcp_client:
        result = await mcp_client.call_tool(
            "read_file", {"path": "/integration/shared.txt"}
        )
        data = result.data if hasattr(result, "data") else result
        assert "shared content" in str(data)

    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        await http_client.delete("/api/v1/files", params={"path": "/integration/shared.txt"})


@pytest.mark.asyncio
async def test_write_via_mcp_grep_via_rest() -> None:
    """Write via MCP, grep via REST."""
    async with Client(mcp) as mcp_client:
        await mcp_client.call_tool(
            "write_file",
            {"path": "/integration/grep-test.txt", "content": "find this pattern"},
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.post(
            "/api/v1/files/search",
            json={"pattern": "find this", "path": "/integration/"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_matches"] == 1
        assert "find this pattern" in data["matches"][0]["line"]

    async with Client(mcp) as mcp_client:
        await mcp_client.call_tool(
            "delete_file", {"path": "/integration/grep-test.txt"}
        )
