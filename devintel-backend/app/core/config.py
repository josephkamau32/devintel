from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "DevIntel AI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption (Fernet key for GitHub tokens)
    TOKEN_ENCRYPTION_KEY: str

    # CSRF
    SECRET_KEY: str

    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_CHAT_MODEL: str = "gpt-4o"

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Redis
    REDIS_URL: str | None = None
    REDIS_POOL_SIZE: int = 10
    REDIS_CACHE_TTL: int = 3600

    # Indexing / Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_MODE: str = "vector"
    TOP_K_CHUNKS: int = 10
    IGNORED_DIRECTORIES: List[str] = ["node_modules", ".git", "venv", ".venv", "__pycache__", "build", "dist"]
    SUPPORTED_FILE_EXTENSIONS: List[str] = [".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".html", ".css", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp"]
    MAX_FILE_SIZE_MB: int = 5

    # Webhooks
    GITHUB_WEBHOOK_SECRET: str = "default_secret"

    # CORS — stored as JSON string in env: '["http://localhost:5173"]'
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v):
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use postgresql+asyncpg:// driver. "
                "Example: postgresql+asyncpg://user:pass@host/dbname"
            )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        if "*" in v:
            raise ValueError("Wildcard CORS origins are forbidden")
        return [origin.rstrip("/") for origin in v]


settings = Settings()
