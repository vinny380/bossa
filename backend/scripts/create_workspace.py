"""Create a new workspace and API key. Usage: python scripts/create_workspace.py [name]"""

import asyncio
import hashlib
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import execute, fetch_one


async def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "workspace"
    workspace_id = await fetch_one(
        "INSERT INTO workspaces (name) VALUES ($1) RETURNING id",
        name,
    )
    assert workspace_id
    wid = str(workspace_id["id"])

    api_key = f"sk-{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    await execute(
        """
        INSERT INTO workspace_api_keys (workspace_id, key_hash, name)
        VALUES ($1, $2, $3)
        """,
        wid,
        key_hash,
        f"{name}-key",
    )

    print(f"Workspace: {wid}")
    print(f"API key:  {api_key}")
    print(f"\nUse in requests: Authorization: Bearer {api_key}")
    print(f"Or: X-API-Key: {api_key}")


if __name__ == "__main__":
    asyncio.run(main())
