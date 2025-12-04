"""
天气数据查询路由
需要 API Key 认证
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.models import APIKey, User
from app.schemas.schemas import WeatherQuery, WeatherDataResponse
from app.core.security import verify_api_key


router = APIRouter(prefix="/weather", tags=["天气数据"])


@router.get("/data", response_model=List[WeatherDataResponse])
async def get_weather_data(
    city: str = Query(None, description="城市名称"),
    start_date: str = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=1000, description="返回条数"),
    api_key_data: Tuple[APIKey, User] = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    获取天气数据 (需要 API Key)
    
    **Header 要求：**
    - `X-API-KEY`: 你的 API 密钥
    
    **查询参数：**
    - **city**: 可选，城市名称
    - **start_date**: 可选，开始日期
    - **end_date**: 可选，结束日期
    - **limit**: 返回条数 (1-1000)
    
    **注意：** 当前返回 Mock 数据，后续将集成真实数据库查询
    """
    api_key, user = api_key_data
    
    # TODO: 后续集成真实的 WeatherData 表查询
    # 示例：
    # from app.models.models import WeatherData
    # query = select(WeatherData)
    # if city:
    #     query = query.where(WeatherData.city == city)
    # ...
    
    # 暂时返回 Mock 数据
    mock_data = [
        {
            "city": city or "北京",
            "date": start_date or "2025-12-04",
            "temperature": 15.5,
            "humidity": 65.0,
            "description": "晴转多云"
        },
        {
            "city": city or "北京",
            "date": "2025-12-05",
            "temperature": 12.3,
            "humidity": 70.0,
            "description": "多云"
        }
    ]
    
    return mock_data[:limit]


@router.get("/stats")
async def get_weather_stats(
    api_key_data: Tuple[APIKey, User] = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    获取天气数据统计信息
    
    返回数据总量、支持的城市列表等
    """
    api_key, user = api_key_data
    
    # Mock 统计数据
    return {
        "total_records": 150000,
        "cities": ["北京", "上海", "广州", "深圳"],
        "date_range": {
            "start": "2023-01-01",
            "end": "2025-12-04"
        },
        "user_info": {
            "username": user.username,
            "remaining_quota": api_key.remaining_quota
        }
    }
