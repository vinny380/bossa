-- workspace_api_keys: cascade deletes + list keys by workspace
CREATE INDEX IF NOT EXISTS idx_workspace_api_keys_workspace_id
  ON workspace_api_keys(workspace_id);

-- Partial index for active keys only (list-keys hot path)
CREATE INDEX IF NOT EXISTS idx_workspace_api_keys_workspace_active
  ON workspace_api_keys(workspace_id) WHERE revoked_at IS NULL;

-- files: cascade when folder deleted
CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id);

-- Remove redundant index (PK on user_id, date already provides it)
DROP INDEX IF EXISTS idx_usage_daily_user_date;
