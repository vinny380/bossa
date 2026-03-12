---
title: "CLI Reference"
description: "Full command reference for auth, workspaces, keys, and filesystem operations."
---

# Bossa CLI Reference

The Bossa CLI manages accounts, workspaces, API keys, and provides full filesystem access. It is a first-class interface for agents — when your harness runs tools as subprocesses, use `bossa files` for the same operations as MCP.

**Install:** `pip install bossa-memory`

---

## Agent Documentation (`bossa init`)

Add Bossa usage instructions to your agent config files (AGENTS.md, CLAUDE.md, GEMINI.md) so your AI agent knows how to use Bossa.

```bash
bossa init
```

Scans project and global locations for AGENTS.md, CLAUDE.md, and GEMINI.md, then appends a Bossa section. When multiple files are found, a checkbox list appears: use arrow keys to navigate, Space to toggle, Enter to confirm. In interactive mode, you are also asked how your agent will use Bossa (CLI, MCP, or both). Use flags for non-interactive use:

| Flag | Description |
|------|-------------|
| `--project` | Only project files (./AGENTS.md, ./CLAUDE.md, ./GEMINI.md at project root) |
| `--global` | Only global files (~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, ~/.gemini/GEMINI.md, etc.) |
| `--path PATH` | Explicit path(s); can repeat for multiple files |
| `--mode`, `-m` | `cli`, `mcp`, or `both` — which instructions to include (default: both) |
| `--overwrite` | Replace existing Bossa section (default: append) |
| `--yes`, `-y` | Skip confirmation prompt |

**Append (default):** Adds the Bossa section to the end of the file. Asks for confirmation unless `--yes`.

**Overwrite:** Use `--overwrite` to update an existing Bossa section. Use this when you upgrade to a new bossa version — the generated content includes version-specific commands and flags. Requires the flag explicitly.

```bash
# Append to project files
bossa init --project --yes

# Append to specific file
bossa init --path ./AGENTS.md --yes

# Update to latest (e.g. after upgrading bossa)
bossa init --path ./AGENTS.md --overwrite --yes

# MCP-only instructions (for Cursor, Claude, LangChain)
bossa init --path ./AGENTS.md --mode mcp --yes
```

---

## Authentication

| Command | Description |
|---------|-------------|
| `bossa signup` | Create account (email + password) |
| `bossa login` | Log in |
| `bossa logout` | Clear stored credentials |
| `bossa whoami` | Show current user |

Credentials are stored in `~/.config/bossa/credentials` (or `$XDG_CONFIG_HOME/bossa/credentials`).

---

## Workspaces

| Command | Description |
|---------|-------------|
| `bossa workspaces list` | List your workspaces |
| `bossa workspaces create <name>` | Create a workspace |

Requires login (`bossa login`).

---

## Upgrade to Pro

| Command | Description |
|---------|-------------|
| `bossa billing upgrade [--interval month\|year]` | Open Stripe Checkout in browser to upgrade to Pro. Default: monthly. |
| `bossa billing manage` | Open Stripe Customer Portal to manage subscription (update payment, view invoices, cancel). |

Requires login (`bossa login`).

---

## Workspace Context (Active Workspace)

Set an active workspace to avoid passing `--key` on every `bossa files` command.

| Command | Description |
|---------|-------------|
| `bossa workspace use <name> [--key sk-xxx]` | Set active workspace. Provide `--key` to store it, or use a previously stored key. |
| `bossa workspace current` | Show active workspace name |

Config is stored in `~/.config/bossa/config.json` (or `$XDG_CONFIG_HOME/bossa/config.json`).

---

## Usage

| Command | Description |
|---------|-------------|
| `bossa usage [--json] [--key sk-xxx]` | Show account usage and limits (storage, files, requests). Uses API key like `bossa files`. |

Displays a techy panel with progress bars, percentages, remaining counts, and reset info. Use `--json` or `BOSSA_CLI_JSON=1` for machine-readable output with computed fields (`pct_storage`, `remaining_storage_mb`, `reset_utc`, etc.). Exit codes: 0 success, 1 error, 2 auth failure.

---

## API Keys

| Command | Description |
|---------|-------------|
| `bossa keys create <workspace> [--save]` | Create an API key (copy it — shown once). Use `--save` / `-s` to save key to config as active workspace; no copy/paste needed. |
| `bossa keys list <workspace>` | List keys for a workspace |
| `bossa keys revoke <workspace> <key_id>` | Revoke a key |

Use `--name` with `create` to name the key (default: `default`).

---

## Filesystem Commands

`bossa files` commands use API key from: `--key` > `BOSSA_API_KEY` > `BOSSA_WORKSPACE` (from config) > `config.active_key`. Run `bossa workspace use <name> --key <key>` to avoid passing `--key` on every command. Default API: `BOSSA_API_URL`.

### Agent Mode

