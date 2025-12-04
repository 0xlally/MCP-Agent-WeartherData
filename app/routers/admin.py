"""
管理员专用路由
用户管理、API Key 生成
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.database import get_db
from app.models.models import User, APIKey
from app.schemas.schemas import (
    UserResponse, 
    UserUpdate,
    APIKeyCreate, 
    APIKeyResponse,
    APIKeyUpdate,
    MessageResponse
)
from app.core.security import get_current_admin_user, get_password_hash
from app.core.config import settings


router = APIRouter(prefix="/admin", tags=["管理员"], dependencies=[Depends(get_current_admin_user)])


# ========== 用户管理 ==========

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """获取所有用户列表"""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """根据 ID 获取用户详情"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    更新用户信息 (密码、状态)
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新字段
    if user_update.password is not None:
        user.hashed_password = get_password_hash(user_update.password)
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """删除用户 (级联删除其所有 API Key)"""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": f"用户 {user.username} 已删除"}


# ========== API Key 管理 ==========

@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    为指定用户生成新的 API Key
    
    - **user_id**: 目标用户 ID
    - **quota**: 初始额度
    - **description**: 备注
    """
    # 验证用户是否存在
    result = await db.execute(
        select(User).where(User.id == key_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标用户不存在"
        )
    
    # 生成新的 API Key
    new_key = APIKey(
        user_id=key_data.user_id,
        access_key=APIKey.generate_key(settings.API_KEY_PREFIX),
        remaining_quota=key_data.quota,
        description=key_data.description,
        is_active=True
    )
    
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    return new_key


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    获取所有 API Key (可按用户筛选)
    
    - **user_id**: 可选，筛选指定用户的 Key
    """
    query = select(APIKey)
    
    if user_id is not None:
        query = query.where(APIKey.user_id == user_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    api_keys = result.scalars().all()
    
    return api_keys


@router.patch("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    key_update: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    更新 API Key (额度、状态)
    """
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )
    
    # 更新字段
    if key_update.remaining_quota is not None:
        api_key.remaining_quota = key_update.remaining_quota
    
    if key_update.is_active is not None:
        api_key.is_active = key_update.is_active
    
    await db.commit()
    await db.refresh(api_key)
    
    return api_key


@router.delete("/api-keys/{key_id}", response_model=MessageResponse)
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """删除 API Key"""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )
    
    await db.delete(api_key)
    await db.commit()
    
    return {"message": f"API Key {api_key.access_key} 已删除"}
