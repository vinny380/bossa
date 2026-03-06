# Bossa

A context discovery engine for AI agents — a hosted virtual filesystem backed by Postgres, exposed via FastMCP. Agents use familiar filesystem operations (`ls`, `cat`, `grep`, `write_file`) while the backend translates to SQL.

## Quick Start

### 1. Database (Docker)

```bash
docker compose up -d postgres
docker compose exec -T postgres psql -U postgres -d bossa -f - < supabase/migrations/001_initial_schema.sql
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env: DATABASE_URL=postgres://postgres:postgres@localhost:5432/bossa
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### 3. Seed Data

```bash
cd backend && python seed.py
```

Seed a specific workspace by API key:

```bash
python seed.py -k sk-aa2b593af96316c9347ce102b7847fbf6b8f373630bea998
```

### 4. Example Agent

```bash
cd examples
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY
python agent.py
```

## API

- **REST**: `http://localhost:8000/api/v1/files`
- **MCP**: `http://localhost:8000/mcp` (HTTP transport)

### Workspaces & API Keys

Each workspace has its own files. Pass an API key to access a workspace:

- **Header**: `Authorization: Bearer <key>` or `X-API-Key: <key>`
- **Default key** (dev): `sk-default` → default workspace

Create a new workspace + key:

```bash
cd backend && python scripts/create_workspace.py my-workspace
```

## Tests

```bash
pytest
```

Requires Postgres (Docker) and `backend/.env` with `DATABASE_URL`.
