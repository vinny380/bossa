-- Link workspaces to Supabase Auth users (user_id = auth.users.id)
-- No FK for local Postgres compat; add FK manually on Supabase: REFERENCES auth.users(id)
ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS user_id UUID;

-- Soft revocation for API keys
ALTER TABLE workspace_api_keys ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON workspaces(user_id);
