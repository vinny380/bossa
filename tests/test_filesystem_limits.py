"""Tests for filesystem limit enforcement in write_file, etc."""

import pytest
from src.db import execute, fetch_one
from src.engine.filesystem import delete_file, write_file
from src.usage import LimitError

DEFAULT_WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_write_file_raises_limit_error_when_over_storage(
    workspace_with_user, monkeypatch
) -> None:
    """write_file raises LimitError when account exceeds storage limit."""
    workspace_id, user_id = workspace_with_user

    async def _mock_usage(account_id: str) -> dict:
        return {
            "storage_bytes": 99 * 1024 * 1024,  # 99 MB
            "storage_mb": 99,
            "files_count": 0,
            "requests_today": 0,
        }

    monkeypatch.setattr("src.usage.get_usage", _mock_usage)
    # Adding 2 MB would put us at 101 MB - over 100 MB free limit
    content_2mb = "x" * (2 * 1024 * 1024)
    with pytest.raises(LimitError):
        await write_file(workspace_id, "/limit-test/big.txt", content_2mb)


@pytest.mark.asyncio
async def test_write_file_raises_limit_error_when_over_file_limit(
    workspace_with_user,
) -> None:
    """write_file raises LimitError when account exceeds file limit."""
    workspace_id, user_id = workspace_with_user
    # Create 500 files (at limit)
    folder_row = await fetch_one(
        "SELECT id FROM folders WHERE workspace_id = $1 AND path = '/' LIMIT 1",
        workspace_id,
    )
    assert folder_row
    for i in range(500):
        await execute(
            """
            INSERT INTO files (workspace_id, folder_id, path, name, content)
            VALUES ($1, $2, $3, $4, 'x')
            ON CONFLICT (workspace_id, path) DO NOTHING
            """,
            workspace_id,
            folder_row["id"],
            f"/file-limit/f{i}.txt",
            f"f{i}.txt",
        )
    try:
        with pytest.raises(LimitError):
            await write_file(workspace_id, "/file-limit/new.txt", "content")
    finally:
        await execute(
            "DELETE FROM files WHERE workspace_id = $1 AND path LIKE '/file-limit/%'",
            workspace_id,
        )


@pytest.mark.asyncio
async def test_write_file_succeeds_when_under_limits(workspace_with_user) -> None:
    """write_file succeeds when under limits (workspace with user_id)."""
    workspace_id, _ = workspace_with_user
    result = await write_file(workspace_id, "/under-limit/ok.txt", "hello")
    assert "Wrote" in result or "ok.txt" in result
    await delete_file(workspace_id, "/under-limit/ok.txt")


@pytest.mark.asyncio
async def test_overwrite_checks_storage_delta_only(workspace_with_user) -> None:
    """Overwrite does not increase file count, only checks storage delta."""
    workspace_id, _ = workspace_with_user
    await write_file(workspace_id, "/overwrite/test.txt", "short")
    # Overwrite with larger content - should check storage delta only
    result = await write_file(workspace_id, "/overwrite/test.txt", "longer content now")
    assert "Wrote" in result or "Edited" in result or "test.txt" in result
    await delete_file(workspace_id, "/overwrite/test.txt")


@pytest.mark.asyncio
async def test_delete_file_does_not_raise(workspace_with_user) -> None:
    """delete_file does not raise (reduces usage)."""
    workspace_id, _ = workspace_with_user
    await write_file(workspace_id, "/delete-me.txt", "content")
    result = await delete_file(workspace_id, "/delete-me.txt")
    assert "Deleted" in result


@pytest.mark.asyncio
async def test_workspace_without_user_id_skips_limits() -> None:
    """Workspace without user_id (default workspace) skips limits."""
    # Default workspace has no user_id - should not enforce limits
    result = await write_file(DEFAULT_WORKSPACE_ID, "/test/skip-limits.txt", "content")
    assert "Wrote" in result or "Error" not in result
    await delete_file(DEFAULT_WORKSPACE_ID, "/test/skip-limits.txt")
