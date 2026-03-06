"""Control plane: workspace CRUD (requires JWT)."""

import asyncpg

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.db import fetch_all, fetch_one
from src.dependencies import get_current_user_id

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: str
    name: str


async def require_workspace_owner(workspace_id: str, user_id: str) -> None:
    """Raise 404 if workspace not found or not owned by user."""
    row = await fetch_one(
        "SELECT id FROM workspaces WHERE id = $1 AND user_id = $2",
        workspace_id,
        user_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    body: WorkspaceCreate,
    user_id: str = Depends(get_current_user_id),
) -> WorkspaceResponse:
    """Create a workspace for the current user."""
    try:
        row = await fetch_one(
            "INSERT INTO workspaces (name, user_id) VALUES ($1, $2) RETURNING id, name",
            body.name,
            user_id,
        )
    except asyncpg.exceptions.UndefinedColumnError as e:
        raise HTTPException(
            status_code=503,
            detail="Database schema outdated. Run migration 003_workspace_user_ownership.sql on your Supabase database.",
        ) from e
    assert row
    return WorkspaceResponse(id=str(row["id"]), name=row["name"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user_id: str = Depends(get_current_user_id),
) -> list[WorkspaceResponse]:
    """List workspaces owned by the current user."""
    rows = await fetch_all(
        "SELECT id, name FROM workspaces WHERE user_id = $1 ORDER BY created_at",
        user_id,
    )
    return [WorkspaceResponse(id=str(r["id"]), name=r["name"]) for r in rows]
