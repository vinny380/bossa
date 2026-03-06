<p align="center">
  <h1 align="center">Bossa</h1>
  <p align="center">
    <strong>A virtual filesystem for AI agents, backed by Postgres.</strong>
  </p>
  <p align="center">
    Give your agents <code>ls</code>, <code>read</code>, <code>write</code>, <code>grep</code>, and <code>glob</code> — powered by SQL under the hood.
  </p>
  <p align="center">
    <a href="#get-started">Get Started</a> &middot;
    <a href="#mcp-tools">MCP Tools</a> &middot;
    <a href="#rest-api">REST API</a> &middot;
    <a href="#examples">Examples</a> &middot;
    <a href="docs/README.md">Docs</a>
  </p>
</p>

---

## Why Bossa?

Most agent frameworks give you tools that read from local disk. That works until you need **multi-tenant isolation**, **search at scale**, or **persistent memory across sessions**.

Bossa replaces the local filesystem with a **Postgres-backed virtual filesystem** and exposes it through **MCP** (Model Context Protocol) and a **REST API**. Your agents use familiar operations — `ls`, `read_file`, `grep`, `write_file` — while Bossa translates them to SQL queries with trigram indexes, full-text search, and workspace-scoped access control.

```
Agent  ──MCP──▶  Bossa  ──SQL──▶  Postgres
       ──REST─▶         (pg_trgm, tsvector, JSONB)
```

**What you get:**

- **Filesystem semantics** agents already understand (`ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete`)
- **Workspace isolation** — each tenant gets its own filesystem, scoped by API key
- **Fast search** — `grep` with boolean logic (`all_of`, `any_of`, `none_of`), regex, pagination, and context lines
- **Dual interface** — MCP for agent frameworks (LangChain, Claude, etc.), REST for everything else
- **Zero local state** — everything lives in Postgres, agents can resume across sessions

---

## Get Started

**Use the managed service** — no infrastructure to run.

| Step | Action |
|------|--------|
| 1 | [Sign up](docs/GETTING_STARTED.md#2-sign-up--log-in) via the CLI |
| 2 | [Create a workspace & API key](docs/GETTING_STARTED.md#3-create-a-workspace--api-key) |
| 3 | [Connect your agent](docs/GETTING_STARTED.md#4-make-your-first-request) via MCP or REST |

**Base URL:** `https://filesystem-fawn.vercel.app`  
**MCP endpoint:** `https://filesystem-fawn.vercel.app/mcp`

### Documentation

| Doc | Description |
|-----|-------------|
| [Getting Started](docs/GETTING_STARTED.md) | Sign up, API key, first request |
| [MCP Integration](docs/MCP.md) | Claude, Cursor, LangChain setup |
| [REST API](docs/REST_API.md) | Full API reference |
| [Agent Integration](docs/AGENT_INTEGRATION.md) | LangChain examples, tool patterns |
| [Self-Hosting](docs/SELF_HOSTING.md) | Run Bossa on your own infrastructure |

---

## CLI

The Bossa CLI manages accounts, workspaces, and API keys. It defaults to the managed service — no config needed.

```bash
pip install -r requirements.txt
# Or: pip install -e .
```

```bash
bossa signup                 # Create account
bossa login                  # Log in
bossa workspaces create my-app
bossa keys create my-app     # Copy the key — shown once

bossa files put ./doc.txt --target /docs
bossa files upload ./my-docs --target /docs
```

See [Getting Started](docs/GETTING_STARTED.md) for full setup.

---

## MCP Tools

Bossa exposes **7 tools** via MCP. Connect Claude Desktop, Cursor, LangChain, or any MCP client to `https://filesystem-fawn.vercel.app/mcp`.

| Tool | What it does |
|------|--------------|
| **`ls`** | List files and directories at a path. Directories end with `/`. |
| **`read_file`** | Return file contents with numbered lines (`1: line text`). |
| **`write_file`** | Create or overwrite a file. |
| **`edit_file`** | Replace the first occurrence of a substring in a file. |
| **`grep`** | Search file contents with literal/regex patterns, boolean filters, pagination. |
| **`glob_search`** | Find files by glob pattern (e.g. `**/*.py`). |
| **`delete_file`** | Permanently delete a file. |

Pass your API key in headers: `Authorization: Bearer YOUR_API_KEY` or `X-API-Key: YOUR_API_KEY`.

---

## REST API

All endpoints under `/api/v1`. Base URL: `https://filesystem-fawn.vercel.app`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/files` | Create or overwrite a file |
| `POST` | `/api/v1/files/bulk` | Bulk create/overwrite files |
| `GET` | `/api/v1/files?path=...` | Read a file |
| `GET` | `/api/v1/files/list?path=...` | List directory contents |
| `POST` | `/api/v1/files/search` | Grep search |
| `DELETE` | `/api/v1/files?path=...` | Delete a file |

Full reference: [docs/REST_API.md](docs/REST_API.md).

---

## Examples

### Interactive chat

```bash
export BOSSA_API_URL=https://filesystem-fawn.vercel.app
export BOSSA_API_KEY=your-api-key
export OPENAI_API_KEY=sk-...
python examples/chat.py
```

### Scripted agent (LangChain)

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient({
    "bossa": {
        "url": "https://filesystem-fawn.vercel.app/mcp",
        "transport": "streamable_http",
        "headers": {
            "Authorization": "Bearer YOUR_API_KEY",
            "X-API-Key": "YOUR_API_KEY"
        }
    }
})
tools = await client.get_tools()
agent = create_agent("openai:gpt-4o", tools)
# Use agent.ainvoke(...)
```

---

## Self-Hosting

Want to run Bossa on your own infrastructure? See [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md) for local Docker setup and Supabase + Vercel deployment.

---

## License

MIT