- **`--json`** or **`-j`** — Output JSON for machine parsing
- **`BOSSA_CLI_JSON=1`** — All commands return JSON without passing the flag
- **`--safe`** — On read-only commands (`ls`, `read`, `grep`, `glob`, `stat`, `tree`, `du`), signals auto-approval for agent harnesses that gate tool execution
- **Exit codes:** 0 success, 1 error (not found, validation), 2 auth failure

### `ls` — List directory

```bash
bossa files ls [path]
```

- **path** (default: `/`): Directory to list
- **Output:** One item per line; directories end with `/`
- **JSON** (with `--json` or `BOSSA_CLI_JSON=1`): `{"items": [{"name": "a/", "type": "directory"}, {"name": "b.txt", "type": "file", "size": 1024, "modified": "2026-03-06T10:00:00Z"}]}`

### `read` — Read file

```bash
bossa files read <path>
```

- **path:** File path
- **Output:** Raw content to stdout (for piping)
- **JSON:** `{"path": "...", "content": "..."}`

### `write` — Write file

```bash
bossa files write <path> [--content "..." | stdin]
```

- **path:** File path
- **--content, -c:** Content string (or read from stdin)
- **Output:** "Wrote /path" or `{"path": "...", "wrote": true}`

```bash
echo "Hello" | bossa files write /hello.txt
bossa files write /note.txt --content "Note content"
```

### `grep` — Search contents

```bash
bossa files grep [pattern] [--path /] [--regex] [--case-sensitive] [--output-mode matches|files_with_matches|count]
```

- **pattern:** Literal or regex pattern (optional if using --all-of/--any-of/--none-of)
- **--path, -p** (default: `/`): Scope to subtree
- **--regex:** Treat pattern as regex
- **--case-sensitive:** Case-sensitive match
- **--whole-word:** Match whole words only
- **--output-mode, -o** (default: `matches`): `matches` | `files_with_matches` | `count`
- **--max-matches** (default: 100): Max results
- **--offset:** Pagination offset
- **--all-of:** All terms must match (AND). Repeatable.
- **--any-of:** At least one term must match (OR). Repeatable.
- **--none-of:** Exclude lines matching any. Repeatable.
- **--context-before:** Lines before each match
- **--context-after:** Lines after each match

### `glob` — Find by pattern

```bash
bossa files glob <pattern> [--path /]
```

- **pattern:** Glob (e.g. `*.md`, `**/*.py`)
- **--path, -p** (default: `/`): Scope to subtree
- **Output:** One path per line
- **JSON:** `{"paths": ["/a.md", "/b.md"]}`

### `edit` — Replace substring

```bash
bossa files edit <path> --old <string> --new <string> [--all]
```

- **path:** File path
- **--old, -o:** String to replace
- **--new, -n:** Replacement string
- **--all, -a:** Replace all occurrences (default: first only)

### `stat` — File metadata

```bash
bossa files stat <path>
```

- **path:** File path
- **Output:** size, modified, created
- **JSON:** `{"path": "...", "size": N, "modified": "...", "created": "..."}`

### `tree` — Directory tree

```bash
bossa files tree [path] [--depth N]
```

- **path** (default: `/`): Directory to show
- **--depth, -d:** Max depth (default: unlimited)

### `du` — Disk usage

```bash
bossa files du [path]
```

- **path** (default: `/`): Directory to summarize
- **Output:** Size per directory

### `delete` — Delete file

```bash
bossa files delete <path>
```

### `put` — Upload single file

```bash
bossa files put <local_file> [--target /path]
```

- **local_file:** Local file path
- **--target, -t:** Remote path (default: `/` + basename)

### `batch` — Batch operations

```bash
bossa files batch
```

Reads JSON lines from stdin. Each line: `{"op": "read"|"write"|"delete", "path": "...", "content": "..."}` (content required for write). Max 100 ops.

### `upload` — Bulk upload

```bash
bossa files upload <local_path> [--target /prefix] [--include-hidden]
```

- **local_path:** Directory or file
- **--target, -t:** Remote path prefix
- **--include-hidden:** Include hidden files (`.` prefix)

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BOSSA_API_URL` | `https://filesystem-fawn.vercel.app` | API base URL |
| `BOSSA_API_KEY` | — | Workspace API key (or use `bossa workspace use`) |
| `BOSSA_WORKSPACE` | — | Override active workspace by name |
| `BOSSA_CLI_JSON` | — | Set to `1` for JSON output from all commands |
| `BOSSA_TIMEOUT` | `30` | HTTP timeout (seconds) |

**Self-hosting:** Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` when using a self-hosted backend.

---

## CLI vs MCP

| Use CLI when | Use MCP when |
|--------------|--------------|
| Your agent runs tools as subprocesses | Your harness supports MCP (Claude, Cursor, LangChain) |
| CLI-based harnesses (beads, etc.) | You want native tool integration |
| You need `--help` discovery | You use MCP tool descriptors |

Both expose the same filesystem operations. See [Agent Integration](AGENT_INTEGRATION) for examples.
