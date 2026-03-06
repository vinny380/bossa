-- API keys for workspace access. Key is stored as SHA-256 hash.
CREATE TABLE IF NOT EXISTS workspace_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(key_hash)
);

CREATE INDEX IF NOT EXISTS idx_workspace_api_keys_hash ON workspace_api_keys(key_hash);

-- Seed a key for the default workspace (hash of "sk-default" for dev)
-- In production, generate with: openssl rand -hex 32
INSERT INTO workspace_api_keys (workspace_id, key_hash, name)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    encode(sha256(convert_to('sk-default', 'UTF8')), 'hex'),
    'default'
)
ON CONFLICT (key_hash) DO NOTHING;
