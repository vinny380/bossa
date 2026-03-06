"""Tests for auth module."""

import pytest
from src.auth import resolve_workspace_id


@pytest.mark.asyncio
async def test_resolve_workspace_id_with_default_key(
    default_workspace_id: str,
) -> None:
    """sk-default resolves to default workspace."""
    result = await resolve_workspace_id("sk-default")
    assert result == default_workspace_id


@pytest.mark.asyncio
async def test_resolve_workspace_id_with_empty_key(
    default_workspace_id: str,
) -> None:
    """Empty key falls back to default workspace."""
    assert await resolve_workspace_id("") == default_workspace_id
    assert await resolve_workspace_id(None) == default_workspace_id


@pytest.mark.asyncio
async def test_resolve_workspace_id_invalid_key_raises() -> None:
    """Invalid API key raises ValueError."""
    with pytest.raises(ValueError, match="Invalid API key"):
        await resolve_workspace_id("sk-invalid")
