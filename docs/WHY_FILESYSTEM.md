---
title: "Why Filesystem Over RAG?"
description: "Why leading agent platforms chose filesystems over traditional RAG pipelines."
---




---

## The Comparison

| Filesystem (Bossa) | Traditional RAG |
|--------------------|-----------------|
| `grep "user preferences"` | Tune embeddings, pray it works |
| Directory structure = organization | Flat vector space |
| Works like CLI tools agents know | New abstractions to learn |
| Debuggable with `ls`, `cat` | Black box retrieval |
| No embedding drift | Constant re-indexing |

---

## Why It Matters

### Simple: Just ls, read, write, grep

Agents already understand files. Every developer knows files. No new abstractions to learn. Your agent can `ls` to explore, `grep` to search, `read` to load—exactly like working with a local filesystem.

### Debuggable: See Exactly What's Stored

With a filesystem, you can inspect memory directly. `bossa files ls /` shows the structure. `bossa files read /user/prefs.json` shows the content. No black box. No wondering why retrieval returned the wrong chunk.

### Familiar: Every Agent Knows Files

Files and directories are universal. Nested paths like `/customers/acme/support-tickets/` map to how humans think about organization. Vector spaces don't.

### Fast: Postgres Full-Text Search Under the Hood

Bossa uses Postgres trigrams and full-text search. No embedding API calls. No re-indexing when you add content. Search is instant and deterministic.

---

## For 80% of Agent Use Cases, Filesystems Just Work Better

RAG excels when you have massive, unstructured corpora and need semantic similarity. But for agent memory—user preferences, conversation history, project context, support tickets—a filesystem is simpler, more transparent, and easier to reason about.

**Claude Code and Manus proved it.** Bossa brings that approach to every agent.

---

## Next Steps

- [Dynamic Context Discovery](DYNAMIC_CONTEXT_DISCOVERY) — How Bossa fits the context-engineering pattern
- [Getting Started](GETTING_STARTED) — Sign up and make your first request
- [Use Cases](USE_CASES) — See what you can build
- [Agent Integration](AGENT_INTEGRATION) — Connect your agent framework
