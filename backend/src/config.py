from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _repo_root = Path(__file__).resolve().parents[2]
    model_config = SettingsConfigDict(
        env_file=(_repo_root / ".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    database_url: str
    default_workspace_id: str = "00000000-0000-0000-0000-000000000001"
    require_api_key: bool = True  # False allows anonymous access (dev/test only)
    allow_default_key: bool = (
        False  # True allows sk-default (local/test only); block in prod
    )
    supabase_url: str | None = None  # For JWT validation (control plane)
    supabase_jwt_secret: str | None = None  # JWT secret from Supabase project settings


settings = Settings()
