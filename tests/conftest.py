import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
# Ensure required config for tests (no defaults in app code; .env.example documents prod)
os.environ.setdefault("ENV", "development")
os.environ.setdefault("DEFAULT_API_KEY", "sk-default")

# Test user ID for limit tests (workspaces with user_id)
TEST_USER_ID = "00000000-0000-0000-0000-000000000002"


@pytest.fixture
def default_workspace_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
async def ensure_migration_005():
    """Ensure migration 005 tables exist (for limit tests)."""
    from src.db import execute

    try:
        await execute("SELECT 1 FROM account_tiers LIMIT 1")
        await execute("SELECT 1 FROM usage_daily LIMIT 1")
    except Exception:
        # Create tier_type enum if missing (for migration 006 compatibility)
        await execute("""
            DO $$ BEGIN
                CREATE TYPE tier_type AS ENUM ('free', 'pro', 'owner');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$
        """)
        await execute("""
            CREATE TABLE IF NOT EXISTS account_tiers (
                user_id UUID PRIMARY KEY,
                tier tier_type NOT NULL DEFAULT 'free'::tier_type,
                stripe_customer_id TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await execute("""
            CREATE TABLE IF NOT EXISTS usage_daily (
                user_id UUID NOT NULL,
                date DATE NOT NULL,
                requests INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)
        try:
            await execute(
                "CREATE INDEX idx_usage_daily_user_date ON usage_daily(user_id, date)"
            )
        except Exception:
            pass
    yield


@pytest.fixture
async def ensure_test_user():
    """Ensure TEST_USER_ID exists in auth.users (and auth.identities) for FK satisfaction.
    Required when running against Supabase local or any DB with workspaces_user_id_fkey.
    Skips if auth.users does not exist (plain Postgres)."""
    from src.db import execute, fetch_one

    try:
        check = await fetch_one(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'auth' AND table_name = 'users'"
        )
        if not check:
            yield
            return

        await execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

        await execute(
            """
            INSERT INTO auth.users (
                id, instance_id, aud, role, email, encrypted_password,
                email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
                created_at, updated_at
            )
            VALUES (
                $1::uuid,
                '00000000-0000-0000-0000-000000000000'::uuid,
                'authenticated',
                'authenticated',
                'test@test.local',
                crypt('test', gen_salt('bf')),
                NOW(),
                '{"provider":"email","providers":["email"]}'::jsonb,
                '{}'::jsonb,
                NOW(),
                NOW()
            )
            ON CONFLICT (id) DO NOTHING
            """,
            TEST_USER_ID,
        )

        identity_data = '{"sub": "' + TEST_USER_ID + '", "email": "test@test.local"}'
        await execute(
            """
            INSERT INTO auth.identities (
                id, user_id, identity_data, provider, provider_id,
                last_sign_in_at, created_at, updated_at
            )
            VALUES (
                $1::uuid, $1::uuid, $2::jsonb,
                'email', $1::uuid,
                NOW(), NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
            """,
            TEST_USER_ID,
            identity_data,
        )
    except Exception:
        pass
    yield


@pytest.fixture
async def workspace_with_user(ensure_migration_005, ensure_test_user):
    """Create workspace with user_id and root folder for limit tests."""
    from src.db import execute

    wid = str(uuid.uuid4())
    await execute(
        "INSERT INTO workspaces (id, name, user_id) VALUES ($1, $2, $3)",
        wid,
        "test-limit-workspace",
        TEST_USER_ID,
    )
    await execute(
        "INSERT INTO folders (workspace_id, parent_id, name, path, depth) VALUES ($1, NULL, '', '/', 0)",
        wid,
    )
    yield wid, TEST_USER_ID
    await execute("DELETE FROM files WHERE workspace_id = $1", wid)
    await execute("DELETE FROM folders WHERE workspace_id = $1", wid)
    await execute("DELETE FROM workspace_api_keys WHERE workspace_id = $1", wid)
    await execute("DELETE FROM workspaces WHERE id = $1", wid)
    await execute("DELETE FROM usage_daily WHERE user_id = $1", TEST_USER_ID)
    await execute("DELETE FROM account_tiers WHERE user_id = $1", TEST_USER_ID)


@pytest.fixture
async def api_key_for_user_workspace(workspace_with_user):
    """Create API key for workspace_with_user, yield (api_key, workspace_id, user_id)."""
    import hashlib
    import secrets

    from src.db import execute

    workspace_id, user_id = workspace_with_user
    api_key = f"sk-{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    await execute(
        """
        INSERT INTO workspace_api_keys (workspace_id, key_hash, name)
        VALUES ($1, $2, $3)
        """,
        workspace_id,
        key_hash,
        "test-limit-key",
    )
    yield api_key, workspace_id, user_id
    await execute(
        "DELETE FROM workspace_api_keys WHERE workspace_id = $1 AND key_hash = $2",
        workspace_id,
        key_hash,
    )


@pytest.fixture
async def api_client_with_user_workspace(api_key_for_user_workspace):
    """AsyncClient with API key for workspace that has user_id. Yields (client, user_id)."""
    from httpx import ASGITransport, AsyncClient
    from src.main import app

    api_key, workspace_id, user_id = api_key_for_user_workspace
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {api_key}"},
    ) as client:
        yield client, user_id


@pytest.fixture(autouse=True)
async def cleanup_db_pool() -> None:
    yield
    from src.db import close_pool

    await close_pool()
