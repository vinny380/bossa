"""FastAPI dependencies."""

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.auth import resolve_workspace_id
from src.auth.jwt import verify_supabase_jwt

_bearer = HTTPBearer()


async def get_current_user_id(
    cred: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Extract Bearer token, verify Supabase JWT, return user_id (sub). Raises 401 if invalid."""
    try:
        payload = verify_supabase_jwt(cred.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return str(user_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


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
