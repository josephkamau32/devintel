import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Demo mode — allows one-click demo login for portfolio demos
    DEMO_MODE: bool = True

    # Redis
    REDIS_URL: str | None = None
    REDIS_POOL_SIZE: int = 10
    REDIS_CACHE_TTL: int = 3600

    # Rate limiting (per-user, per-minute)
    RATE_LIMIT_PER_MINUTE: int = 100

    # Indexing / Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_MODE: str = "vector"
    TOP_K_CHUNKS: int = 10
    IGNORED_DIRECTORIES: list[str] = ["node_modules", ".git", "venv", ".venv", "__pycache__", "build", "dist"]
    SUPPORTED_FILE_EXTENSIONS: list[str] = [".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".html", ".css", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp"]
    MAX_FILE_SIZE_MB: int = 5

    # Job Poller
    JOB_POLL_INTERVAL_SECONDS: float = 2.0
    JOB_POLLER_CONCURRENCY: int = 3

    # Webhooks
    # Default empty → webhook validation will reject requests unless explicitly configured
    GITHUB_WEBHOOK_SECRET: str = ""

    # CORS — stored as JSON string in env: '["http://localhost:5173"]' or comma-separated string
    CORS_ORIGINS: str | list[str] = ["http://localhost:5173"]

    # Frontend URL — used to build redirect URLs after OAuth (must NOT end with /)
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v):
        from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

        # Render provides postgres://, we need postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        parsed = urlparse(v)
        if parsed.query:
            query = dict(parse_qsl(parsed.query))
            if "sslmode" in query:
                query["ssl"] = query.pop("sslmode")
            query.pop("channel_binding", None)

            new_query = urlencode(query)
            parsed = parsed._replace(query=new_query)
            v = urlunparse(parsed)

        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use postgresql+asyncpg:// driver. "
                "Example: postgresql+asyncpg://user:pass@host/dbname"
            )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        if "*" in v:
            raise ValueError("Wildcard CORS origins are forbidden")
        return [origin.rstrip("/") for origin in v]


settings = Settings()
