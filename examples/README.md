# Bossa Example Agent

A LangChain agent that connects to the Bossa MCP server and performs context discovery.

## Prerequisites

1. Bossa backend running: `cd backend && uvicorn src.main:app --reload`
2. Seed data: `cd backend && python seed.py`
3. OpenAI API key

## Setup

```bash
cd examples
pip install -r ../requirements.txt
cd .. && cp .env.example .env
# Edit .env in repo root and add your OPENAI_API_KEY
```

## Run

**Interactive chat** (recommended):

```bash
python chat.py
```

**Demo script** (runs predefined queries):

```bash
python agent.py
```

The agent will:
1. Explore the filesystem with `ls`
2. Search for Enterprise customers with `grep`
3. Read customer profiles with `read_file`
4. Save analysis with `write_file`
