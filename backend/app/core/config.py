"""Application configuration settings using Pydantic Settings."""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings and environment variables."""

    # Project metadata
    PROJECT_NAME: str = "VantageAI Technical Screening Engine"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./screening_system.db"

    # AI / LLM Configuration
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    PRIMARY_LLM_PROVIDER: str = "auto"  # 'gemini', 'openai', 'heuristic' or 'auto'
    DEFAULT_GEMINI_MODEL: str = "gemini-1.5-flash"
    DEFAULT_OPENAI_MODEL: str = "gpt-4o-mini"

    # RAG & Knowledge Base
    KNOWLEDGE_BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent / "knowledge_base"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    RAG_CHUNK_SIZE: int = 450
    RAG_CHUNK_OVERLAP: int = 80
    RAG_TOP_K: int = 3

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
