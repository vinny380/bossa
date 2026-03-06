from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.api.router import api_router
from src.db import close_pool
from src.mcp.server import mcp


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    yield
    await close_pool()


mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with app_lifespan(app):
        async with mcp_app.lifespan(app):
            yield


app = FastAPI(title="Bossa", lifespan=combined_lifespan)
app.include_router(api_router, prefix="/api/v1")
app.mount("/mcp", mcp_app)
