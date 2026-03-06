import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_post_files_creates_file(api_client: AsyncClient) -> None:
    """POST /api/v1/files creates a file."""
    response = await api_client.post(
        "/api/v1/files",
        json={"path": "/test/api-create.txt", "content": "API test content"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data or "content" in data or data.get("path") == "/test/api-create.txt"


@pytest.mark.asyncio
async def test_get_files_reads_file(api_client: AsyncClient) -> None:
    """GET /api/v1/files?path=... reads a file."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/api-read.txt", "content": "read me"},
    )
    response = await api_client.get("/api/v1/files", params={"path": "/test/api-read.txt"})
    assert response.status_code == 200
    data = response.json()
    assert "read me" in str(data.get("content", data))


@pytest.mark.asyncio
async def test_get_files_list_returns_directory(api_client: AsyncClient) -> None:
    """GET /api/v1/files/list?path=... lists directory."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/list-dir/file.txt", "content": "x"},
    )
    response = await api_client.get(
        "/api/v1/files/list", params={"path": "/test/list-dir/"}
    )
    assert response.status_code == 200
    data = response.json()
    items = data if isinstance(data, list) else data.get("items", data.get("files", []))
    assert any("file.txt" in str(i) for i in items)


@pytest.mark.asyncio
async def test_post_files_search_grep(api_client: AsyncClient) -> None:
    """POST /api/v1/files/search greps for pattern."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/search.txt", "content": "needle in haystack"},
    )
    response = await api_client.post(
        "/api/v1/files/search",
        json={"pattern": "needle", "path": "/test/"},
    )
    assert response.status_code == 200
    data = response.json()
    content = str(data.get("results", data.get("content", data)))
    assert "needle" in content


@pytest.mark.asyncio
async def test_delete_files_removes_file(api_client: AsyncClient) -> None:
    """DELETE /api/v1/files?path=... removes a file."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/api-delete.txt", "content": "delete me"},
    )
    response = await api_client.delete(
        "/api/v1/files", params={"path": "/test/api-delete.txt"}
    )
    assert response.status_code in (200, 204)
    get_response = await api_client.get(
        "/api/v1/files", params={"path": "/test/api-delete.txt"}
    )
    assert get_response.status_code == 404 or "not found" in get_response.text.lower()
