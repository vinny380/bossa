<p align="center">
  <h1 align="center">Bossa</h1>
  <p align="center">
    <strong>Stop building agents that forget.</strong>
  </p>
  <p align="center">
    Give your AI a filesystem. <code>ls</code>, <code>grep</code>, <code>read</code>, <code>write</code>. That's it.
  </p>
  <p align="center">
    <strong>📖 <a href="https://docs.bossamemory.com">Documentation → docs.bossamemory.com</a></strong>
  </p>
  <p align="center">
    <code>pip install bossa-memory</code> · No infrastructure · Sign up, get a key, ship.
  </p>
  <p align="center">
    <a href="#get-started">Get Started</a> &middot;
    <a href="https://docs.bossamemory.com/PRICING">Pricing</a> &middot;
    <a href="#why-filesystem-over-rag">Why Filesystem?</a> &middot;
    <a href="#cli">CLI</a> &middot;
    <a href="#mcp-tools">MCP</a> &middot;
    <a href="#rest-api">REST API</a> &middot;
    <a href="#examples">Examples</a> &middot;
    <a href="https://docs.bossamemory.com">Docs</a>
  </p>
</p>

---

## Your agent keeps asking the same questions.

Every session is Groundhog Day. User preferences? Forgotten. Last conversation? Gone. Project context? *What project?*

You've tried RAG. Embeddings. Chunking. Tuning. It's a rabbit hole—and your agent still forgets.

**Claude Code and Manus figured it out: give agents a filesystem.** Not vectors. Not embeddings. Files. `ls`, `grep`, `read`, `write`. Agents already know how to use them. Bossa gives your agents that filesystem—persistent, searchable, Postgres-backed—in one line.

---

## Why filesystem over RAG?

| Bossa (filesystem) | Traditional RAG |
|--------------------|-----------------|
| `grep "user preferences"` | Tune embeddings, pray it works |
| Directory structure = organization | Flat vector space |
| Works like CLI tools agents know | New abstractions to learn |
| Debuggable with `ls`, `cat` | Black box retrieval |
| No embedding drift | Constant re-indexing |

