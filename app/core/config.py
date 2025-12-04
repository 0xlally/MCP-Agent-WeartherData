"""
核心配置管理
使用 Pydantic Settings 管理环境变量
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "Weather Data Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/weather_db"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"  # 生产环境请务必更换
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    # API Key 配置
    API_KEY_PREFIX: str = "sk-"
    DEFAULT_QUOTA: int = 1000  # 默认额度
    
    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
