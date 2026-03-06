# Getting Started with Bossa (Managed Service)

Use the Bossa managed service to give your apps and agents a virtual filesystem. No infrastructure to run — just sign up, get an API key, and start building.

**Base URL:** `https://filesystem-fawn.vercel.app`

---

## 1. Install the CLI

The Bossa CLI manages accounts, workspaces, and API keys.

```bash
pip install -r requirements.txt
# Or: pip install -e .   # to get the 'bossa' command
```

---

## 2. Sign Up & Log In

```bash
# Create an account (email + password)
bossa signup

# Log in
bossa login

# Verify
bossa whoami
```

The CLI defaults to the managed service and fetches auth config automatically. No environment variables needed for signup/login.

---

## 3. Create a Workspace & API Key

```bash
# Create a workspace (e.g. "my-app")
bossa workspaces create my-app

# Create an API key (copy it — shown once)
bossa keys create my-app
```

Example output:

```
Created API key for workspace my-app:
  sk-7f3a9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f

Store this key securely. It won't be shown again.
```

---

## 4. Make Your First Request

### REST

```bash
# List root directory
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://filesystem-fawn.vercel.app/api/v1/files/list?path=/"

# Create a file
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"path": "/hello.txt", "content": "Hello from Bossa!"}' \
  "https://filesystem-fawn.vercel.app/api/v1/files"

# Read the file
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://filesystem-fawn.vercel.app/api/v1/files?path=/hello.txt"
```

### MCP

Connect any MCP client (Claude Desktop, Cursor, LangChain) to:

```
https://filesystem-fawn.vercel.app/mcp
```

Pass your API key in headers:

- `Authorization: Bearer YOUR_API_KEY`
- `X-API-Key: YOUR_API_KEY`

See [MCP Integration](./MCP.md) for client-specific setup.

---

## 5. Upload Files via CLI

```bash
# Single file
bossa files put ./my-doc.txt --target /docs/my-doc.txt

# Entire directory (bulk)
bossa files upload ./my-docs --target /docs
```

Set `BOSSA_API_KEY` in your environment, or use `--key YOUR_API_KEY`. The CLI uses the managed service by default when `BOSSA_API_URL` points to the hosted URL.

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `BOSSA_API_URL` | No | Default: `https://filesystem-fawn.vercel.app` (managed service). Override for self-hosted. |
| `BOSSA_API_KEY` | Yes (API calls) | Your workspace API key (for file uploads, examples) |
| `OPENAI_API_KEY` | Yes (examples) | For running the example agents |

**Self-hosting only:** Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` when pointing the CLI at your own backend.

---

## Next Steps

- [MCP Integration](./MCP.md) — Connect Claude, Cursor, LangChain
- [REST API Reference](./REST_API.md) — Full endpoint documentation
- [Agent Integration](./AGENT_INTEGRATION.md) — Build AI agents with Bossa tools
