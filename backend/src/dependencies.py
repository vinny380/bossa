"""FastAPI dependencies."""

from fastapi import Header, HTTPException
from src.auth import resolve_workspace_id


async def get_workspace_id(
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str:
    """Extract API key from headers and resolve to workspace_id."""
    api_key = x_api_key
    if not api_key and authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:].strip()

    try:
        return await resolve_workspace_id(api_key)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
