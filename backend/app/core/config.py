"""
Application configuration management.
Handles environment variables and application settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Book Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DATABASE_TEST_URL: Optional[str] = None

    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT encoding")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenRouter (Llama3)
    OPENROUTER_API_KEY: str = Field(..., description="OpenRouter API key")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLAMA_MODEL: str = "meta-llama/llama-3-8b-instruct"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is properly formatted."""
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is set and secure."""
        if not v or v == "your-secret-key-here-change-in-production":
            raise ValueError("SECRET_KEY must be set to a secure value")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
