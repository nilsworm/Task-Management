from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    cost_currency: str = "EUR"
    root_path: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"
    ai_provider: str = "ollama"
    ai_api_key: str = ""
    ai_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    own_account_ibans: list[str] = []

    @field_validator("own_account_ibans", mode="before")
    @classmethod
    def parse_ibans(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [i.strip().upper() for i in v.split(",") if i.strip()]
        return [i.upper() for i in v]


settings = Settings()
