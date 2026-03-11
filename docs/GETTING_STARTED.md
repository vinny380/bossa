---
title: "Getting Started"
description: "Sign up, get an API key, and make your first request. CLI, MCP, or REST."
---

# Get Started in 30 Seconds

Give your AI agent persistent memory so it remembers conversations, learns preferences, and builds up context over time—just like Claude Code does.

No database setup. No vector embeddings. Just simple files that work.

**Base URL:** `https://filesystem-fawn.vercel.app`

---

## What You'll Build

By the end of this guide, you'll have an agent that:

- Stores user preferences in `/user/prefs.json`
- Searches past conversations with `grep`
- Remembers context across sessions

Let's go.

---

## 1. Install the CLI

The Bossa CLI manages accounts, workspaces, and API keys.

```bash
pip install bossa-memory
```

---

## 2. Sign Up & Log In

```bash
# Create an account (email + password)
bossa signup

# Log in
bossa login

# Verify
bossa whoami
```

The CLI defaults to the managed service and fetches auth config automatically. No environment variables needed for signup/login.

---

## 3. Create a Workspace & API Key

Free tier includes 1 workspace. See [Pricing & Limits](PRICING) for tier details.

```bash
# Create a workspace (e.g. "my-app")
bossa workspaces create my-app

# Create an API key (copy it — shown once)
bossa keys create my-app
```

**One-liner:** Create workspace and key and save to config in one step:

```bash
bossa workspaces create my-app && bossa keys create my-app --save
```

Example output:

```
Created API key for workspace my-app:
  sk-7f3a9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f

Store this key securely. It won't be shown again.
```

### 4. Set Active Workspace (optional but recommended)

Avoid passing `--key` on every command by setting an active workspace:

```bash
bossa workspace use my-app --key sk-7f3a9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f
```

Or use `bossa keys create my-app --save` to create and save in one step. The key is stored in `~/.config/bossa/config.json`. After this, you can run `bossa files ls /` without `--key`.

### Add Bossa to your agent config (optional)

Run `bossa init` to add Bossa usage instructions to your AGENTS.md or CLAUDE.md. Your AI agent will then know how to use Bossa commands.

```bash
bossa init --path ./AGENTS.md --yes
```

---

## 5. Make Your First Request

Agents can use Bossa in two main ways:

| Interface | When to use |
|-----------|-------------|
| **CLI** | Your agent runs tools as subprocesses (CLI-based harnesses, beads, etc.). Use `bossa files ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete` with `--json` or `BOSSA_CLI_JSON=1`. |
| **MCP** | Your harness supports MCP (Claude Desktop, Cursor, LangChain). Connect to the MCP endpoint and use the tools directly. |

Both expose the same filesystem operations. Choose based on how your agent executes tools.

### REST (scripts, curl)

```bash
# List root directory
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://filesystem-fawn.vercel.app/api/v1/files/list?path=/"

# Create a file
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"path": "/hello.txt", "content": "Hello from Bossa!"}' \
  "https://filesystem-fawn.vercel.app/api/v1/files"

# Read the file
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://filesystem-fawn.vercel.app/api/v1/files?path=/hello.txt"
```

### CLI (agent subprocess)

```bash
# Option A: Use active workspace (after bossa workspace use my-app --key sk-xxx)
bossa files ls /
bossa files read /hello.txt

# Option B: Set BOSSA_API_KEY
export BOSSA_API_KEY=YOUR_API_KEY
export BOSSA_CLI_JSON=1   # Optional: JSON output for agents
bossa files ls /
bossa files read /hello.txt
```

See [CLI Reference](CLI) for the full command reference.

### MCP (agent frameworks)

Connect any MCP client (Claude Desktop, Cursor, LangChain) to:

```
https://filesystem-fawn.vercel.app/mcp
```

Pass your API key in headers:

- `Authorization: Bearer YOUR_API_KEY`
- `X-API-Key: YOUR_API_KEY`

See [MCP Integration](MCP) for client-specific setup.

---

## 6. Upload Files via CLI

```bash
# Single file
bossa files put ./my-doc.txt --target /docs/my-doc.txt

# Entire directory (bulk)
bossa files upload ./my-docs --target /docs
```

Set `BOSSA_API_KEY` in your environment, use `--key YOUR_API_KEY`, or run `bossa workspace use <name> --key <key>` to store the key. The CLI uses the managed service by default when `BOSSA_API_URL` points to the hosted URL.

### Full filesystem access

```bash
bossa files ls /              # List directory
bossa files read /path/file   # Read file
bossa files write /path       # Write (stdin or --content)
bossa files grep "pattern"    # Search contents
bossa files glob "*.md"       # Find by glob
bossa files edit /path --old X --new Y
bossa files delete /path
```

### Using the CLI as an agent

When your agent harness runs tools as subprocesses (e.g. CLI-based agents), use `bossa files` for full filesystem access. Use `--json` for machine-readable output, or set `BOSSA_CLI_JSON=1` so all commands return JSON without passing the flag. Exit codes: 0 success, 1 error, 2 auth failure.

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `BOSSA_API_URL` | No | Default: `https://filesystem-fawn.vercel.app` (managed service). Override for self-hosted. |
| `BOSSA_API_KEY` | Yes (API calls) | Your workspace API key. Or use `bossa workspace use <name> --key <key>`. |
| `BOSSA_WORKSPACE` | No | Override active workspace by name (lookup key from config). |
| `BOSSA_CLI_JSON` | No | Set to `1` for agent mode — all CLI commands return JSON |
| `OPENAI_API_KEY` | Yes (examples) | For running the example agents |

**Self-hosting only:** Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` when pointing the CLI at your own backend.

---

## Next Steps

- [MCP Integration](MCP) — Connect Claude, Cursor, LangChain
- [REST API Reference](REST_API) — Full endpoint documentation
- [Agent Integration](AGENT_INTEGRATION) — Build AI agents with Bossa tools
