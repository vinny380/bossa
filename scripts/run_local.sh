#!/bin/bash
# Run Bossa locally: Postgres (Docker) + migrations + seed + server.
# Forces local DATABASE_URL; other vars from .env or defaults.

set -e
cd "$(dirname "$0")/.."

# Local Postgres (env vars override .env for this run)
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/bossa"
export ENV="${ENV:-development}"
export DEFAULT_WORKSPACE_ID="${DEFAULT_WORKSPACE_ID:-00000000-0000-0000-0000-000000000001}"
export DEFAULT_API_KEY="${DEFAULT_API_KEY:-sk-default}"

echo "=== Starting Postgres ==="
docker compose up -d postgres

echo "=== Waiting for Postgres ==="
until docker compose exec -T postgres pg_isready -U postgres -d bossa 2>/dev/null; do
  sleep 1
done

echo "=== Running migrations ==="
if docker compose exec -T postgres psql -U postgres -d bossa -tAc "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='workspaces'" 2>/dev/null | grep -q 1; then
  echo "  Schema exists, skipping."
else
  for f in supabase/migrations/*.sql; do
    echo "  $f"
    docker compose exec -T postgres psql -U postgres -d bossa -f - < "$f"
  done
fi

echo "=== Installing dependencies ==="
pip install -r requirements.txt -q

echo "=== Seeding demo data ==="
cd backend && python seed.py && cd ..

echo ""
echo "=== Starting server at http://localhost:8000 ==="
echo "  Health: /health"
echo "  MCP:    /mcp"
echo "  REST:   /api/v1"
echo ""
cd backend && uvicorn src.main:app --reload
