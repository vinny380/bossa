import os

import pytest
from dotenv import load_dotenv

load_dotenv("backend/.env")
# Allow anonymous access in tests (in-process MCP has no HTTP headers)
os.environ.setdefault("REQUIRE_API_KEY", "false")
# Allow sk-default for API tests
os.environ.setdefault("ALLOW_DEFAULT_KEY", "true")


@pytest.fixture
def default_workspace_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
async def cleanup_db_pool() -> None:
    yield
    from src.db import close_pool

    await close_pool()
