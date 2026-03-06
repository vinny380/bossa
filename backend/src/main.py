from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from src.api.router import api_router
from src.config import settings
from src.db import close_pool, ping
from src.mcp.request_context import _captured_request
from src.mcp.server import mcp
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class CaptureMCPRequestMiddleware(BaseHTTPMiddleware):
    """Capture request for /mcp so tools can read headers when CurrentHeaders is empty."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            token = _captured_request.set(request)
            try:
                return await call_next(request)
            finally:
                _captured_request.reset(token)
        return await call_next(request)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    yield
    await close_pool()


mcp_app = mcp.http_app(
    path="/",
    transport="streamable-http",
    stateless_http=True,
)


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with app_lifespan(app):
        async with mcp_app.lifespan(app):
            yield


app = FastAPI(title="Bossa", lifespan=combined_lifespan)
app.add_middleware(CaptureMCPRequestMiddleware)
app.include_router(api_router, prefix="/api/v1")
app.mount("/mcp", mcp_app)


@app.get("/auth/config")
async def auth_config() -> dict[str, str]:
    """Public auth config for CLI (Supabase URL + anon key). Used when CLI points at managed service."""
    if settings.supabase_url and settings.supabase_anon_key:
        return {
            "supabase_url": settings.supabase_url,
            "supabase_anon_key": settings.supabase_anon_key,
        }
    raise HTTPException(status_code=404, detail="Auth config not available")


@app.get("/health")
async def health() -> dict[str, str]:
    if not await ping():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "ok"}
