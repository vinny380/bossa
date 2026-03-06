from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
    )
    database_url: str
    default_workspace_id: str = "00000000-0000-0000-0000-000000000001"


settings = Settings()
