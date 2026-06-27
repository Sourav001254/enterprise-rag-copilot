# configs/settings.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # GCP
    GCP_PROJECT_ID: str = "enterprise-rag"
    GCP_REGION: str = "us-central1"

    # Database
    POSTGRES_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db"
    POSTGRES_POOL_MIN: int = 2
    POSTGRES_POOL_MAX: int = 10

    # Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "k8s_docs"

    # Cache
    UPSTASH_REDIS_URL: str = "redis://localhost:6379"
    UPSTASH_REDIS_TOKEN: Optional[str] = None

    # LLM
    OPENAI_API_KEY: str = ""
    PORTKEY_API_KEY: str = ""
    PORTKEY_VIRTUAL_KEY_PRIMARY: str = ""
    GROQ_API_KEY: str = ""
    VOYAGE_API_KEY: Optional[str] = None
    TAVILY_API_KEY: str = ""

    # Auth
    JWT_PUBLIC_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"
    ALLOW_DEV_AUTH: bool = False
    ALLOWED_ORIGINS: list[str] = []

    # Observability
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "enterprise-rag-k8s"
    LOGFIRE_TOKEN: str = ""

    # Ingestion
    UPLOAD_ROOT_DIR: str = "./data/uploads"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNKING_STRATEGY: str = "semantic"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # RAG tuning
    RETRIEVER_TOP_K: int = 20
    RERANKER_TOP_K: int = 5
    CRAG_SCORE_THRESHOLD: float = 0.7
    SELF_RAG_SCORE_THRESHOLD: float = 0.8
    SELF_RAG_MAX_ATTEMPTS: int = 2
    RETRIEVAL_MAX_ATTEMPTS: int = 3
    HYDE_NUM_QUERIES: int = 3

    # Rate limiting
    RATE_LIMIT_PER_USER: int = 20
    TOKEN_BUDGET_DAILY: int = 100000

    # Cache TTLs (seconds)
    CACHE_TTL_EMBEDDING: int = 604800   # 7 days
    CACHE_TTL_INTENT: int = 86400       # 24h
    CACHE_TTL_SQL: int = 86400          # 24h
    CACHE_TTL_SQL_RESULT: int = 900     # 15m
    CACHE_TTL_ANSWER: int = 3600        # 1h
    SEMANTIC_CACHE_THRESHOLD: float = 0.95

    # Cost tracking
    COST_TRACKING_ENABLED: bool = True

settings = Settings()
