---
title: "Use Cases"
description: "What you can build with Bossa: coding assistants, multi-agent teams, context engineering, dynamic context discovery."
---

# What Can You Build?

Bossa gives your agents a persistent filesystem. Here are concrete examples aligned with modern agent patterns: coding assistants, multi-agent collaboration, and context engineering.

---

## 1. Coding Assistant

Your coding agent remembers project context, tech stack, and conventions across sessions. No more re-explaining your codebase.

### File Structure

```
/projects
  /my-app
    tech-stack.json
    conventions.md
    architecture.md
    decisions/
```

### Example: Store and Retrieve Project Context

```bash
# Session 1: Capture project context
bossa files write /projects/my-app/tech-stack.json '{"framework": "FastAPI", "db": "Postgres", "style": "async"}'
bossa files write /projects/my-app/conventions.md '# Code style: type hints, pydantic models, async I/O'

# Session 2: Agent pulls context on demand
bossa files read /projects/my-app/conventions.md
# Agent: "I'll follow your FastAPI + async patterns."
```

### Example: Search Across Decisions

```bash
bossa files grep "auth" --path /projects/my-app/decisions
```

---

## 2. Multi-Agent Team

Multiple agents share one workspace. Agent A writes context; Agent B reads it. Handoffs, shared state, no duplicate work.

### File Structure

```
/agents
  /planner
    current-task.md
    next-steps.md
  /coder
    implementation-notes.md
  /reviewer
    feedback.md
```

### Example: Agent Handoff

```bash
# Planner agent writes task for coder
bossa files write /agents/planner/current-task.md 'Implement auth middleware. Use JWT. See /agents/planner/next-steps.md'

# Coder agent reads and executes
bossa files read /agents/planner/current-task.md
bossa files read /agents/planner/next-steps.md
# Coder: implements, then writes notes for reviewer
bossa files write /agents/coder/implementation-notes.md 'Auth done. Edge cases: token expiry, refresh flow.'
```

### Example: Shared Discovery

```bash
bossa files ls /agents
bossa files grep "auth" --path /agents
```

---

## 3. Context Engineering (Dynamic Context Discovery)

Instead of loading everything into context, agents discover what's relevant with `ls` and `grep`, then pull only what they need. Fewer tokens, better answers. Same pattern Cursor and LangChain use for dynamic context.

### File Structure

```
/context
  /user
    preferences.json
  /projects
    /alpha
      summary.md
      decisions/
    /beta
      summary.md
```

### Example: Discover Then Read

```bash
# Agent discovers what exists
bossa files ls /context/projects

# Agent searches for relevant context
bossa files grep "database" --path /context

# Agent reads only what it needs
bossa files read /context/projects/alpha/summary.md
```

### Example: Avoid Token Bloat

```bash
# Don't load everything—grep first, read second
bossa files grep "migration" --path /context/projects/alpha
# Then: bossa files read /context/projects/alpha/decisions/migration-2026-03.md
```

---

## 4. Session Memory (Learn Once, Remember Forever)

The simplest pattern: learn something in session 1, use it in session 2.

```bash
# Session 1: Learn something
bossa files write /learned/facts.json '{"user_likes": "vim", "preferred_lang": "Python"}'

# Session 2: Remember it
bossa files read /learned/facts.json
# Agent: "I remember you like vim!"
```

---

## 5. Research Agent

Build up a knowledge base over weeks. Organize sources, findings, and notes by topic. Search across everything.

### File Structure

```
/research
  /ai-trends-2026
    sources.md
    findings.json
  /context-engineering
    papers.md
    notes/
```

### Example: Store and Search Research

```bash
bossa files write /research/context-engineering/findings.json '{
  "key_concepts": ["dynamic context", "pull-on-demand", "ls/grep pattern"],
  "sources": ["cursor-blog", "langchain-blog"]
}'
bossa files grep "dynamic context" --path /research
```

---

## 6. Customer Support Agent

Never ask a customer the same question twice. Store account info, ticket history, and interaction context.

### File Structure

```
/customers
  /acme-corp
    account-info.json
    support-tickets/
    interaction-history.md
```

### Example: Store and Search Customer Context

```bash
bossa files write /customers/acme-corp/account-info.json '{
  "company": "Acme Corp",
  "plan": "enterprise",
  "notes": "Prefers email over chat"
}'
bossa files grep "enterprise" --path /customers
```

---

## Next Steps

- [Getting Started](GETTING_STARTED) — Sign up and make your first request
- [Why Filesystem?](WHY_FILESYSTEM) — Filesystem vs RAG
- [Agent Integration](AGENT_INTEGRATION) — Connect LangChain, Claude, Cursor
