"""
安全认证模块
实现 JWT 登录认证 和 API Key 验证
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid
import hmac
from sqlalchemy import update
from jose import JWTError, jwt

#变更说明
# 下面导入的模块用于增强 JWT 与 API Key 的安全性：
# - `uuid`：生成每个 JWT 的 `jti`（唯一标识符），便于将来实现 token 撤销、审计或去重。
# - `hmac`：使用 `hmac.compare_digest` 做常量时间比较，减少时间侧信道泄露（用于比较 API Key）。
# - `sqlalchemy.update`：用于执行原子性更新（在 API Key 额度扣减时使用），可减少并发竞态导致的超扣或负数额度问题。
#
# 说明：这些改进均限定在本文件内（仅修改本模块），以降低改动范围与回归风险；如果需要更强的保证（例如
# 把 API Key 存为哈希、或添加持久化的撤销表），则需要跨文件/数据库的更改。

from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.database import get_db
from app.models.models import User, APIKey
from app.schemas.schemas import TokenData


#密码加密配置 
# （修改）使用 Argon2 提升密码哈希安全性（需要在 requirements 中安装 passlib[argon2]）
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

#OAuth2 配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


#密码哈希工具

def get_password_hash(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


#JWT Token 管理

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
    
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # （修改）标准化声明：过期时间（exp）、颁发时间（iat）和唯一 id（jti）
    # 安全理由：
    # - `iat`（Issued At）可用于检测 token 的颁发时间和审计；
    # - `jti`（JWT ID）为 token 提供全局唯一标识，便于将来实现基于 jti 的撤销列表或一次性刷新策略；
    # - 在验证和审计流程中记录 jti 可以帮助发现重复使用或回放攻击。
    # 注意：此处只是在 token 中设置 jti/iat，本身不实现撤销逻辑；需要额外的存储（内存/DB）来跟踪被撤销的 jti。
    iat = now_utc
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "iat": iat, "jti": jti})

    # 签名说明：使用配置的算法进行签名。务必在生产中确保：
    # - settings.ALGORITHM 与使用的密钥类型匹配（HS256 对称、RS256 非对称），
    # - SECRET_KEY / 私钥以安全方式存放（环境变量/密钥管理服务），不要将密钥写入源码库。
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
        # （修改）变更说明：增强对 JWT header 中 alg 字段的验证，防止算法混淆攻击
        # 先解析 header 并确保 alg 与配置一致，防止 alg 混淆攻击（algorithm confusion attack）
        # 背景：攻击者可能构造一个使用不同算法（例如将 alg 改为 "none" 或从 RS 改为 HS）且被服务器误接受的 token。
        # 为降低风险，这里在解码签名前检查 token header 的 `alg` 字段与服务期望的 `settings.ALGORITHM` 完全匹配。
        # 备注：该检查可以阻止常见的 alg 混淆攻击，但并不能替代正确的密钥管理（例如确保私钥/公钥与算法一致）。
        try:
            unverified_header = jwt.get_unverified_header(token)
            header_alg = unverified_header.get("alg")
        except Exception:
            header_alg = None

        if header_alg is None or header_alg.upper() != settings.ALGORITHM.upper():
            # 如果 header 中没有 alg 或与配置不符，则直接拒绝，返回 401
            raise credentials_exception

        # 解析并验证签名：使用配置的算法和密钥进行验证
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
    # 查询 API Key（基于明文存储的现状）
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

    # （修改）使用常量时间比较以减少时间侧信道泄露
    if not hmac.compare_digest(str(api_key.access_key), str(x_api_key)):
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
    
    # （修改）尝试以原子方式扣减额度以避免并发竞态
    if api_key.remaining_quota <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API Key 额度已用尽，请联系管理员充值"
        )

    stmt = (
        update(APIKey)
        .where(APIKey.id == api_key.id, APIKey.remaining_quota > 0)
        .values(remaining_quota=APIKey.remaining_quota - 1, last_used_at=datetime.now(timezone.utc))
    )
    res = await db.execute(stmt)
    await db.commit()
    # res.rowcount 可能受驱动影响，若为0则说明并发导致扣减失败/额度已被其他请求消耗
    try:
        rowcount = res.rowcount
    except Exception:
        rowcount = None
    if rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API Key 并发扣减失败或额度已用尽"
        )
    
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
