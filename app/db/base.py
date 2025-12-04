"""
导入所有模型以便 Alembic 自动检测
"""
from app.db.database import Base
from app.models.models import User, APIKey, SystemConfig

__all__ = ["Base", "User", "APIKey", "SystemConfig"]
