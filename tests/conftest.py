import pytest
from dotenv import load_dotenv

load_dotenv("backend/.env")


@pytest.fixture
def default_workspace_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
async def cleanup_db_pool() -> None:
    yield
    from src.db import close_pool
    await close_pool()
