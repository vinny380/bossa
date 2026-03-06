"""Tests for auth module."""

import pytest
from src.auth import resolve_workspace_id


@pytest.mark.asyncio
async def test_resolve_workspace_id_with_default_key(
    default_workspace_id: str,
) -> None:
    """sk-default resolves to default workspace when allow_default_key is True."""
    result = await resolve_workspace_id("sk-default")
    assert result == default_workspace_id


@pytest.mark.asyncio
async def test_resolve_workspace_id_sk_default_blocked_in_prod(monkeypatch) -> None:
    """sk-default is rejected when allow_default_key is False (production)."""
    from src import config

    monkeypatch.setattr(config.settings, "allow_default_key", False)
    with pytest.raises(ValueError, match="Invalid API key"):
        await resolve_workspace_id("sk-default")


@pytest.mark.asyncio
async def test_resolve_workspace_id_with_empty_key_raises(monkeypatch) -> None:
    """Missing or empty key raises ValueError when API key is required."""
    from src import config

    monkeypatch.setattr(config.settings, "require_api_key", True)
    with pytest.raises(ValueError, match="API key required"):
        await resolve_workspace_id("")
    with pytest.raises(ValueError, match="API key required"):
        await resolve_workspace_id(None)


@pytest.mark.asyncio
async def test_resolve_workspace_id_with_empty_key_fallback_when_not_required(
    monkeypatch, default_workspace_id: str
) -> None:
    """Empty key falls back to default workspace when require_api_key is False."""
    from src import config

    monkeypatch.setattr(config.settings, "require_api_key", False)
    assert await resolve_workspace_id("") == default_workspace_id
    assert await resolve_workspace_id(None) == default_workspace_id


@pytest.mark.asyncio
async def test_resolve_workspace_id_invalid_key_raises() -> None:
    """Invalid API key raises ValueError."""
    with pytest.raises(ValueError, match="Invalid API key"):
        await resolve_workspace_id("sk-invalid")
