from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://asmi:asmi_secret@localhost:5432/asmi"
    secret_key: str = "dev-only-change-me"
    session_cookie_name: str = "asmi_session"
    session_ttl_hours: int = 72
    cors_origins: str = "http://localhost:3000"
    env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ASMI_")


settings = Settings()
