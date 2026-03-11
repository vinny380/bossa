-- Tier enum: free, pro, owner (owner bypasses limits)
DO $$ BEGIN
    CREATE TYPE tier_type AS ENUM ('free', 'pro', 'owner');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Drop CHECK and default before type change
ALTER TABLE account_tiers ALTER COLUMN tier DROP DEFAULT;
ALTER TABLE account_tiers DROP CONSTRAINT IF EXISTS account_tiers_tier_check;

-- Alter account_tiers to use enum
ALTER TABLE account_tiers
  ALTER COLUMN tier TYPE tier_type
  USING (
    CASE tier::text
      WHEN 'free' THEN 'free'::tier_type
      WHEN 'pro' THEN 'pro'::tier_type
      ELSE 'free'::tier_type
    END
  );

ALTER TABLE account_tiers ALTER COLUMN tier SET DEFAULT 'free'::tier_type;
