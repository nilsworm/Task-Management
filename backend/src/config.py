from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager"
    backend_port: int = 8000
    # comma-separated list of allowed CORS origins
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    # ISO 4217 currency code used for all cost entries
    cost_currency: str = "EUR"
    import_folder: str = Field(
        default="/app/imports",
        description="Folder path for CSV import files"
    )
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"

    # AI provider selection: "ollama" | "openrouter"
    ai_provider: str = "ollama"
    ai_api_key: str = ""
    # Default free model for OpenRouter; override in .env
    ai_model: str = "meta-llama/llama-3.3-70b-instruct:free"


settings = Settings()
