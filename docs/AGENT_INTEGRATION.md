# Agent Integration Guide

This guide is for **AI agents** and **developers** building agents that use Bossa as a virtual filesystem. Use the managed service so your agents get persistent, searchable storage without running infrastructure.

**Base URL:** `https://filesystem-fawn.vercel.app`  
**MCP endpoint:** `https://filesystem-fawn.vercel.app/mcp`

---

## Quick Start for Agents

1. **Get an API key** — Sign up via the Bossa CLI, create a workspace, create a key. See [Getting Started](./GETTING_STARTED.md).

2. **Choose your interface:**
   - **CLI** — If your agent runs tools as subprocesses (CLI-based harnesses, beads), use `bossa files ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete`. Set `BOSSA_CLI_JSON=1` for JSON output.
   - **MCP** — If your harness supports MCP (LangChain, Claude, Cursor), connect to `https://filesystem-fawn.vercel.app/mcp` with headers `Authorization: Bearer YOUR_API_KEY` or `X-API-Key: YOUR_API_KEY`.

3. **Use the tools** — Both interfaces expose the same operations: `ls`, `read`/`read_file`, `write`/`write_file`, `grep`, `glob`/`glob_search`, `edit`/`edit_file`, `delete`/`delete_file`.

---

## CLI Example (agent subprocess)

When your agent executes tools as subprocesses:

```bash
export BOSSA_API_KEY=your-api-key
export BOSSA_CLI_JSON=1

# Agent discovers context
bossa files ls /
bossa files glob "*.md" --path /memory
bossa files read /memory/summary.md

# Agent writes memory
echo "# Session notes\n\n..." | bossa files write /memory/session-1.md
```

---

## LangChain Example (MCP)

```python
import asyncio
import os
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

BOSSA_URL = "https://filesystem-fawn.vercel.app/mcp"
BOSSA_API_KEY = os.environ["BOSSA_API_KEY"]  # Your workspace key

async def main():
    client = MultiServerMCPClient({
        "bossa": {
            "url": BOSSA_URL,
            "transport": "streamable_http",
            "headers": {
                "X-API-Key": BOSSA_API_KEY,
                "Authorization": f"Bearer {BOSSA_API_KEY}"
            }
        }
    })
    tools = await client.get_tools()
    agent = create_agent("openai:gpt-4o", tools)

    response = await agent.ainvoke({
        "messages": [
            HumanMessage(content="List files at / and then read the first file you find")
        ]
    })
    print(response)

asyncio.run(main())
```

---

## Tool Usage Patterns

These patterns apply to both MCP tools and CLI commands. MCP uses `read_file`; CLI uses `bossa files read`.

### Explore Before Reading

Use `ls` to discover structure, then `read`/`read_file` only for relevant files:

```
1. ls path="/"
2. ls path="/customers"
3. read_file path="/customers/acme/profile.md"
```

### Search Without Reading Everything

Use `grep` with `output_mode="files_with_matches"` to find files, then read only matches:

```
1. grep pattern="Enterprise" path="/customers" output_mode="files_with_matches"
2. read_file path="/customers/acme/profile.md"
```

### Save Agent Output

Use `write_file` (MCP) or `bossa files write` (CLI) to persist summaries, analyses, or memory:

```
# MCP
write_file path="/memory/session-summary.md" content="# Session Summary\n\n..."

# CLI
echo "# Session Summary\n\n..." | bossa files write /memory/session-summary.md
```

### Edit In Place

Use `edit_file` (MCP) or `bossa files edit` (CLI) for targeted changes instead of read → modify → write:

```
# MCP
edit_file path="/config.json" old_string="\"debug\": false" new_string="\"debug\": true"

# CLI
bossa files edit /config.json --old '"debug": false' --new '"debug": true'
```

---

## Environment Variables for Examples

| Variable | Description |
|----------|-------------|
| `BOSSA_API_URL` | `https://filesystem-fawn.vercel.app` (managed service) |
| `BOSSA_API_KEY` | Your workspace API key |
| `OPENAI_API_KEY` | For LangChain/OpenAI agents |

---

## Workspace Isolation

Each API key maps to one workspace. Agents using key A cannot see or modify files in workspace B. See [MCP Integration](./MCP.md#workspace-isolation) for details.
