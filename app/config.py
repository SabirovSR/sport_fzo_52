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
    
    # Cluster configuration
    BOT_INSTANCE_ID: str = Field("1", env="BOT_INSTANCE_ID")
    WORKER_ID: str = Field("1", env="WORKER_ID")
    
    # Admin configuration
    ADMIN_CHAT_ID: int = Field(0, env="ADMIN_CHAT_ID")
    SUPER_ADMIN_IDS: str = Field("", env="SUPER_ADMIN_IDS")
    
    # Application settings
    DEBUG: bool = Field(False, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    MAX_ITEMS_PER_PAGE: int = Field(10, env="MAX_ITEMS_PER_PAGE")
    RATE_LIMIT_REQUESTS: int = Field(30, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(60, env="RATE_LIMIT_WINDOW")
    
    # Monitoring settings
    SENTRY_DSN: str = Field("", env="SENTRY_DSN")
    APP_VERSION: str = Field("1.0.0", env="APP_VERSION")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def mongo_url(self) -> str:
        """Build MongoDB connection URL"""
        # Handle multiple hosts (replica set)
        if ',' in self.MONGO_HOST:
            hosts = self.MONGO_HOST
        else:
            hosts = f"{self.MONGO_HOST}:{self.MONGO_PORT}"
        
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{hosts}/{self.MONGO_DB_NAME}?authSource=admin"
        return f"mongodb://{hosts}/{self.MONGO_DB_NAME}"
    
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL"""
        # Handle multiple hosts (cluster mode)
        if ',' in self.REDIS_HOST:
            # For Redis Cluster, return the first node
            first_host = self.REDIS_HOST.split(',')[0]
            host_port = first_host.split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else self.REDIS_PORT
        else:
            host = self.REDIS_HOST
            port = self.REDIS_PORT
        
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{host}:{port}/0"
        return f"redis://{host}:{port}/0"
    
    @property
    def redis_cluster_nodes(self) -> list:
        """Get Redis cluster nodes"""
        if ',' in self.REDIS_HOST:
            nodes = []
            for host_port in self.REDIS_HOST.split(','):
                host_port_parts = host_port.split(':')
                host = host_port_parts[0]
                port = int(host_port_parts[1]) if len(host_port_parts) > 1 else self.REDIS_PORT
                nodes.append(f"{host}:{port}")
            return nodes
        return [f"{self.REDIS_HOST}:{self.REDIS_PORT}"]
    
    @property
    def super_admin_ids_list(self) -> List[int]:
        """Get list of super admin IDs"""
        if not self.SUPER_ADMIN_IDS:
            return []
        return [int(admin_id.strip()) for admin_id in self.SUPER_ADMIN_IDS.split(",") if admin_id.strip().isdigit()]


# Global settings instance
settings = Settings()