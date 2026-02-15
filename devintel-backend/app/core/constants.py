"""Core application constants to avoid magic numbers and strings."""

# ===========================================
# RATE LIMITING CONSTANTS
# ===========================================
AUTH_RATE_LIMIT = "5/minute"  # Authentication endpoints
CHAT_RATE_LIMIT = "20/minute"  # Chat endpoints
INDEXING_RATE_LIMIT = "3/minute"  # Repository indexing
API_GLOBAL_RATE_LIMIT = "100/minute"  # Global rate limit

# ===========================================
# CACHE TTL (Time To Live) CONSTANTS
# ===========================================
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour
CACHE_TTL_EMBEDDING = 7200  # 2 hours for embedding results

# ===========================================
# DATABASE QUERY CONSTANTS
# ===========================================
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
DEFAULT_SKIP = 0

# ===========================================
# RAG PIPELINE CONSTANTS
# ===========================================
DEFAULT_CHUNK_SIZE = 700
DEFAULT_CHUNK_OVERLAP = 120
DEFAULT_TOP_K = 6
MAX_CONTEXT_CHUNKS = 10
EMBEDDING_DIMENSIONS = 1536

# ===========================================
# FILE PROCESSING CONSTANTS
# ===========================================
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".rb",
    ".md", ".json", ".yaml", ".yml",
    ".c", ".cpp", ".h", ".hpp",
    ".cs", ".php", ".swift", ".kt"
}

IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build",
    "venv", ".venv", "__pycache__", ".pytest_cache",
    "vendor", "target", ".next", "out"
}

# ===========================================
# SECURITY CONSTANTS
# ===========================================
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# ===========================================
# TOKEN EXPIRY CONSTANTS
# ===========================================
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
GITHUB_TOKEN_REFRESH_BUFFER_HOURS = 24

# ===========================================
# REQUEST SIZE LIMITS
# ===========================================
MAX_REQUEST_SIZE_MB = 10
MAX_REQUEST_SIZE_BYTES = MAX_REQUEST_SIZE_MB * 1024 * 1024

# ===========================================
# OPENAI API CONSTANTS
# ===========================================
DEFAULT_OPENAI_MODEL = "gpt-4-turbo-preview"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7

# ===========================================
# HTTP STATUS MESSAGE CONSTANTS
# ===========================================
MSG_UNAUTHORIZED = "Authentication required"
MSG_FORBIDDEN = "Access forbidden"
MSG_NOT_FOUND = "Resource not found"
MSG_INTERNAL_ERROR = "Internal server error"
MSG_VALIDATION_ERROR = "Validation error"
MSG_RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
