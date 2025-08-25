import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, validator, SecretStr


class Settings(BaseSettings):
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Application settings
    PROJECT_NAME: str = "Samoey Copilot"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    API_V1_STR: str = "/api/v1"
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "Samoey Copilot API"
    API_DESCRIPTION: str = "AI-Powered Development Assistant"
    API_VERSION: str = "1.0.0"

    # Security - CRITICAL: Changed defaults
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production-minimum-32-chars")
    ALGORITHM: str = "HS256"  # Added missing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # CORS - More restrictive defaults
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return ["http://localhost:3000", "http://localhost:8000"]  # Default localhost only

    # Database - More secure defaults
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")  # Empty by default, must be set
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "samoey_copilot")
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        if not values.get("POSTGRES_PASSWORD"):
            raise ValueError("POSTGRES_PASSWORD must be set in environment")
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_URL: Optional[RedisDsn] = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        password_part = f":{values.get('REDIS_PASSWORD')}@" if values.get("REDIS_PASSWORD") else ""
        return f"redis://{password_part}{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"

    # AI/ML
    HUGGINGFACE_TOKEN: Optional[SecretStr] = None
    OPENAI_API_KEY: Optional[SecretStr] = None
    AI_MODEL_PATH: str = os.getenv("AI_MODEL_PATH", "models/")
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "data/vector_store")

    # Security settings
    SECURITY_ENABLED: bool = True
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = None

    # Monitoring
    SENTRY_DSN: Optional[SecretStr] = None
    PROMETHEUS_ENABLED: bool = True
    ENABLE_METRICS: bool = True
    METRICS_PREFIX: str = "samoey_copilot"

    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", None)
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[SecretStr] = None
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL", None)
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME", None)

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".py", ".js", ".ts", ".json", ".yml", ".yaml", ".md", ".txt"]

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    RELOAD: bool = os.getenv("RELOAD", "false").lower() == "true"

    # Admin settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_DEFAULT_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "change-me-in-production")

    # Monitoring settings
    MONITORING_INTERVAL: int = 5  # seconds
    ALERT_THRESHOLD_CPU: float = 80.0  # percentage
    ALERT_THRESHOLD_MEMORY: float = 85.0  # percentage
    ALERT_THRESHOLD_DISK: float = 90.0  # percentage

    # Websocket
    WS_MESSAGE_QUEUE_SIZE: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds

    class Config:
        case_sensitive = True
        env_file = ".env"
        secrets_dir = "/run/secrets"  # For Docker secrets


settings = Settings()
