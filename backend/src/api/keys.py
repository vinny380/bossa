"""Control plane: API key CRUD (requires JWT)."""

import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api.workspaces import require_workspace_owner
from src.auth import hash_key
from src.db import fetch_all, fetch_one
from src.dependencies import get_current_user_id

router = APIRouter(prefix="/workspaces", tags=["keys"])


class KeyCreate(BaseModel):
    name: str = "default"


class KeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str


class KeyResponse(BaseModel):
    id: str
    name: str
    created_at: str


@router.post("/{workspace_id}/keys", response_model=KeyCreateResponse)
async def create_key(
    workspace_id: str,
    body: KeyCreate,
    user_id: str = Depends(get_current_user_id),
) -> KeyCreateResponse:
    """Create an API key for the workspace. Key is shown once."""
    await require_workspace_owner(workspace_id, user_id)
    api_key = f"sk-{secrets.token_hex(24)}"
    key_hash = hash_key(api_key)
    row = await fetch_one(
        """
        INSERT INTO workspace_api_keys (workspace_id, key_hash, name)
        VALUES ($1, $2, $3)
        RETURNING id, name
        """,
        workspace_id,
        key_hash,
        body.name,
    )
    assert row
    return KeyCreateResponse(
        id=str(row["id"]),
        name=row["name"],
        key=api_key,
    )


@router.get("/{workspace_id}/keys", response_model=list[KeyResponse])
async def list_keys(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
) -> list[KeyResponse]:
    """List API keys for the workspace (metadata only, no plaintext)."""
    await require_workspace_owner(workspace_id, user_id)
    rows = await fetch_all(
        """
        SELECT id, name, created_at FROM workspace_api_keys
        WHERE workspace_id = $1 AND revoked_at IS NULL
        ORDER BY created_at
        """,
        workspace_id,
    )
    return [
        KeyResponse(
            id=str(r["id"]),
            name=r["name"] or "default",
            created_at=r["created_at"].isoformat() if r["created_at"] else "",
        )
        for r in rows
    ]


@router.delete("/{workspace_id}/keys/{key_id}")
async def revoke_key(
    workspace_id: str,
    key_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Revoke an API key (soft delete)."""
    await require_workspace_owner(workspace_id, user_id)
    row = await fetch_one(
        """
        UPDATE workspace_api_keys
        SET revoked_at = NOW()
        WHERE id = $1 AND workspace_id = $2 AND revoked_at IS NULL
        RETURNING id
        """,
        key_id,
        workspace_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Key not found or already revoked")
    return {"revoked": True}
