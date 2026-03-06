# Agent Guidance

Guidance for implementing features and maintaining this codebase. See README.md for project overview.

## Testing

### Red/Green TDD

1. **Red**: Write a failing test first. The test describes the desired behavior.
2. **Green**: Implement the minimum code to make the test pass.
3. **Refactor**: Clean up without changing behavior.

Run tests frequently: `pytest` (or `pytest tests/test_foo.py -v` for a single file).

### Test Conventions

- Tests live in `tests/`. Mirror backend structure: `test_filesystem.py` for `engine/filesystem.py`.
- Use real dependencies where practical (Postgres, MCP). Avoid trivial mocks.
- Async tests: use `pytest-asyncio` (already configured in `pytest.ini`).
- Fixtures: `conftest.py` provides `default_workspace_id`, pool cleanup. Reuse them.

## Code Style

### Python

- Type hints on function signatures.
- Pydantic for all data classes and request/response models.
- Prefer `async` for I/O (db, HTTP). Use `asyncpg` for Postgres.

### Structure

- `backend/src/` — core logic. Keep modules focused.
- `backend/src/engine/` — filesystem operations (ls, read, write, grep, etc.).
- `backend/src/api/` — REST endpoints. Thin layer over engine.
- `backend/src/mcp/` — MCP tools. Delegate to engine.

### Adding Features

1. Add or extend tests first. Tests must fail initially. You're following the red/green TDD. 
2. Implement in the engine if it touches data; expose via API and/or MCP as needed.
3. Update `models.py` for new request/response shapes.

## Database

- Migrations in `supabase/migrations/`. Numbered: `001_initial_schema.sql`, `002_...`.
- Never edit applied migrations. Add new ones for schema changes.
- All file operations are scoped by `workspace_id`.

## Security

- No secrets in code. Use `.env` (gitignored) and `pydantic-settings`.
- `.env.example` documents required vars without real values.

## MCP / FastMCP

- When mounting MCP in FastAPI, pass `mcp_app.lifespan` to the parent app (combine with your own lifespan). Otherwise the session manager won't initialize and clients get "Session terminated".
- MCP tools delegate to the engine. Keep tool logic thin.

## Examples

- Load `dotenv` before imports that need env vars (e.g. `OPENAI_API_KEY`).
- For multi-turn agents, pass full conversation history to each invoke so the agent has context (e.g. "your findings" refers to prior turns).

## Auth

- API key per workspace. Keys in `workspace_api_keys` (hashed). Resolve via `src.auth.resolve_workspace_id`.
- REST: `get_workspace_id` dependency. MCP: `get_workspace_id` via `Depends`, reads from `Authorization` or `X-API-Key`.
- No key → default workspace. Invalid key → 401 (REST) or tool error (MCP).

# Version Control
- Leverage GitHub branches to implement new features, merge them back into dev.