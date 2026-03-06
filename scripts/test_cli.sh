#!/bin/bash
# Test the Bossa CLI: login, create workspace, create key.
# Prerequisites:
#   1. Create .env in project root with:
#      SUPABASE_URL=https://YOUR_PROJECT.supabase.co
#      SUPABASE_ANON_KEY=your-anon-key
#   2. Enable Supabase Auth (email/password). Create a user: python -m cli signup
#   3. Run migration 003 on Supabase
#   4. Set SUPABASE_JWT_SECRET in Vercel for the API

set -e
cd "$(dirname "$0")/.."

echo "=== Installing CLI dependencies ==="
python -m pip install -r requirements.txt -q

echo "The CLI loads SUPABASE_URL, SUPABASE_ANON_KEY from root .env"
echo ""

echo "=== Step 1: Login (email + password) ==="
python -m cli login

echo ""
echo "=== Step 2: Create workspace 'my-project' ==="
python -m cli workspaces create my-project

echo ""
echo "=== Step 3: Create API key ==="
python -m cli keys create my-project

echo ""
echo "=== Done. Use the key with: Authorization: Bearer <key> or X-API-Key: <key> ==="
