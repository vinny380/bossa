"""Resolve API key to workspace_id."""

import hashlib

from src.config import settings
from src.db import fetch_one


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def resolve_workspace_id(api_key: str | None) -> str:
    """Resolve API key to workspace_id. Requires a valid API key unless require_api_key is False."""
    if not api_key or not api_key.strip():
        if settings.require_api_key:
            raise ValueError("API key required")
        return settings.default_workspace_id

    key_hash = _hash_key(api_key.strip())
    row = await fetch_one(
        """
        SELECT workspace_id FROM workspace_api_keys
        WHERE key_hash = $1
        """,
        key_hash,
    )
    if row:
        if key_hash == _hash_key("sk-default") and not settings.allow_default_key:
            raise ValueError("Invalid API key")
        return str(row["workspace_id"])
    raise ValueError("Invalid API key")
