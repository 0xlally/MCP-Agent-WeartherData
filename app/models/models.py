"""
数据库 ORM 模型
定义用户、API Key、系统配置表、天气数据表
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import secrets


class User(Base):
    """用户表 - 区分管理员和普通用户"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 角色：admin/user
    role = Column(String(20), default="user", nullable=False)
    
    # 账号状态
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系：一个用户可以拥有多个 API Key
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class APIKey(Base):
    """API Key 表 - 用于外部鉴权"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # API 密钥 (如 "sk-abc123...")
    access_key = Column(String(100), unique=True, index=True, nullable=False)
    
    # 剩余调用额度
    remaining_quota = Column(Integer, default=1000, nullable=False)
    
    # 密钥状态
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 备注信息
    description = Column(String(200), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系：反向引用用户
    user = relationship("User", back_populates="api_keys")
    
    @staticmethod
    def generate_key(prefix: str = "sk-") -> str:
        """生成随机 API Key"""
        return f"{prefix}{secrets.token_urlsafe(32)}"
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, key={self.access_key[:20]}..., quota={self.remaining_quota})>"


class SystemConfig(Base):
    """系统配置表 - 供 AI Agent 动态调整"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 配置键 (如 "crawler_interval", "max_data_rows")
    key = Column(String(100), unique=True, index=True, nullable=False)
    
    # 配置值 (JSON 字符串或纯文本)
    value = Column(Text, nullable=False)
    
    # 配置描述
    description = Column(String(300), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value[:50]})>"


class WeatherData(Base):
    """天气数据表 - 存储历史天气记录"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 城市名称
    city = Column(String(50), nullable=False, index=True)
    
    # 日期 (Date 类型，只存储日期不含时间)
    date = Column(Date, nullable=False, index=True)
    
    # 天气状况描述 (如 "晴 / 多云")
    weather_condition = Column(String(100), nullable=False)
    
    # 最低温度 (摄氏度)
    temp_min = Column(Float, nullable=False)
    
    # 最高温度 (摄氏度)
    temp_max = Column(Float, nullable=False)
    
    # 原始气温字符串 (如 "6℃-15℃")
    temp_raw = Column(String(50), nullable=True)
    
    # 风力风向描述
    wind_info = Column(String(200), nullable=False)
    
    # 数据导入时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 复合索引：city + date (用于快速查询特定城市的历史数据)
    __table_args__ = (
        Index('idx_city_date', 'city', 'date'),
    )
    
    def __repr__(self):
        return f"<WeatherData(city={self.city}, date={self.date}, temp={self.temp_min}~{self.temp_max}℃)>"
