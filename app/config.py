import os
from typing import List
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Bot configuration
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    WEBHOOK_URL: str = Field("", env="WEBHOOK_URL")
    WEBHOOK_SECRET: str = Field("", env="WEBHOOK_SECRET")
    
    # Database configuration
    MONGO_HOST: str = Field("mongodb", env="MONGO_HOST")
    MONGO_PORT: int = Field(27017, env="MONGO_PORT")
    MONGO_DB_NAME: str = Field("fok_bot", env="MONGO_DB_NAME")
    MONGO_USERNAME: str = Field("", env="MONGO_USERNAME")
    MONGO_PASSWORD: str = Field("", env="MONGO_PASSWORD")
    
    # Redis configuration
    REDIS_HOST: str = Field("redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field("", env="REDIS_PASSWORD")
    
    # Celery configuration
    CELERY_BROKER_URL: str = Field("redis://redis:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://redis:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Admin configuration
    ADMIN_CHAT_ID: int = Field(0, env="ADMIN_CHAT_ID")
    SUPER_ADMIN_IDS: str = Field("", env="SUPER_ADMIN_IDS")
    
    # Application settings
    DEBUG: bool = Field(False, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    MAX_ITEMS_PER_PAGE: int = Field(10, env="MAX_ITEMS_PER_PAGE")
    RATE_LIMIT_REQUESTS: int = Field(30, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(60, env="RATE_LIMIT_WINDOW")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def mongo_url(self) -> str:
        """Build MongoDB connection URL"""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB_NAME}"
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB_NAME}"
    
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    @property
    def super_admin_ids_list(self) -> List[int]:
        """Get list of super admin IDs"""
        if not self.SUPER_ADMIN_IDS:
            return []
        return [int(admin_id.strip()) for admin_id in self.SUPER_ADMIN_IDS.split(",") if admin_id.strip().isdigit()]


# Global settings instance
settings = Settings()