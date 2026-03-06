import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _repo_root = Path(__file__).resolve().parents[2]
    model_config = SettingsConfigDict(
        env_file=(_repo_root / ".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str
    database_url: str
    default_workspace_id: str
    default_api_key: str  # Dev key to allow/block (e.g. sk-default)
    require_api_key: bool = True  # Overridden by env when not explicitly set
    allow_default_key: bool = False  # Overridden by env when not explicitly set
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_jwt_secret: str | None = None

    @model_validator(mode="after")
    def _apply_env_defaults(self) -> "Settings":
        if "REQUIRE_API_KEY" in os.environ and "ALLOW_DEFAULT_KEY" in os.environ:
            return self
        is_dev = self.env.lower() in ("development", "dev", "local")
        if "REQUIRE_API_KEY" not in os.environ:
            object.__setattr__(self, "require_api_key", not is_dev)
        if "ALLOW_DEFAULT_KEY" not in os.environ:
            object.__setattr__(self, "allow_default_key", is_dev)
        return self


settings = Settings()
