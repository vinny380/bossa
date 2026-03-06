"""CLI configuration."""

import os
from pathlib import Path

BOSSA_API_URL = os.environ.get(
    "BOSSA_API_URL",
    "https://filesystem-fawn.vercel.app",
)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

_config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
CREDENTIALS_PATH = Path(_config_home) / "bossa" / "credentials"
