"""Tests for usage/limits service. Requires migration 005."""

import pytest
from src.db import execute, fetch_one
from src.usage import (LimitError, check_limits, get_account_id, get_tier,
                       get_usage, increment_requests)

DEFAULT_WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_get_account_id_returns_user_id_for_workspace_with_user(
    workspace_with_user,
) -> None:
    """get_account_id returns user_id for workspace with user_id."""
    workspace_id, user_id = workspace_with_user
    result = await get_account_id(workspace_id)
    assert result == user_id


@pytest.mark.asyncio
async def test_get_account_id_returns_none_for_workspace_without_user() -> None:
    """get_account_id returns None for workspace without user_id (default workspace)."""
    result = await get_account_id(DEFAULT_WORKSPACE_ID)
    assert result is None


@pytest.mark.asyncio
async def test_get_tier_returns_free_for_new_user(workspace_with_user) -> None:
    """get_tier returns 'free' for new user (lazy-creates)."""
    _, user_id = workspace_with_user
    result = await get_tier(user_id)
    assert result == "free"


@pytest.mark.asyncio
async def test_get_tier_returns_pro_when_set(workspace_with_user) -> None:
    """get_tier returns 'pro' when set."""
    _, user_id = workspace_with_user
    await execute(
        """
        INSERT INTO account_tiers (user_id, tier) VALUES ($1, 'pro')
        ON CONFLICT (user_id) DO UPDATE SET tier = 'pro'
        """,
        user_id,
    )
    result = await get_tier(user_id)
    assert result == "pro"


@pytest.mark.asyncio
async def test_get_tier_returns_owner_when_in_config(
    workspace_with_user, monkeypatch
) -> None:
    """get_tier returns 'owner' when account_id is in OWNER_USER_IDS."""
    _, user_id = workspace_with_user
    from src.config import settings

    monkeypatch.setattr(settings, "owner_user_ids", user_id)
    result = await get_tier(user_id)
    assert result == "owner"


@pytest.mark.asyncio
async def test_check_limits_skips_when_tier_owner(
    workspace_with_user, monkeypatch
) -> None:
    """check_limits passes when tier is 'owner' (DB or config), even over limits."""
    _, user_id = workspace_with_user
    # Set user over request limit
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date()
    await execute(
        """
        INSERT INTO usage_daily (user_id, date, requests) VALUES ($1, $2, 2000)
        ON CONFLICT (user_id, date) DO UPDATE SET requests = 2000
        """,
        user_id,
        today,
    )

    # Mock get_tier to return 'owner' (simulates DB tier='owner')
    async def _mock_tier(account_id: str) -> str:
        return "owner"

    monkeypatch.setattr("src.usage.get_tier", _mock_tier)
    # Should not raise even though over request limit
    await check_limits(user_id, "request")


@pytest.mark.asyncio
async def test_get_usage_returns_storage_files_requests(workspace_with_user) -> None:
    """get_usage returns storage_bytes, files_count, requests_today."""
    workspace_id, user_id = workspace_with_user
    usage = await get_usage(user_id)
    assert "storage_bytes" in usage
    assert "files_count" in usage
    assert "requests_today" in usage
    assert usage["storage_bytes"] >= 0
    assert usage["files_count"] >= 0
    assert usage["requests_today"] >= 0


@pytest.mark.asyncio
async def test_check_limits_raises_when_over_storage_limit(
    workspace_with_user, monkeypatch
) -> None:
    """check_limits raises LimitError when over storage limit."""
    _, user_id = workspace_with_user

    # Free tier = 100 MB. Patch get_usage to return 101 MB so we don't need to insert 101 MB.
    async def _mock_usage(account_id: str) -> dict:
        return {
            "storage_bytes": 101 * 1024 * 1024,  # 101 MB
            "storage_mb": 101,
            "files_count": 0,
            "requests_today": 0,
        }

    monkeypatch.setattr("src.usage.get_usage", _mock_usage)
    with pytest.raises(LimitError) as exc_info:
        await check_limits(user_id, "write", delta_storage=0, delta_files=0)
    assert (
        "storage" in str(exc_info.value).lower()
        or "limit" in str(exc_info.value).lower()
    )


