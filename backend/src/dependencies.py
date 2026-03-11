"""FastAPI dependencies."""

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.auth import resolve_workspace_id
from src.auth.jwt import verify_supabase_jwt
from src.usage import check_limits, get_account_id, increment_requests

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


async def get_workspace_id_with_tracking(
    workspace_id: str = Depends(get_workspace_id),
) -> str:
    """Resolve workspace_id, track request, check limits. Use for file endpoints."""
    account_id = await get_account_id(workspace_id)
    if account_id is not None:
        await increment_requests(account_id)
        await check_limits(account_id, "request")
    return workspace_id
