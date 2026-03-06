CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(workspace_id, path)
);

-- Core indexes
CREATE INDEX idx_files_workspace_path ON files(workspace_id, path);
CREATE INDEX idx_files_content_trgm ON files USING gin(content gin_trgm_ops);
CREATE INDEX idx_files_content_fts ON files USING gin(to_tsvector('english', content));
CREATE INDEX idx_files_metadata ON files USING gin(metadata);

-- Seed default workspace
INSERT INTO workspaces (id, name) VALUES ('00000000-0000-0000-0000-000000000001', 'default');
