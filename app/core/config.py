from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration and RAG pipeline settings."""
    APP_NAME: str = "AI Customer Support Coaching Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    # Relational Database
    DATABASE_URL: str = "sqlite:///./support_coaching.db"

    # ChromaDB Vector Storage
    CHROMA_PERSIST_DIR: str = "./chroma_storage"
    CHROMA_COLLECTION_NAME: str = "kb_chunks"

    # RAG Settings (Configurable per Section 2 & 8 of Design Doc)
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE_TOKENS: int = 220
    CHUNK_OVERLAP_TOKENS: int = 40
    MAX_CHUNK_TOKENS: int = 240
    RETRIEVAL_TOP_K: int = 4
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.35

    # LLM Settings (Placeholders for Milestone 2)
    LLM_PROVIDER: str = "none"
    LLM_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