**For 80% of agent use cases, filesystems just work.** [Why we chose this →](https://docs.bossamemory.com/WHY_FILESYSTEM)

---

## Dynamic context discovery—built in.

[Cursor](https://cursor.com/blog/dynamic-context-discovery) and [LangChain](https://blog.langchain.com/context-engineering-for-agents/) are moving to *dynamic context discovery*: let the agent pull context on demand instead of loading everything. Fewer tokens. Better answers.

Bossa is the storage layer for that. Your agent uses `ls` and `grep` to *discover* what's relevant, then `read` to pull only what it needs. No new concepts. Just files.

---

## Get Started

**30 seconds.** No infrastructure. No Docker. No config.

| Step | Action |
|------|--------|
| 1 | [Sign up](https://docs.bossamemory.com/GETTING_STARTED#2-sign-up--log-in) via the CLI |
| 2 | [Create a workspace & API key](https://docs.bossamemory.com/GETTING_STARTED#3-create-a-workspace--api-key) |
| 3 | [Connect your agent](https://docs.bossamemory.com/GETTING_STARTED#4-make-your-first-request) via MCP or REST |

**Base URL:** `https://bossamemory.com`  
**MCP endpoint:** `https://bossamemory.com/mcp`

```bash
pip install bossa-memory
bossa signup && bossa login
bossa workspaces create my-app && bossa keys create my-app
bossa workspace use my-app --key sk-...   # Store key, then:
bossa files ls /
```

---

## What you get

- **Feels like local files** — `ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete`. No new concepts.
- **Powered by Postgres** — Full-text search, trigrams, ACID, JSON. Enterprise-ready.
- **Plug-and-play** — CLI for subprocess agents; MCP for LangChain, Claude, Cursor; REST for scripts.
- **Your agent's space** — Each API key = one workspace. No cross-tenant leakage.

---

## What can you build?

**Coding assistant** — Project context, tech stack, conventions. Your agent remembers how you structure code.

**Multi-agent team** — Multiple agents share one workspace. Handoffs, shared state, no duplicate work.

**Context engineering** — Discover what's relevant with ls/grep, pull only what you need. Fewer tokens.

[See more examples →](https://docs.bossamemory.com/USE_CASES)

---

## CLI

First-class for agents. When your harness runs tools as subprocesses, use `bossa files` for full parity with MCP.

```bash
bossa files ls /                    # List directory
bossa files read /docs/x.md         # Read file
bossa files grep "project alpha"   # Search
echo "content" | bossa files write /note.txt
```

**Agent mode:** `BOSSA_CLI_JSON=1` for machine-readable output. [Full CLI reference →](https://docs.bossamemory.com/CLI)

---

## MCP Tools

Connect to `https://bossamemory.com/mcp`. Pass `Authorization: Bearer YOUR_API_KEY` or `X-API-Key: YOUR_API_KEY`.

| Tool | What it does |
|------|--------------|
| `ls` | List files and directories |
| `read_file` | Read file contents |
| `write_file` | Create or overwrite |
| `edit_file` | Replace substring in place |
| `grep` | Search with literal/regex |
| `glob_search` | Find by pattern |
| `delete_file` | Delete a file |

[MCP setup for Claude, Cursor, LangChain →](https://docs.bossamemory.com/MCP)

---

## REST API

Base URL: `https://bossamemory.com`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/files` | Create or overwrite |
| `GET` | `/api/v1/files?path=...` | Read file |
| `GET` | `/api/v1/files/list?path=...` | List directory |
| `POST` | `/api/v1/files/search` | Grep search |
| `GET` | `/api/v1/files/glob?pattern=...&path=...` | Glob search |
| `PATCH` | `/api/v1/files` | Edit in place |
| `DELETE` | `/api/v1/files?path=...` | Delete |

[Full REST reference →](https://docs.bossamemory.com/REST_API)

---

## Examples

### CLI (agent subprocess)

```bash
export BOSSA_API_KEY=your-api-key
export BOSSA_CLI_JSON=1
bossa files ls /
bossa files read /memory/summary.md
echo "New content" | bossa files write /memory/note.txt
```

### LangChain + MCP

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "bossa": {
        "url": "https://bossamemory.com/mcp",
        "transport": "streamable_http",
        "headers": {"X-API-Key": "YOUR_API_KEY"}
    }
})
tools = await client.get_tools()
# Use with your agent
```

[More examples in the repo →](https://github.com/vinny380/bossa/tree/main/examples)

---

## Self-Hosting

Run Bossa on your own infrastructure. [Self-hosting guide →](https://docs.bossamemory.com/SELF_HOSTING)

---

## Documentation

| Doc | Description |
|-----|-------------|
| [Getting Started](https://docs.bossamemory.com/GETTING_STARTED) | Sign up, API key, first request |
| [Pricing & Limits](https://docs.bossamemory.com/PRICING) | Account tiers, usage limits |
| [Why Filesystem?](https://docs.bossamemory.com/WHY_FILESYSTEM) | Filesystem vs RAG |
| [Dynamic Context Discovery](https://docs.bossamemory.com/DYNAMIC_CONTEXT_DISCOVERY) | How Bossa fits Cursor & LangChain |
| [CLI Reference](https://docs.bossamemory.com/CLI) | Full command reference |
| [MCP Integration](https://docs.bossamemory.com/MCP) | Claude, Cursor, LangChain |
| [REST API](https://docs.bossamemory.com/REST_API) | Full API reference |
| [Agent Integration](https://docs.bossamemory.com/AGENT_INTEGRATION) | Examples, tool patterns |
| [Self-Hosting](https://docs.bossamemory.com/SELF_HOSTING) | Run on your infrastructure |

---

## License

MIT
