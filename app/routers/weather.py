"""
天气数据查询路由
需要 API Key 认证
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.models import APIKey, User, WeatherData
from app.schemas.schemas import WeatherDataResponse
from app.core.security import verify_api_key


router = APIRouter(prefix="/weather", tags=["天气数据"])


@router.get("/data")
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
    - **start_date**: 可选，开始日期 (YYYY-MM-DD)
    - **end_date**: 可选，结束日期 (YYYY-MM-DD)
    - **limit**: 返回条数 (1-1000)
    
    **返回示例：**
    ```json
    [
        {
            "city": "昆明",
            "date": "2016-01-01",
            "weather_condition": "小到中雨 / 阵雨",
            "temp_min": 6.0,
            "temp_max": 15.0,
            "wind_info": "无持续风向 ≤3级 / 无持续风向 ≤3级"
        }
    ]
    ```
    """
    api_key, user = api_key_data
    
    # 构建查询
    query = select(WeatherData)
    
    # 按城市筛选
    if city:
        query = query.where(WeatherData.city == city)
    
    # 按日期范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.where(WeatherData.date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.where(WeatherData.date <= end)
        except ValueError:
            pass
    
    # 排序和限制
    query = query.order_by(WeatherData.date.desc()).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    weather_records = result.scalars().all()
    
    # 格式化返回数据
    data = [
        {
            "city": record.city,
            "date": record.date.strftime("%Y-%m-%d"),
            "weather_condition": record.weather_condition,
            "temp_min": record.temp_min,
            "temp_max": record.temp_max,
            "wind_info": record.wind_info
        }
        for record in weather_records
    ]
    
    return data


@router.get("/stats")
async def get_weather_stats(
    api_key_data: Tuple[APIKey, User] = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    获取天气数据统计信息
    
    返回数据总量、支持的城市列表、日期范围等
    """
    api_key, user = api_key_data
    
    # 查询总记录数
    count_query = select(func.count(WeatherData.id))
    count_result = await db.execute(count_query)
    total_records = count_result.scalar()
    
    # 查询城市列表
    cities_query = select(WeatherData.city).distinct()
    cities_result = await db.execute(cities_query)
    cities = [city for city in cities_result.scalars().all()]
    
    # 查询日期范围
    date_query = select(
        func.min(WeatherData.date).label('min_date'),
        func.max(WeatherData.date).label('max_date')
    )
    date_result = await db.execute(date_query)
    date_range = date_result.one_or_none()
    
    return {
        "total_records": total_records,
        "cities_count": len(cities),
        "cities": cities[:20] if cities else [],  # 返回前20个城市
        "date_range": {
            "start": date_range[0].strftime("%Y-%m-%d") if date_range and date_range[0] else None,
            "end": date_range[1].strftime("%Y-%m-%d") if date_range and date_range[1] else None
        },
        "user_info": {
            "username": user.username,
            "remaining_quota": api_key.remaining_quota
        }
    }
