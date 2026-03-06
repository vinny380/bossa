# Bossa CLI Reference

The Bossa CLI manages accounts, workspaces, API keys, and provides full filesystem access. It is a first-class interface for agents — when your harness runs tools as subprocesses, use `bossa files` for the same operations as MCP.

**Install:** `pip install -r requirements.txt` or `pip install -e .`

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

## API Keys

| Command | Description |
|---------|-------------|
| `bossa keys create <workspace>` | Create an API key (copy it — shown once) |
| `bossa keys list <workspace>` | List keys for a workspace |
| `bossa keys revoke <workspace> <key_id>` | Revoke a key |

Use `--name` with `create` to name the key (default: `default`).

---

## Filesystem Commands

All `bossa files` commands require `BOSSA_API_KEY` or `--key`. They default to the managed service (`BOSSA_API_URL`).

### Agent Mode

- **`--json`** or **`-j`** — Output JSON for machine parsing
- **`BOSSA_CLI_JSON=1`** — All commands return JSON without passing the flag
- **Exit codes:** 0 success, 1 error (not found, validation), 2 auth failure

### `ls` — List directory

```bash
bossa files ls [path]
```

- **path** (default: `/`): Directory to list
- **Output:** One item per line; directories end with `/`
- **JSON:** `{"items": ["a/", "b.txt"]}`

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
bossa files grep <pattern> [--path /] [--regex] [--case-sensitive] [--output-mode matches|files_with_matches|count]
```

- **pattern:** Literal or regex pattern
- **--path, -p** (default: `/`): Scope to subtree
- **--regex:** Treat pattern as regex
- **--case-sensitive:** Case-sensitive match
- **--output-mode, -o** (default: `matches`): `matches` | `files_with_matches` | `count`
- **--max-matches** (default: 100): Max results

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
bossa files edit <path> --old <string> --new <string>
```

- **path:** File path
- **--old, -o:** String to replace (first occurrence)
- **--new, -n:** Replacement string

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
| `BOSSA_API_KEY` | — | Workspace API key (required for files commands) |
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

Both expose the same filesystem operations. See [Agent Integration](./AGENT_INTEGRATION.md) for examples.
