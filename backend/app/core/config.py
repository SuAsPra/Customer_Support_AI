from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///./data/app.db"

    llm_provider: str = "none"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "all-MiniLM-L6-v2"

    chroma_persist_dir: str = "./data/chroma"
    chunk_size: int = 450  # token target (approximated)
    chunk_overlap: int = 60
    retrieval_top_k: int = 5

    upload_dir: str = "./data/uploads"

    @property
    def base_dir(self) -> Path:
        # backend/app/core/config.py -> backend
        return Path(__file__).resolve().parents[2]


settings = Settings()
