"""Resolve API key to workspace_id."""

import hashlib

from src.config import settings
from src.db import fetch_one


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def resolve_workspace_id(api_key: str | None) -> str:
    """Resolve API key to workspace_id. Falls back to default if no key provided."""
    if not api_key or not api_key.strip():
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
        return str(row["workspace_id"])
    raise ValueError("Invalid API key")
