import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Конфигурация приложения"""
    
    # Основные настройки
    APP_NAME: str = "CRM МойСклад Integration"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Окружение
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # База данных PostgreSQL
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres" 
    POSTGRES_DB: str = "crm_dev"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        values = info.data if hasattr(info, 'data') else {}
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@db:5432/{values.get('POSTGRES_DB')}"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # МойСклад API
    MOYSKLAD_TOKEN: str = "your_moysklad_token_here"
    MOYSKLAD_BASE_URL: str = "https://api.moysklad.ru/api/remap/1.2/"
    MOYSKLAD_RATE_LIMIT: int = 5
    MOYSKLAD_BATCH_SIZE: int = 1000
    
    # JWT
    JWT_SECRET: str = "your-super-secret-jwt-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://app-frontend:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # Кеширование
    CACHE_TTL: int = 300
    SYNC_INTERVAL: int = 3600
    
    # Мониторинг
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True
    
    # Файлы
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # API лимиты
    API_RATE_LIMIT: int = 1000
    API_BURST_LIMIT: int = 100
    
    # Локализация
    TIMEZONE: str = "Europe/Moscow"
    LANGUAGE: str = "ru-RU"
    
    # Производительность
    WORKERS_COUNT: int = 4
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Глобальный экземпляр настроек
settings = Settings()

