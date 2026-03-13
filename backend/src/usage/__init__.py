"""Usage tracking and limit enforcement."""

from datetime import datetime, timezone

from src.config import settings
from src.db import execute, fetch_one

LIMITS = {
    "free": {
        "storage_mb": 100,
        "files": 500,
        "requests_per_day": 1_000,
    },
    "pro": {
        "storage_mb": 10_000,  # 10 GB
        "files": 200_000,
        "requests_per_day": 100_000,
    },
    "owner": {
        "storage_mb": 100_000,  # Effectively unlimited
        "files": 1_000_000,
        "requests_per_day": 1_000_000,
    },
}


class LimitError(Exception):
    """Raised when account exceeds usage limits."""

    pass


async def get_account_id(workspace_id: str) -> str | None:
    """Return user_id for workspace, or None if workspace has no user_id (skip enforcement)."""
    row = await fetch_one(
        "SELECT user_id FROM workspaces WHERE id = $1",
        workspace_id,
    )
    if not row or row["user_id"] is None:
        return None
    return str(row["user_id"])


async def get_tier(account_id: str) -> str:
    """Return tier for account. Lazy-creates 'free' if missing. Config owners get 'owner' and are synced to DB."""
    if account_id in settings.owner_user_ids_list:
        # Sync to DB when tier_type enum exists (migration 006); skip if not yet applied
        try:
            await execute(
                """
                INSERT INTO account_tiers (user_id, tier) VALUES ($1, 'owner')
                ON CONFLICT (user_id) DO UPDATE SET tier = 'owner'
                """,
                account_id,
            )
        except Exception:
            pass  # Migration 006 not applied; config is source of truth
        return "owner"

    row = await fetch_one(
        "SELECT tier FROM account_tiers WHERE user_id = $1",
        account_id,
    )
    if row:
        return str(row["tier"])
    await execute(
        """
        INSERT INTO account_tiers (user_id, tier) VALUES ($1, 'free')
        ON CONFLICT (user_id) DO NOTHING
        """,
        account_id,
    )
    return "free"


async def get_usage(account_id: str) -> dict:
    """Return storage_bytes, files_count, requests_today for account."""
    row = await fetch_one(
        """
        SELECT
            COALESCE(SUM(LENGTH(f.content)), 0)::BIGINT AS storage_bytes,
            COUNT(f.id)::INTEGER AS files_count
        FROM files f
        JOIN workspaces w ON f.workspace_id = w.id
        WHERE w.user_id = $1
        """,
        account_id,
    )
    storage_bytes = row["storage_bytes"] or 0
    files_count = row["files_count"] or 0

    today = datetime.now(timezone.utc).date()
    req_row = await fetch_one(
        "SELECT requests FROM usage_daily WHERE user_id = $1 AND date = $2",
        account_id,
        today,
    )
    requests_today = req_row["requests"] if req_row else 0

    return {
        "storage_bytes": storage_bytes,
        "storage_mb": storage_bytes / 1_000_000,
        "files_count": files_count,
        "requests_today": requests_today,
    }


def _is_owner(account_id: str, tier: str | None = None) -> bool:
    """Return True if account_id in config or tier is owner (bypass limits)."""
    if account_id in settings.owner_user_ids_list:
        return True
    return tier == "owner"


async def check_limits(
    account_id: str,
    operation: str,
    delta_storage: int = 0,
    delta_files: int = 0,
) -> None:
    """Raise LimitError if account would exceed limits. Skip if owner."""
    tier = await get_tier(account_id)
    if _is_owner(account_id, tier):
        return

    limits = LIMITS[tier]
    usage = await get_usage(account_id)

    if operation == "request":
        if usage["requests_today"] >= limits["requests_per_day"]:
            raise LimitError(
                f"{tier.capitalize()} tier limit: {limits['requests_per_day']:,} requests/day. "
                "Upgrade at https://docs.bossamemory.com/PRICING"
            )
        return

    if operation == "write":
        new_storage_mb = (usage["storage_bytes"] + delta_storage) / 1_000_000
        if new_storage_mb > limits["storage_mb"]:
            raise LimitError(
                f"{tier.capitalize()} tier limit: {limits['storage_mb']:,} MB storage. "
                "Upgrade at https://docs.bossamemory.com/PRICING"
            )
        new_files = usage["files_count"] + delta_files
        if new_files > limits["files"]:
            raise LimitError(
                f"{tier.capitalize()} tier limit: {limits['files']:,} files. "
                "Upgrade at https://docs.bossamemory.com/PRICING"
            )


async def increment_requests(account_id: str) -> None:
    """Increment daily request count for account. Skip if owner."""
    if _is_owner(account_id):
        return

    today = datetime.now(timezone.utc).date()
    await execute(
        """
        INSERT INTO usage_daily (user_id, date, requests)
        VALUES ($1, $2, 1)
        ON CONFLICT (user_id, date) DO UPDATE
        SET requests = usage_daily.requests + 1
        """,
        account_id,
        today,
    )
