-- Add FK from usage_daily.user_id to auth.users (matches migration 005 intent)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'auth' AND table_name = 'users'
  ) THEN
    -- Delete orphan rows (user_id not in auth.users) before adding FK
    DELETE FROM usage_daily ud
    WHERE NOT EXISTS (SELECT 1 FROM auth.users u WHERE u.id = ud.user_id);

    ALTER TABLE usage_daily
      ADD CONSTRAINT usage_daily_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
  END IF;
EXCEPTION
  WHEN duplicate_object THEN NULL;  -- Constraint already exists
END $$;
