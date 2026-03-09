---
title: "Bossa CLI for AI Agents"
description: "Use Bossa from OpenClaw, Claude Code, and exec-based agents. Commands, auth, and JSON mode."
---

# Bossa CLI for AI Agents

When your agent runs tools as subprocesses (OpenClaw exec, Claude Code, beads, etc.), use the Bossa CLI for persistent filesystem access. No MCP required.

**Install:** `pip install bossa-memory`

---

## Auth

- **`BOSSA_API_KEY`** — Set in env before the agent runs. Injected at container/process start.
- **`bossa workspace use <name> --key sk-xxx`** — Store key in `~/.config/bossa/config.json`. Subsequent `bossa files` commands use it without `--key`.
- **`--key`** — Override per command when needed.

Resolution order: `--key` > `BOSSA_API_KEY` > `BOSSA_WORKSPACE` (from config) > `config.active_key`.

---

## Commands

| Command | Description |
|---------|-------------|
| `bossa files ls [path]` | List directory |
| `bossa files read <path>` | Read file |
| `bossa files write <path>` | Write (stdin or `--content`) |
| `bossa files grep <pattern>` | Search contents |
| `bossa files glob <pattern>` | Find by glob |
| `bossa files edit <path> --old X --new Y` | Replace substring |
| `bossa files delete <path>` | Delete file |

---

## JSON Mode

Set `BOSSA_CLI_JSON=1` or use `--json` for machine-readable output:

```bash
export BOSSA_CLI_JSON=1
bossa files ls /
# {"items": ["a/", "b.txt"]}
```

---

## Exit Codes

- `0` — Success
- `1` — Error (not found, validation)
- `2` — Auth failure (invalid API key)

---

## Example (OpenClaw exec)

```bash
bossa files ls /
bossa files read /memory/summary.md
echo "Session notes" | bossa files write /memory/session-1.md
```

Ensure `bossa` is on PATH and `BOSSA_API_KEY` (or config) is set in the exec environment.
