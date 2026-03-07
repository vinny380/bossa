<p align="center">
  <h1 align="center">Bossa</h1>
  <p align="center">
    <strong>Your AI Agent's Long-Term Memory</strong>
  </p>
  <p align="center">
    Remember every conversation. Search instantly. Never repeat yourself.
  </p>
  <p align="center">
    Bossa gives your AI agents a persistent filesystem to store and retrieve context across sessions—just like Claude Code and Manus do.
  </p>
  <p align="center">
    <strong>📖 <a href="https://bossa.mintlify.app">Documentation → bossa.mintlify.app</a></strong>
  </p>
  <p align="center">
    Used by agents built with Claude, LangChain, Cursor, and AutoGPT.
  </p>
  <p align="center">
    <a href="#get-started">Get Started</a> &middot;
    <a href="#why-filesystem-over-rag">Why Filesystem?</a> &middot;
    <a href="#cli">CLI</a> &middot;
    <a href="#mcp-tools">MCP</a> &middot;
    <a href="#rest-api">REST API</a> &middot;
    <a href="#examples">Examples</a> &middot;
    <a href="https://bossa.mintlify.app">Docs</a>
  </p>
</p>

---

## The Problem: Agents Forget Everything

Every time your agent starts, it's like Groundhog Day:

- Re-learning user preferences every session
- Asking the same questions over and over
- No memory of previous work or context
- RAG pipelines that are complex and brittle

**Claude Code and Manus solved this with filesystems.** Now you can too.

---

## Why Filesystem Over RAG?

Leading agent platforms like Claude Code and Manus chose filesystems over traditional RAG pipelines. Here's why:

| Filesystem (Bossa) | Traditional RAG |
|--------------------|------------------|
| `grep "user preferences"` | Tune embeddings, pray it works |
| Directory structure = organization | Flat vector space |
| Works like CLI tools agents know | New abstractions to learn |
| Debuggable with `ls`, `cat` | Black box retrieval |
| No embedding drift | Constant re-indexing |

**For 80% of agent use cases, filesystems just work better.**

[Read: Why We Chose Filesystem Over RAG →](https://bossa.mintlify.app/WHY_FILESYSTEM)

---

## Simple API. Powerful Backend.

Bossa is "Supabase for agent memory"—but simpler. Your agents use familiar operations—`ls`, `read`, `grep`, `write`—while Bossa translates them to SQL with trigram indexes, full-text search, and workspace-scoped access control.

```
Agent  ──CLI──▶  Bossa  ──SQL──▶  Postgres
       ──MCP──▶        (pg_trgm, tsvector, JSONB)
       ──REST─▶
```

**What you get:**

- **Feels like local files** — `ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete`. No new concepts.
- **Powered by Postgres** — Full-text search with trigrams, ACID transactions, JSON storage, enterprise-ready.
- **Plug-and-play** — CLI for subprocess agents; MCP for LangChain, Claude, Cursor; REST for scripts.
- **Your agent's personal file system** — Each agent gets its own space, scoped by API key.

---

## Get Started

**Get started in 30 seconds** — no infrastructure to run. Give your agents long-term memory in minutes.

**What you'll build:**

- Store user preferences in `/user/prefs.json`
- Search past conversations with `grep`
- Remember context across sessions

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
| [Getting Started](https://bossa.mintlify.app/GETTING_STARTED) | Sign up, API key, first request |
| [CLI Reference](https://bossa.mintlify.app/CLI) | Full CLI command reference |
| [MCP Integration](https://bossa.mintlify.app/MCP) | Claude, Cursor, LangChain setup |
| [REST API](https://bossa.mintlify.app/REST_API) | Full API reference |
| [Agent Integration](https://bossa.mintlify.app/AGENT_INTEGRATION) | LangChain examples, tool patterns |
| [Self-Hosting](https://bossa.mintlify.app/SELF_HOSTING) | Run Bossa on your own infrastructure |

---

## What Can You Build?

### Personal AI Assistant

```
/memory
  /user
    preferences.json
    conversation-history/
  /projects
    /project-alpha
      context.md
      decisions.md
```

Your agent remembers preferences, past conversations, and project context.

### Customer Support Agent

```
/customers
  /acme-corp
    account-info.json
    support-tickets/
    interaction-history.md
```

Never ask a customer the same question twice.

### Research Agent

```
/research
  /topic-analysis
    sources.md
    findings.json
    notes/
```

Build up a knowledge base over weeks of research.

[See More Examples →](https://bossa.mintlify.app/USE_CASES)

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
