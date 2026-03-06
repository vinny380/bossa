# Agent Integration Guide

This guide is for **AI agents** and **developers** building agents that use Bossa as a virtual filesystem. Use the managed service so your agents get persistent, searchable storage without running infrastructure.

**Base URL:** `https://filesystem-fawn.vercel.app`  
**MCP endpoint:** `https://filesystem-fawn.vercel.app/mcp`

---

## Quick Start for Agents

1. **Get an API key** — Sign up via the Bossa CLI, create a workspace, create a key. See [Getting Started](./GETTING_STARTED.md).

2. **Connect via MCP** — Point your MCP client at `https://filesystem-fawn.vercel.app/mcp` with headers:
   - `Authorization: Bearer YOUR_API_KEY`
   - `X-API-Key: YOUR_API_KEY`

3. **Use the tools** — `ls`, `read_file`, `write_file`, `grep`, `glob_search`, `edit_file`, `delete_file`.

---

## LangChain Example

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

### Explore Before Reading

Use `ls` to discover structure, then `read_file` only for relevant files:

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

Use `write_file` to persist summaries, analyses, or memory:

```
write_file path="/memory/session-summary.md" content="# Session Summary\n\n..."
```

### Edit In Place

Use `edit_file` for targeted changes instead of read → modify → write:

```
edit_file path="/config.json" old_string="\"debug\": false" new_string="\"debug\": true"
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
