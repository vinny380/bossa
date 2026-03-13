---
title: "Dynamic Context Discovery"
description: "How Bossa fits the context-engineering pattern used by Cursor and LangChain."
---

Modern agent harnesses are shifting from **static context** (everything loaded up front) to **dynamic context discovery**—letting the agent pull relevant context on demand. As [Cursor puts it](https://cursor.com/blog/dynamic-context-discovery):

> As models have become better as agents, we've found success by providing fewer details up front, making it easier for the agent to pull relevant context on its own.

Dynamic discovery is more token-efficient and improves response quality by reducing context window bloat. Bossa provides the **files primitive** that this pattern relies on.

---

## Why Files Work

Files are the universal interface for dynamic context discovery. Agents already understand `ls`, `grep`, `read`, and `tail`. No new abstractions to learn. Cursor notes that "files have been a simple and powerful primitive to use"—and Bossa gives your agents a persistent, searchable filesystem for exactly that.

When context lives in files, the agent can:

- **Discover** structure with `ls` and `glob` before loading anything
- **Search** with `grep` to find relevant files without reading everything
- **Read** only what it needs, when it needs it
- **Persist** context (scratchpad, memory) for later discovery

---

## How Bossa Fits

Bossa's operations map directly to the dynamic context discovery pattern:

| Operation | Role in Dynamic Discovery |
|-----------|---------------------------|
| `ls` / `glob` | Discover structure before loading; see what's available |
| `grep` | Find relevant files without reading everything |
| `read` | Pull only what's needed into the context window |
| `write` | Persist context (summaries, preferences, session notes) for later discovery |

Your agent stores memory in Bossa. When it needs context, it uses `ls`, `grep`, or `glob` to find the right files, then `read` to load only those. No embedding calls. No retrieval pipeline. Just files.

---

## Practical Patterns

The patterns in [Agent Integration](AGENT_INTEGRATION) are dynamic context discovery in action:

### Explore Before Reading

Use `ls` to discover structure, then `read` only for relevant files:

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

These patterns keep the context window lean. The agent pulls only what it needs.

---

## Next Steps

- [Why Filesystem Over RAG?](WHY_FILESYSTEM) — Filesystem vs RAG for agent memory
- [Agent Integration](AGENT_INTEGRATION) — CLI and MCP examples, tool usage patterns
- [Getting Started](GETTING_STARTED) — Sign up and make your first request

---

## References

- [Dynamic context discovery](https://cursor.com/blog/dynamic-context-discovery) — Cursor (Jan 2026)
- [Context Engineering for Agents](https://blog.langchain.com/context-engineering-for-agents/) — LangChain (Jul 2025)
