-- Add FK from workspaces.user_id to auth.users (Supabase only; skips if auth.users missing)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'auth' AND table_name = 'users'
  ) THEN
    -- Null out user_ids that don't exist in auth.users (e.g. test data)
    UPDATE workspaces w
    SET user_id = NULL
    WHERE w.user_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM auth.users u WHERE u.id = w.user_id);

    ALTER TABLE workspaces
      ADD CONSTRAINT workspaces_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
  END IF;
EXCEPTION
  WHEN duplicate_object THEN NULL;  -- Constraint already exists
END $$;
