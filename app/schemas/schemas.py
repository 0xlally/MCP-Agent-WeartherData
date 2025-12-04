"""
Pydantic 数据验证模型
用于 API 请求/响应的数据验证和序列化
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ========== 用户相关 Schema ==========

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")


class UserCreate(UserBase):
    """用户注册"""
    password: str = Field(..., min_length=6, description="密码，至少6位")
    role: str = Field(default="user", description="角色: admin/user")


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """用户更新"""
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


# ========== JWT Token 相关 ==========

class Token(BaseModel):
    """JWT Token 响应"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token 解析后的数据"""
    username: Optional[str] = None
    role: Optional[str] = None


# ========== API Key 相关 Schema ==========

class APIKeyBase(BaseModel):
    """API Key 基础模型"""
    description: Optional[str] = Field(None, max_length=200, description="密钥备注")


class APIKeyCreate(APIKeyBase):
    """创建 API Key (管理员为用户生成)"""
    user_id: int = Field(..., description="所属用户ID")
    quota: int = Field(default=1000, ge=0, description="初始额度")


class APIKeyResponse(APIKeyBase):
    """API Key 响应模型"""
    id: int
    user_id: int
    access_key: str
    remaining_quota: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyUpdate(BaseModel):
    """更新 API Key"""
    remaining_quota: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


# ========== 系统配置相关 Schema ==========

class SystemConfigBase(BaseModel):
    """系统配置基础模型"""
    key: str = Field(..., min_length=1, max_length=100, description="配置键")
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, max_length=300, description="配置描述")


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置"""
    pass


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class SystemConfigUpdate(BaseModel):
    """更新系统配置"""
    value: str = Field(..., description="新的配置值")
    description: Optional[str] = None


# ========== 天气数据相关 Schema (暂时 Mock) ==========

class WeatherQuery(BaseModel):
    """天气数据查询参数"""
    city: Optional[str] = Field(None, description="城市名称")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    limit: int = Field(default=100, ge=1, le=1000, description="返回条数")


class WeatherDataResponse(BaseModel):
    """天气数据响应 (Mock 结构)"""
    city: str
    date: str
    temperature: float
    humidity: float
    description: str


# ========== 通用响应模型 ==========

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int
    page: int
    page_size: int
    data: list
