"""
Application configuration using Pydantic Settings
"""
import json
from typing import List, Optional, Union
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0", description="Redis URL")
    
    # MoySklad API
    MOYSKLAD_TOKEN: Optional[str] = Field(default=None, description="MoySklad API token")
    
    # JWT Authentication
    JWT_SECRET: str = Field(default="replace_me_with_strong_secret_key", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=1440, description="JWT expiration in minutes")
    
    # Sentry
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    
    # Application
    APP_ENV: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from either comma-separated string or JSON array"""
        if v is None:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                else:
                    return [v]
            except json.JSONDecodeError:
                # If JSON parsing fails, split by comma
                return [origin.strip() for origin in v.split(',') if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Cache
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds")
    SYNC_INTERVAL: int = Field(default=3600, description="Sync interval in seconds")
    
    # MoySklad API settings
    MOYSKLAD_BASE_URL: str = Field(
        default="https://api.moysklad.ru/api/remap/1.2",
        description="MoySklad API base URL"
    )
    MOYSKLAD_RATE_LIMIT: int = Field(default=100, description="MoySklad rate limit per 5 seconds")
    MOYSKLAD_BATCH_SIZE: int = Field(default=1000, description="MoySklad batch size for requests")
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
