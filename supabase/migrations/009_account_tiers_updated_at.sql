-- Auto-update account_tiers.updated_at on row change
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS account_tiers_updated_at ON account_tiers;
CREATE TRIGGER account_tiers_updated_at
  BEFORE UPDATE ON account_tiers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
