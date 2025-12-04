"""
安全认证模块
实现 JWT 登录认证 和 API Key 验证
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.database import get_db
from app.models.models import User, APIKey
from app.schemas.schemas import TokenData


# ========== OAuth2 配置 ==========
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ========== 密码哈希工具 (直接使用 bcrypt) ==========

def get_password_hash(password: str) -> str:
    """加密密码 (bcrypt 限制最长 72 字节)"""
    # 确保密码不超过 72 字节
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # 使用 bcrypt 生成密码哈希
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ========== JWT Token 管理 ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Token
    
    Args:
        data: 要编码的数据字典 (通常包含 username, role)
        expires_delta: 过期时间增量
    
    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


async def decode_access_token(token: str) -> TokenData:
    """
    解析 JWT Token
    
    Args:
        token: JWT Token 字符串
    
    Returns:
        TokenData 包含用户名和角色
    
    Raises:
        HTTPException: Token 无效或过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None:
            raise credentials_exception
        
        return TokenData(username=username, role=role)
    
    except JWTError:
        raise credentials_exception


# ========== 用户认证依赖 ==========

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    从 JWT Token 获取当前登录用户
    用于需要登录认证的路由
    """
    token_data = await decode_access_token(token)
    
    result = await db.execute(
        select(User).where(User.username == token_data.username)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    验证当前用户是否为管理员
    用于需要管理员权限的路由
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# ========== API Key 验证依赖 ==========

async def verify_api_key(
    x_api_key: str = Header(..., description="API 密钥"),
    db: AsyncSession = Depends(get_db)
) -> Tuple[APIKey, User]:
    """
    验证 API Key 的有效性和额度
    用于需要 API Key 认证的公开接口 (如 /weather)
    
    Args:
        x_api_key: 请求头中的 X-API-KEY
        db: 数据库会话
    
    Returns:
        (APIKey对象, User对象) 元组
    
    Raises:
        HTTPException: API Key 无效、额度不足或已禁用
    """
    # 查询 API Key
    result = await db.execute(
        select(APIKey).where(APIKey.access_key == x_api_key)
    )
    api_key = result.scalar_one_or_none()
    
    # 验证 API Key 是否存在
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 无效"
        )
    
    # 验证 API Key 是否激活
    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key 已被禁用"
        )
    
    # 验证剩余额度
    if api_key.remaining_quota <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API Key 额度已用尽，请联系管理员充值"
        )
    
    # 获取关联用户
    result = await db.execute(
        select(User).where(User.id == api_key.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="关联用户不存在或已禁用"
        )
    
    # 扣减额度
    api_key.remaining_quota -= 1
    api_key.last_used_at = datetime.utcnow()
    await db.commit()
    
    return api_key, user


async def verify_admin_or_system_key(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    验证用户是管理员或系统级别 Key
    用于 AI Agent 专用接口
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员或系统 Agent 可访问"
        )
    return current_user
