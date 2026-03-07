<p align="center">
  <h1 align="center">Bossa</h1>
  <p align="center">
    <strong>The Memory Layer of Your Agents</strong>
  </p>
  <p align="center">
    Persistent, searchable memory — backed by Postgres, exposed as a filesystem. Give your agents <code>ls</code>, <code>read</code>, <code>write</code>, <code>grep</code>, and <code>glob</code> to store and recall knowledge across sessions.
  </p>
  <p align="center">
    <strong>📖 <a href="https://bossa.mintlify.app">Documentation → bossa.mintlify.app</a></strong>
  </p>
  <p align="center">
    <a href="#get-started">Get Started</a> &middot;
    <a href="#dynamic-context-discovery">Dynamic Context Discovery</a> &middot;
    <a href="#cli">CLI</a> &middot;
    <a href="#mcp-tools">MCP</a> &middot;
    <a href="#rest-api">REST API</a> &middot;
    <a href="#examples">Examples</a> &middot;
    <a href="https://bossa.mintlify.app">Docs</a>
  </p>
</p>

---

## Why Bossa?

Agents need memory that persists across sessions and scales with search. Bossa is that memory layer — a **Postgres-backed virtual filesystem** exposed through **CLI**, **MCP** (Model Context Protocol), and **REST**. Your agents use familiar operations — `ls`, `read`, `grep`, `write` — while Bossa translates them to SQL with trigram indexes, full-text search, and workspace-scoped access control.

```
Agent  ──CLI──▶  Bossa  ──SQL──▶  Postgres
       ──MCP──▶        (pg_trgm, tsvector, JSONB)
       ──REST─▶
```

**What you get:**

- **Memory as filesystem** — Agents already understand files; no new abstractions. Use `ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete`.
- **Dynamic context discovery** — Search and explore at runtime instead of packing static prompts. Find what matters without reading everything.
- **Workspace isolation** — Each agent or tenant gets its own memory space, scoped by API key.
- **Fast search** — `grep` with boolean logic (`all_of`, `any_of`, `none_of`), regex, pagination, and context lines.
- **CLI + MCP + REST** — Use the CLI when your agent runs subprocesses; use MCP when your harness supports it (LangChain, Claude, Cursor); use REST for scripts and custom integrations.

---

## Dynamic Context Discovery

Traditional **context engineering** means manually assembling prompts with the right docs, examples, and rules. It works, but it's brittle and doesn't scale — you have to guess what context matters upfront.

**Dynamic context discovery** flips that: agents discover what they need at runtime. They `ls` to explore structure, `grep` to find relevant files, `read_file` only what matters. Bossa provides the searchable, persistent memory layer that makes this possible.

```mermaid
flowchart LR
    Agent --> Discover[ls / grep / glob]
    Discover --> Load[read_file]
    Load --> Respond[Respond]
```

Instead of packing static prompts, let your agents discover context dynamically.

---

## Get Started

**Use the managed service** — no infrastructure to run. Give your agents a memory layer and dynamic context discovery in minutes.

| Step | Action |
|------|--------|
| 1 | [Sign up](https://bossa.mintlify.app/GETTING_STARTED#2-sign-up--log-in) via the CLI |
| 2 | [Create a workspace & API key](https://bossa.mintlify.app/GETTING_STARTED#3-create-a-workspace--api-key) |
| 3 | [Connect your agent](https://bossa.mintlify.app/GETTING_STARTED#4-make-your-first-request) via MCP or REST |

**Base URL:** `https://filesystem-fawn.vercel.app`  
**MCP endpoint:** `https://filesystem-fawn.vercel.app/mcp`

### Documentation

| Doc | Description |
|-----|-------------|
| [Getting Started](https://bossa.mintlify.app/GETTING_STARTED) | Sign up, API key, memory layer setup |
| [CLI Reference](https://bossa.mintlify.app/CLI) | Full CLI command reference |
| [MCP Integration](https://bossa.mintlify.app/MCP) | Claude, Cursor, LangChain setup |
| [REST API](https://bossa.mintlify.app/REST_API) | Full API reference |
| [Agent Integration](https://bossa.mintlify.app/AGENT_INTEGRATION) | LangChain examples, tool patterns |
| [Self-Hosting](https://bossa.mintlify.app/SELF_HOSTING) | Run Bossa on your own infrastructure |

---

## CLI

The Bossa CLI is a first-class interface for agents. When your harness runs tools as subprocesses (e.g. CLI-based agents, beads), use `bossa files` for full filesystem parity with MCP: `ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete`. The CLI also manages accounts, workspaces, and API keys. It defaults to the managed service — no config needed.

```bash
pip install bossa-memory
```

```bash
bossa signup                 # Create account
bossa login                  # Log in
bossa workspaces create my-app
bossa keys create my-app     # Copy the key — shown once

bossa files ls /             # List directory
bossa files read /docs/x.md  # Read file
bossa files put ./doc.txt --target /docs
bossa files upload ./my-docs --target /docs
```

**Agent mode:** Use `--json` for machine-readable output, or set `BOSSA_CLI_JSON=1` to get JSON from all commands. Exit codes: 0 success, 1 error, 2 auth failure.

See [CLI Reference](https://bossa.mintlify.app/CLI) for full command reference.

---

## MCP Tools

When your agent harness supports MCP (Claude Desktop, Cursor, LangChain), connect to `https://filesystem-fawn.vercel.app/mcp`. Agents use these tools to discover and use context dynamically — list, search, read, and write memory as files. Bossa exposes **7 tools** via MCP.

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
| `GET` | `/api/v1/files/glob?pattern=...&path=...` | Glob search |
| `PATCH` | `/api/v1/files` | Edit file (replace substring) |
| `DELETE` | `/api/v1/files?path=...` | Delete a file |

Full reference: [REST API](https://bossa.mintlify.app/REST_API).

---

## Examples

### CLI (agent subprocess)

```bash
export BOSSA_API_KEY=your-api-key
export BOSSA_CLI_JSON=1   # JSON output for agents
bossa files ls /
bossa files read /memory/summary.md
echo "New content" | bossa files write /memory/note.txt
```

### Interactive chat (MCP, discover context dynamically)

Clone the repo for examples (requires LangChain, etc.):

```bash
git clone https://github.com/vinny380/bossa && cd bossa
pip install -r requirements.txt
export BOSSA_API_KEY=your-api-key
export OPENAI_API_KEY=sk-...
python examples/chat.py
```

### Scripted agent (LangChain + MCP)

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

Want to run Bossa on your own infrastructure? See [Self-Hosting](https://bossa.mintlify.app/SELF_HOSTING) for local Docker setup and Supabase + Vercel deployment. Self-hosting requires cloning the repo and `pip install -r requirements.txt`.

---

## License

MIT
