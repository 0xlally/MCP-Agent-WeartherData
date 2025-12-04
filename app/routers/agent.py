"""
AI Agent 专用路由
用于动态调整系统配置
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.database import get_db
from app.models.models import User, SystemConfig
from app.schemas.schemas import (
    SystemConfigCreate,
    SystemConfigResponse,
    SystemConfigUpdate,
    MessageResponse
)
from app.core.security import get_current_admin_user


router = APIRouter(prefix="/agent", tags=["AI Agent"], dependencies=[Depends(get_current_admin_user)])


@router.get("/configs", response_model=List[SystemConfigResponse])
async def list_configs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    获取所有系统配置
    供 AI Agent 读取当前策略
    """
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    return configs


@router.get("/configs/{config_key}", response_model=SystemConfigResponse)
async def get_config(
    config_key: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    根据 key 获取指定配置
    
    **常用配置键：**
    - `crawler_interval`: 爬虫抓取间隔 (秒)
    - `max_data_rows`: 最大数据保留行数
    - `enable_cache`: 是否启用缓存
    """
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config_key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置 '{config_key}' 不存在"
        )
    
    return config


@router.post("/configs", response_model=SystemConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config_data: SystemConfigCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    创建新的系统配置
    
    **示例：**
    ```json
    {
        "key": "crawler_interval",
        "value": "3600",
        "description": "爬虫抓取间隔 (秒)"
    }
    ```
    """
    # 检查配置是否已存在
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config_data.key)
    )
    existing_config = result.scalar_one_or_none()
    
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配置 '{config_data.key}' 已存在，请使用更新接口"
        )
    
    # 创建新配置
    new_config = SystemConfig(
        key=config_data.key,
        value=config_data.value,
        description=config_data.description
    )
    
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    return new_config


@router.put("/configs/{config_key}", response_model=SystemConfigResponse)
async def update_config(
    config_key: str,
    config_update: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    更新系统配置 (AI Agent 核心调用接口)
    
    **用途：** Agent 可根据数据情况动态调整爬虫频率等参数
    
    **示例：**
    ```json
    {
        "value": "7200",
        "description": "调整为2小时抓取一次"
    }
    ```
    """
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config_key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置 '{config_key}' 不存在"
        )
    
    # 更新配置
    config.value = config_update.value
    if config_update.description is not None:
        config.description = config_update.description
    
    await db.commit()
    await db.refresh(config)
    
    return config


@router.delete("/configs/{config_key}", response_model=MessageResponse)
async def delete_config(
    config_key: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """删除系统配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config_key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置 '{config_key}' 不存在"
        )
    
    await db.delete(config)
    await db.commit()
    
    return {"message": f"配置 '{config_key}' 已删除"}


@router.post("/trigger-crawler", response_model=MessageResponse)
async def trigger_crawler(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """
    手动触发爬虫任务
    供 AI Agent 在检测到数据缺口时调用
    
    **注意：** 实际实现需要与爬虫模块集成
    """
    # TODO: 集成实际的爬虫触发逻辑
    # 例如：向消息队列发送任务，或调用爬虫脚本
    
    return {
        "message": "爬虫任务已加入队列",
        "detail": "预计1分钟内开始执行"
    }
