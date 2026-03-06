<p align="center">
  <h1 align="center">Bossa</h1>
  <p align="center">
    <strong>A virtual filesystem for AI agents, backed by Postgres.</strong>
  </p>
  <p align="center">
    Give your agents <code>ls</code>, <code>read</code>, <code>write</code>, <code>grep</code>, and <code>glob</code> — powered by SQL under the hood.
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> &middot;
    <a href="#mcp-tools">MCP Tools</a> &middot;
    <a href="#rest-api">REST API</a> &middot;
    <a href="#examples">Examples</a>
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

## Quick Start

### 1. Start Postgres

```bash
docker compose up -d postgres
```

### 2. Run migrations

```bash
docker compose exec -T postgres psql -U postgres -d bossa \
  -f - < supabase/migrations/001_initial_schema.sql

docker compose exec -T postgres psql -U postgres -d bossa \
  -f - < supabase/migrations/002_workspace_api_keys.sql
```

### 3. Start the server

```bash
cd backend
cp .env.example .env        # DATABASE_URL is pre-configured for local Docker
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### 4. Seed demo data

```bash
cd backend && python seed.py
```

Server is live at `http://localhost:8000`. MCP at `/mcp`, REST at `/api/v1`.

---

## MCP Tools

Bossa exposes **7 tools** via MCP that agents can call directly. Connect with any MCP-compatible client (LangChain, Claude Desktop, ChatGPT, etc.).

| Tool | What it does |
|---|---|
| **`ls`** | List files and directories at a path. Directories end with `/`. |
| **`read_file`** | Return file contents with numbered lines (`1: line text`). |
| **`write_file`** | Create or overwrite a file. |
| **`edit_file`** | Replace the first occurrence of a substring in a file. |
| **`grep`** | Search file contents with literal/regex patterns, boolean filters, pagination, and context lines. |
| **`glob_search`** | Find files by glob pattern (e.g. `**/*.py`). |
| **`delete_file`** | Permanently delete a file. |

All tools include [MCP annotations](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) (`readOnlyHint`, `destructiveHint`, etc.) so clients can skip confirmation prompts for safe operations.

### `grep` in detail

`grep` is the most powerful tool — it's designed to let agents search without reading entire files:

```
grep(
  pattern="Enterprise",           # literal or regex
  path="/customers/",             # scope to a subtree
  output_mode="files_with_matches",  # just file paths
  all_of=["Enterprise", "SSO"],   # AND logic (same line)
  none_of=["churned"],            # exclude lines
  context_before=2,               # lines of context
  max_matches=50,                 # pagination
)
```

Three output modes: `matches` (lines + context), `files_with_matches` (paths only), `count`.

---

## REST API

All endpoints live under `/api/v1`. Pass workspace API keys via `Authorization: Bearer <key>` or `X-API-Key: <key>`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/files` | Create or overwrite a file (`{path, content}`) |
| `GET` | `/api/v1/files?path=...` | Read a file |
| `GET` | `/api/v1/files/list?path=...` | List directory contents |
| `POST` | `/api/v1/files/search` | Grep search (full `GrepSearchRequest` body) |
| `DELETE` | `/api/v1/files?path=...` | Delete a file |

---

## Workspaces & API Keys

Every file is scoped to a **workspace**. Workspaces are isolated — agents in one workspace cannot see files in another.

- **Default key (dev):** `sk-default` points to the default workspace
- **No key:** falls back to the default workspace
- **Invalid key:** returns `401`

Create a new workspace:

```bash
cd backend && python scripts/create_workspace.py my-workspace
# → Workspace ID: a1b2c3d4-...
# → API Key: sk-7f3a...
```

Pass the key in requests:

```bash
# REST
curl -H "Authorization: Bearer sk-7f3a..." http://localhost:8000/api/v1/files/list

# MCP — headers passed at connection time (see examples below)
```

---

## Examples

### Scripted agent (LangChain + GPT-4o)

The demo agent explores the filesystem, finds Enterprise customers, reads profiles, and writes an analysis:

```bash
cd examples
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
python agent.py
```

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient({
    "bossa": {
        "url": "http://localhost:8000/mcp",
        "transport": "http",
        "headers": {"Authorization": "Bearer sk-default"},
    }
})
tools = await client.get_tools()
agent = create_agent("openai:gpt-4o", tools)

response = await agent.ainvoke({
    "messages": [HumanMessage(content="Find all Enterprise customers")]
})
```

### Interactive chat

```bash
python examples/chat.py
```

```
You: What files are available?
Bossa: I found the following structure:
  customers/
  docs/
  memory/
  tickets/
...

You: Find all tickets about pricing
Bossa: Found 1 match in /tickets/2024/march/ticket-001.md ...
```

---

## Architecture

```
┌─────────────┐     ┌─────────────┐
│  MCP Client │     │ REST Client │
│ (LangChain, │     │  (curl, app)│
│  Claude...) │     │             │
└──────┬──────┘     └──────┬──────┘
       │ MCP (HTTP)        │ REST
       ▼                   ▼
┌──────────────────────────────────┐
│          FastAPI + FastMCP       │
│  ┌──────────┐  ┌──────────────┐ │
│  │ MCP Tools│  │ REST Routes  │ │
│  └────┬─────┘  └──────┬───────┘ │
│       └───────┬───────┘         │
│          ┌────▼─────┐           │
│          │  Engine   │           │
│          │(filesystem│           │
│          │  .py)     │           │
│          └────┬─────┘           │
└───────────────┼─────────────────┘
                │ asyncpg
       ┌────────▼────────┐
       │    Postgres      │
       │ (pg_trgm, GIN,  │
       │  tsvector, JSONB)│
       └─────────────────┘
```

Both MCP and REST share the same engine layer — there's one implementation of each filesystem operation, not two.

---

## Project Structure

```
backend/
  src/
    main.py            # FastAPI app, mounts MCP at /mcp
    config.py           # Env-based settings (DATABASE_URL, etc.)
    db.py               # asyncpg connection pool
    auth.py             # API key → workspace resolution
    models.py           # Pydantic request/response models
    api/                # REST endpoints
    engine/             # Filesystem operations (the actual logic)
    mcp/                # MCP tool definitions
  seed.py              # Populate demo data
  scripts/
    create_workspace.py # Create workspace + API key

examples/
  agent.py             # Scripted demo agent
  chat.py              # Interactive chat

supabase/migrations/   # SQL migrations (001, 002, ...)
tests/                 # pytest (async, real Postgres)
```

---

## Testing

Tests run against a real Postgres instance — no mocks for the database layer.

```bash
# All tests
pytest

# Verbose, single file
pytest tests/test_filesystem.py -v
```

Test coverage includes:
- **Engine:** all filesystem operations, grep with regex/boolean/pagination/context, glob, edit
- **REST API:** CRUD, search, auth (401 for bad keys)
- **MCP tools:** tool invocation via FastMCP test client
- **Integration:** write via REST, read via MCP (and vice versa)
- **Auth:** key resolution, default fallback, invalid key rejection

---

## Configuration

### `backend/.env`

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Postgres connection string | _(required)_ |
| `DEFAULT_WORKSPACE_ID` | Fallback workspace when no API key is provided | `00000000-0000-0000-0000-000000000001` |

### `examples/.env`

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for the example agents | _(required)_ |
| `BOSSA_API_KEY` | Bossa workspace API key | `sk-default` |

---

## License

MIT