@pytest.mark.asyncio
async def test_check_limits_raises_when_over_file_limit(workspace_with_user) -> None:
    """check_limits raises LimitError when over file limit."""
    _, user_id = workspace_with_user
    # Free tier = 500 files. Create 501 files.
    workspace_id = workspace_with_user[0]
    folder_row = await fetch_one(
        "SELECT id FROM folders WHERE workspace_id = $1 AND path = '/' LIMIT 1",
        workspace_id,
    )
    assert folder_row
    folder_id = folder_row["id"]
    for i in range(501):
        await execute(
            """
            INSERT INTO files (workspace_id, folder_id, path, name, content)
            VALUES ($1, $2, $3, $4, 'x')
            ON CONFLICT (workspace_id, path) DO NOTHING
            """,
            workspace_id,
            folder_id,
            f"/limit-test/file{i}.txt",
            f"file{i}.txt",
        )
    try:
        with pytest.raises(LimitError) as exc_info:
            await check_limits(user_id, "write", delta_storage=0, delta_files=1)
        assert (
            "file" in str(exc_info.value).lower()
            or "limit" in str(exc_info.value).lower()
        )
    finally:
        await execute(
            "DELETE FROM files WHERE workspace_id = $1 AND path LIKE '/limit-test/%'",
            workspace_id,
        )


@pytest.mark.asyncio
async def test_check_limits_raises_when_over_request_limit(workspace_with_user) -> None:
    """check_limits raises LimitError when over request limit."""
    _, user_id = workspace_with_user
    # Free tier = 1000 requests/day. Set usage_daily to 1000.
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date()
    await execute(
        """
        INSERT INTO usage_daily (user_id, date, requests) VALUES ($1, $2, 1000)
        ON CONFLICT (user_id, date) DO UPDATE SET requests = 1000
        """,
        user_id,
        today,
    )
    with pytest.raises(LimitError) as exc_info:
        await check_limits(user_id, "request")
    assert (
        "request" in str(exc_info.value).lower()
        or "limit" in str(exc_info.value).lower()
    )


@pytest.mark.asyncio
async def test_check_limits_passes_when_under_limits(workspace_with_user) -> None:
    """check_limits passes when under limits."""
    _, user_id = workspace_with_user
    await check_limits(user_id, "write", delta_storage=100, delta_files=1)
    await check_limits(user_id, "request")


@pytest.mark.asyncio
async def test_check_limits_passes_for_owner(workspace_with_user, monkeypatch) -> None:
    """check_limits passes (no raise) when account_id is in OWNER_USER_IDS."""
    _, user_id = workspace_with_user
    # Set user over limits
    await execute(
        """
        INSERT INTO usage_daily (user_id, date, requests) VALUES ($1, (NOW() AT TIME ZONE 'UTC')::DATE, 2000)
        ON CONFLICT (user_id, date) DO UPDATE SET requests = 2000
        """,
        user_id,
    )
    # Patch owner_user_ids so owner_user_ids_list includes our test user
    from src.config import settings

    monkeypatch.setattr(settings, "owner_user_ids", user_id)
    # Should not raise even though over request limit
    await check_limits(user_id, "request")


@pytest.mark.asyncio
async def test_increment_requests_upserts_usage_daily(workspace_with_user) -> None:
    """increment_requests upserts usage_daily."""
    _, user_id = workspace_with_user
    await increment_requests(user_id)
    usage = await get_usage(user_id)
    assert usage["requests_today"] >= 1
    await increment_requests(user_id)
    usage2 = await get_usage(user_id)
    assert usage2["requests_today"] >= 2
