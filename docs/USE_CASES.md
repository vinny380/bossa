---
title: "Use Cases"
description: "What you can build with Bossa: personal assistants, support agents, research tools."
---

# What Can You Build?

Bossa gives your agents a persistent filesystem. Here are concrete examples of what that enables.

---

## 1. Personal AI Assistant

Your agent remembers preferences, past conversations, and project context across sessions.

### File Structure

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

### Example: Store and Retrieve Preferences

```bash
# Session 1: Learn user preferences
bossa files write /user/preferences.json '{"theme": "dark", "timezone": "PST", "name": "Alice"}'

# Session 2: Agent retrieves in future sessions
bossa files read /user/preferences.json
# Agent: "I remember you prefer dark mode, Alice!"
```

### Example: Search Past Conversations

```bash
bossa files grep "project alpha" --path /memory
```

---

## 2. Customer Support Agent

Never ask a customer the same question twice. Store account info, ticket history, and interaction context.

### File Structure

```
/customers
  /acme-corp
    account-info.json
    support-tickets/
    interaction-history.md
  /globex-inc
    account-info.json
    support-tickets/
```

### Example: Store Account Context

```bash
bossa files write /customers/acme-corp/account-info.json '{
  "company": "Acme Corp",
  "plan": "enterprise",
  "contact": "support@acme.com",
  "notes": "Prefers email over chat"
}'
```

### Example: Search Across All Customers

```bash
bossa files grep "enterprise" --path /customers
```

---

## 3. Research Agent

Build up a knowledge base over weeks of research. Organize sources, findings, and notes by topic.

### File Structure

```
/research
  /topic-analysis
    sources.md
    findings.json
    notes/
  /ai-trends-2026
    sources.md
    findings.json
```

### Example: Store Research Findings

```bash
bossa files write /research/ai-trends-2026/findings.json '{
  "key_trends": ["multimodal", "agentic", "smaller models"],
  "sources": ["paper1", "paper2"],
  "last_updated": "2026-03-01"
}'
```

### Example: Search Across All Research

```bash
bossa files grep "LLM" --path /research
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

## Next Steps

- [Getting Started](GETTING_STARTED) — Sign up and make your first request
- [Why Filesystem?](WHY_FILESYSTEM) — Filesystem vs RAG
- [Agent Integration](AGENT_INTEGRATION) — Connect LangChain, Claude, Cursor
