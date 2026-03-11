"""Tests for workspace API (JWT-protected)."""

import pytest
from httpx import ASGITransport, AsyncClient
from src.dependencies import get_current_user_id
from src.main import app

TEST_USER_ID = "00000000-0000-0000-0000-000000000002"


@pytest.mark.asyncio
async def test_create_workspace_returns_402_when_free_tier_has_one(
    workspace_with_user, monkeypatch
) -> None:
    """create_workspace returns 402 when free tier user already has 1 workspace."""

    # workspace_with_user creates 1 workspace for TEST_USER_ID
    async def override_get_current_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer fake-jwt-for-test"},
        ) as client:
            response = await client.post(
                "/api/v1/workspaces",
                json={"name": "second-workspace"},
            )
        assert response.status_code == 402
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_owner_can_create_multiple_workspaces(
    workspace_with_user, monkeypatch
) -> None:
    """Owner (config or tier) can create multiple workspaces."""
    from src.db import execute

    async def override_get_current_user_id():
        return TEST_USER_ID

    from src.config import settings

    monkeypatch.setattr(settings, "owner_user_ids", TEST_USER_ID)
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer fake-jwt-for-test"},
        ) as client:
            response = await client.post(
                "/api/v1/workspaces",
                json={"name": "owner-second-workspace"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "owner-second-workspace"
        created_id = data["id"]
        await execute("DELETE FROM workspaces WHERE id = $1", created_id)
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
