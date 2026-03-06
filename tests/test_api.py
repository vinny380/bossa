import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-default"}
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=headers
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health_returns_ok(api_client: AsyncClient) -> None:
    """GET /health returns app health and DB status."""
    response = await api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"


@pytest.mark.asyncio
async def test_auth_config() -> None:
    """GET /auth/config returns config when configured, 404 otherwise."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/config")
    if response.status_code == 200:
        data = response.json()
        assert "supabase_url" in data
        assert "supabase_anon_key" in data
    else:
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_files_creates_file(api_client: AsyncClient) -> None:
    """POST /api/v1/files creates a file."""
    response = await api_client.post(
        "/api/v1/files",
        json={"path": "/test/api-create.txt", "content": "API test content"},
    )
    assert response.status_code == 200
    data = response.json()
    assert (
        "path" in data
        or "content" in data
        or data.get("path") == "/test/api-create.txt"
    )


@pytest.mark.asyncio
async def test_get_files_reads_file(api_client: AsyncClient) -> None:
    """GET /api/v1/files?path=... reads a file."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/api-read.txt", "content": "read me"},
    )
    response = await api_client.get(
        "/api/v1/files", params={"path": "/test/api-read.txt"}
    )
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
    """POST /api/v1/files/search returns structured grep results."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/search-basic/search.txt", "content": "needle in haystack"},
    )
    response = await api_client.post(
        "/api/v1/files/search",
        json={"pattern": "needle", "path": "/test/search-basic/"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["output_mode"] == "matches"
    assert data["total_matches"] == 1
    assert data["returned_matches"] == 1
    assert data["matches"][0]["path"] == "/test/search-basic/search.txt"
    assert "needle in haystack" in data["matches"][0]["line"]


@pytest.mark.asyncio
async def test_post_files_search_supports_regex_and_files_output(
    api_client: AsyncClient,
) -> None:
    """POST /api/v1/files/search supports regex and files-only mode."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/search-files/a.txt", "content": "ticket-001"},
    )
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/search-files/b.txt", "content": "ticket-abc"},
    )
    response = await api_client.post(
        "/api/v1/files/search",
        json={
            "pattern": r"ticket-\d+",
            "path": "/test/search-files/",
            "regex": True,
            "output_mode": "files_with_matches",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["output_mode"] == "files_with_matches"
    assert data["files"] == ["/test/search-files/a.txt"]


@pytest.mark.asyncio
async def test_post_files_search_supports_pagination_and_metadata(
    api_client: AsyncClient,
) -> None:
    """POST /api/v1/files/search paginates match results."""
    await api_client.post(
        "/api/v1/files",
        json={
            "path": "/test/search-page/search-page.txt",
            "content": "hit one\nhit two\nhit three",
        },
    )
    response = await api_client.post(
        "/api/v1/files/search",
        json={
            "pattern": "hit",
            "path": "/test/search-page/",
            "max_matches": 2,
            "offset": 0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 3
    assert data["returned_matches"] == 2
    assert data["has_more"] is True
    assert data["next_offset"] == 2


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


@pytest.mark.asyncio
async def test_missing_api_key_returns_401(monkeypatch) -> None:
    """Missing API key returns 401 when API key is required."""
    from src import config

    monkeypatch.setattr(config.settings, "require_api_key", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/files",
            params={"path": "/"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(api_client: AsyncClient) -> None:
    """Invalid API key returns 401."""
    response = await api_client.get(
        "/api/v1/files",
        params={"path": "/"},
        headers={"Authorization": "Bearer sk-invalid"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_post_files_bulk_creates_files(api_client: AsyncClient) -> None:
    """POST /api/v1/files/bulk creates multiple files."""
    response = await api_client.post(
        "/api/v1/files/bulk",
        json={
            "files": [
                {"path": "/test/bulk-api/a.txt", "content": "a"},
                {"path": "/test/bulk-api/b.txt", "content": "b"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "created" in data
    assert "updated" in data
    assert "failed" in data
    assert data["created"] + data["updated"] >= 2
    assert len(data["failed"]) == 0
    # Verify files exist
    for path in ["/test/bulk-api/a.txt", "/test/bulk-api/b.txt"]:
        r = await api_client.get("/api/v1/files", params={"path": path})
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_post_files_bulk_validation_empty_rejects(
    api_client: AsyncClient,
) -> None:
    """POST /api/v1/files/bulk rejects empty files array."""
    response = await api_client.post(
        "/api/v1/files/bulk",
        json={"files": []},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_post_files_bulk_auth_required(monkeypatch) -> None:
    """POST /api/v1/files/bulk requires API key when enforced."""
    from src import config

    monkeypatch.setattr(config.settings, "require_api_key", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/files/bulk",
            json={"files": [{"path": "/x.txt", "content": "x"}]},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_valid_api_key_works(api_client: AsyncClient) -> None:
    """Valid API key (sk-default) allows access."""
    response = await api_client.get(
        "/api/v1/files/list",
        params={"path": "/"},
        headers={"Authorization": "Bearer sk-default"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_files_glob_returns_paths(api_client: AsyncClient) -> None:
    """GET /api/v1/files/glob returns matching file paths."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/glob-dir/a.md", "content": "a"},
    )
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/glob-dir/b.md", "content": "b"},
    )
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/glob-dir/c.txt", "content": "c"},
    )
    response = await api_client.get(
        "/api/v1/files/glob",
        params={"pattern": "*.md", "path": "/test/glob-dir/"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    paths = data["paths"]
    assert "/test/glob-dir/a.md" in paths
    assert "/test/glob-dir/b.md" in paths
    assert "/test/glob-dir/c.txt" not in paths


@pytest.mark.asyncio
async def test_patch_files_edit_replaces_string(api_client: AsyncClient) -> None:
    """PATCH /api/v1/files edits file by replacing old_string with new_string."""
    await api_client.post(
        "/api/v1/files",
        json={"path": "/test/api-edit.txt", "content": "hello world"},
    )
    response = await api_client.patch(
        "/api/v1/files",
        json={
            "path": "/test/api-edit.txt",
            "old_string": "world",
            "new_string": "bossa",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("path") == "/test/api-edit.txt"
    assert data.get("edited") is True
    # Verify content changed
    get_resp = await api_client.get(
        "/api/v1/files", params={"path": "/test/api-edit.txt"}
    )
    assert get_resp.status_code == 200
    assert "hello bossa" in str(get_resp.json().get("content", ""))
