---
title: "Self-Hosting"
description: "Run Bossa on your own infrastructure. Docker, Supabase, Vercel."
---

# Self-Hosting Bossa

Run Bossa on your own infrastructure. For most users, the [managed service](index#why-bossa) is simpler — no Postgres, migrations, or deployment to manage.

**When self-hosting:** CLI users must set `BOSSA_API_URL` to your deployment URL and `SUPABASE_URL` + `SUPABASE_ANON_KEY` (your Supabase project) so the CLI can authenticate.

---

## Quick Start (Local)

**One-liner (Postgres + migrations + seed + server):**

```bash
./scripts/run_local.sh
```

Or step by step:

### 1. Start Postgres

```bash
docker compose up -d postgres
```

### 2. Run migrations

```bash
docker compose exec -T postgres psql -U postgres -d bossa \
  -f - < supabase/migrations/001_initial_schema.sql

docker compose exec -T postgres psql -U postgres -d bossa \
  -f - < supabase/migrations/002_workspace_api_keys.sql

docker compose exec -T postgres psql -U postgres -d bossa \
  -f - < supabase/migrations/003_workspace_user_ownership.sql

docker compose exec -T postgres psql -U postgres -d bossa \
  -f - < supabase/migrations/004_folders.sql

docker compose exec -T postgres psql -U postgres -d bossa \
  -f - < supabase/migrations/005_rls_policies.sql
```

### 3. Start the server

```bash
cp .env.example .env        # ENV=development, DATABASE_URL pre-configured for local Docker
pip install -r requirements.txt
cd backend
uvicorn src.main:app --reload
```

### 4. Seed demo data

```bash
cd backend && python seed.py
```

Server is live at `http://localhost:8000`. Health at `/health`, MCP at `/mcp`, REST at `/api/v1`.

### 5. Run tests

```bash
pytest
```

---

## Deploy to Supabase + Vercel

Hosted deployment path. **API keys are required** for all data endpoints (REST and MCP); only `/health` is public.

### 1. Create a Supabase project

Use the project Postgres connection string as `DATABASE_URL`. The app connects directly over Postgres, so no Supabase client setup is required.

### 2. Run migrations on Supabase

Apply all SQL migrations in order:

```
supabase/migrations/001_initial_schema.sql
supabase/migrations/002_workspace_api_keys.sql
supabase/migrations/003_workspace_user_ownership.sql
supabase/migrations/004_folders.sql
supabase/migrations/005_rls_policies.sql
```

See [RLS_AND_SECURITY.md](RLS_AND_SECURITY.md) for why RLS is required (protects data when using anon key).

Run them with the Supabase SQL editor or `psql` against the Supabase Postgres endpoint.

### 3. Set Vercel environment variables

In your Vercel project settings, add:

```bash
ENV=production
DATABASE_URL=postgres://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres
DEFAULT_WORKSPACE_ID=00000000-0000-0000-0000-000000000001
DEFAULT_API_KEY=sk-default
```

For CLI auth (signup/login) to work against your deployment:

```bash
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=your-anon-key-from-supabase-dashboard
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-dashboard
```

The CLI fetches `SUPABASE_URL` and `SUPABASE_ANON_KEY` from `GET /auth/config` when users point at your deployment. Users who self-host must set these env vars when running their own backend.

### 4. Deploy

```bash
vercel
```

For local Vercel-style verification:

```bash
vercel dev
```

### 5. Smoke test

```bash
curl https://your-deployment-url.vercel.app/health
curl -H "Authorization: Bearer YOUR_API_KEY" https://your-deployment-url.vercel.app/api/v1/files/list?path=/
```

`sk-default` is blocked in production. Create keys with the CLI or `python backend/scripts/create_workspace.py`.

MCP endpoint: `https://your-deployment-url.vercel.app/mcp` (pass `Authorization: Bearer YOUR_API_KEY` or `X-API-Key: YOUR_API_KEY` in client headers).
