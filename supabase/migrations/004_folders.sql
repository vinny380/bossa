-- Folders table: explicit hierarchy with parent_id and depth
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0 CHECK (depth >= 0 AND depth <= 50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(workspace_id, path)
);

CREATE INDEX idx_folders_workspace_path ON folders(workspace_id, path);
CREATE INDEX idx_folders_parent ON folders(parent_id);
CREATE INDEX idx_folders_depth ON folders(workspace_id, depth);

-- Root folder for default workspace (path="/", name="", parent_id=NULL, depth=0)
INSERT INTO folders (id, workspace_id, parent_id, name, path, depth)
VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000001',
    NULL,
    '',
    '/',
    0
);

-- Add folder_id and name to files
ALTER TABLE files ADD COLUMN folder_id UUID REFERENCES folders(id) ON DELETE CASCADE;
ALTER TABLE files ADD COLUMN name TEXT;
