from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager"
    backend_port: int = 8000
    # comma-separated list of allowed CORS origins
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    # ISO 4217 currency code used for all cost entries
    cost_currency: str = "EUR"


settings = Settings()
