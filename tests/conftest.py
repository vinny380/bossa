import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
# Ensure required config for tests (no defaults in app code; .env.example documents prod)
os.environ.setdefault("ENV", "development")
os.environ.setdefault("DEFAULT_API_KEY", "sk-default")


@pytest.fixture
def default_workspace_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
async def cleanup_db_pool() -> None:
    yield
    from src.db import close_pool

    await close_pool()
