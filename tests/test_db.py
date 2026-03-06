import pytest
from src.db import fetch_one, fetch_all, execute


@pytest.mark.asyncio
async def test_fetch_one_returns_row(default_workspace_id: str) -> None:
    """fetch_one returns a row from a simple query."""
    row = await fetch_one(
        "SELECT id, name FROM workspaces WHERE id = $1",
        default_workspace_id,
    )
    assert row is not None
    assert str(row["id"]) == default_workspace_id
    assert row["name"] == "default"


@pytest.mark.asyncio
async def test_fetch_all_returns_rows(default_workspace_id: str) -> None:
    """fetch_all returns multiple rows."""
    rows = await fetch_all("SELECT id, name FROM workspaces ORDER BY name")
    assert len(rows) >= 1
    assert any(r["name"] == "default" for r in rows)


@pytest.mark.asyncio
async def test_execute_runs_insert(default_workspace_id: str) -> None:
    """execute runs an INSERT and returns."""
    await execute(
        """
        INSERT INTO files (workspace_id, path, content)
        VALUES ($1, $2, $3)
        ON CONFLICT (workspace_id, path) DO UPDATE SET content = EXCLUDED.content
        """,
        default_workspace_id,
        "/test/execute-check.txt",
        "test content",
    )
    row = await fetch_one(
        "SELECT content FROM files WHERE workspace_id = $1 AND path = $2",
        default_workspace_id,
        "/test/execute-check.txt",
    )
    assert row is not None
    assert row["content"] == "test content"
