"""Seed a workspace with sample files for context discovery demo."""

import argparse
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.auth import resolve_workspace_id
from src.config import settings
from src.engine import filesystem as fs

FILES = [
    (
        "/customers/acme-corp/profile.md",
        """# Acme Corp

**Tier:** Enterprise
**Contact:** john@acme.com
**Notes:** Interested in API access. Key decision maker.""",
    ),
    (
        "/customers/globex/profile.md",
        """# Globex Inc

**Tier:** Starter
**Contact:** jane@globex.com
**Notes:** Evaluating options. Budget-conscious.""",
    ),
    (
        "/customers/initech/profile.md",
        """# Initech

**Tier:** Enterprise
**Contact:** michael@initech.com
**Notes:** Large team. Needs SSO integration.""",
    ),
    (
        "/tickets/2024/march/ticket-001.md",
        """# Ticket 001

**Customer:** Acme Corp
**Subject:** Pricing objection
**Content:** Customer raised concerns about enterprise pricing. Discussed volume discounts.""",
    ),
    (
        "/tickets/2024/march/ticket-002.md",
        """# Ticket 002

**Customer:** Globex Inc
**Subject:** Onboarding
**Content:** New customer onboarding. Setup call scheduled.""",
    ),
    (
        "/docs/product-overview.md",
        """# Product Overview

Bossa is a cloud-hosted filesystem for AI agents. It provides context discovery through familiar filesystem operations.""",
    ),
    (
        "/docs/api-reference.md",
        """# API Reference

## Files
- POST /api/v1/files - Create or overwrite
- GET /api/v1/files?path=... - Read
- DELETE /api/v1/files?path=... - Delete""",
    ),
    (
        "/memory/README.md",
        """# Agent Scratchpad

Write notes and analysis here. Agents can use this for session memory.""",
    ),
]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a workspace with sample files")
    parser.add_argument(
        "-k",
        "--key",
        help="API key for the workspace to seed (default: default workspace)",
    )
    args = parser.parse_args()

    if args.key:
        workspace_id = await resolve_workspace_id(args.key)
    else:
        workspace_id = settings.default_workspace_id

    for path, content in FILES:
        await fs.write_file(workspace_id, path, content)
        print(f"  {path}")
    print(f"\nSeeded {len(FILES)} files to workspace {workspace_id}")


if __name__ == "__main__":
    asyncio.run(main())
