"""Resolve API key to workspace_id."""

import hashlib
import logging

import asyncpg
from src.config import settings
from src.db import fetch_one

logger = logging.getLogger(__name__)


def hash_key(key: str) -> str:
    """Hash API key for storage/lookup."""
    return hashlib.sha256(key.encode()).hexdigest()


async def resolve_workspace_id(api_key: str | None) -> str:
    """Resolve API key to workspace_id. Requires a valid API key unless require_api_key is False."""
    if not api_key or not api_key.strip():
        logger.info(
            "resolve_workspace_id: missing_api_key require_api_key=%s default_workspace_id=%s",
            settings.require_api_key,
            settings.default_workspace_id,
        )
        if settings.require_api_key:
            raise ValueError("API key required")
        return settings.default_workspace_id

    api_key = api_key.strip()
    key_hash = hash_key(api_key)
    logger.info(
        "resolve_workspace_id: api_key_present key_hash_prefix=%s allow_default_key=%s",
        key_hash[:10],
        settings.allow_default_key,
    )
    try:
        row = await fetch_one(
            """
            SELECT workspace_id FROM workspace_api_keys
            WHERE key_hash = $1 AND revoked_at IS NULL
            """,
            key_hash,
        )
    except asyncpg.exceptions.UndefinedColumnError:
        logger.warning(
            "resolve_workspace_id: schema_missing_revoked_at_column key_hash_prefix=%s",
            key_hash[:10],
        )
        row = await fetch_one(
            "SELECT workspace_id FROM workspace_api_keys WHERE key_hash = $1",
            key_hash,
        )
    if row:
        if (
            key_hash == hash_key(settings.default_api_key)
            and not settings.allow_default_key
        ):
            logger.info("resolve_workspace_id: sk_default_blocked")
            raise ValueError("Invalid API key")
        logger.info(
            "resolve_workspace_id: resolved workspace_id=%s", row["workspace_id"]
        )
        return str(row["workspace_id"])
    logger.info(
        "resolve_workspace_id: invalid_api_key key_hash_prefix=%s", key_hash[:10]
    )
    raise ValueError("Invalid API key")
