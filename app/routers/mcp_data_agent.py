"""
HTTP-facing wrappers for Data Agent MCP tools.
Exposes the async tool_* functions from mcp_tools/data_agent.py via FastAPI routes.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from mcp_tools.data_agent import (
    tool_check_coverage,
    tool_custom_query,
    tool_get_dataset_overview,
    tool_get_range,
    tool_update_city_range,
)

router = APIRouter(prefix="/mcp", tags=["mcp-data-agent"])


# ---------- Models ----------


class WeatherItem(BaseModel):
    city: str
    date: str
    weather_condition: Optional[str] = None
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    wind_info: Optional[str] = None


class GetRangeRequest(BaseModel):
    city: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = 500


class GetRangeResult(BaseModel):
    count: int
    items: List[WeatherItem]


class DatasetOverviewRequest(BaseModel):
    pass


class DateRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class DatasetOverviewResult(BaseModel):
    total_records: int
    cities: List[str]
    date_range: DateRange


class CoverageRequest(BaseModel):
    city: str
    start_date: str
    end_date: str


class CoverageResult(BaseModel):
    city: str
    start_date: str
    end_date: str
    total_days: int
    available_days: int
    missing_days: List[str]


class CustomQueryRequest(BaseModel):
    fields: List[str] = []
    city: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = 200


class CustomQueryResult(BaseModel):
    count: int
    fields: List[str]
    rows: List[Dict[str, Any]]


class UpdateCityRangeRequest(BaseModel):
    city: str
    start_date: str
    end_date: str


class UpdateCityRangeResult(BaseModel):
    ok: bool
    message: str
    city: str
    start_date: str
    end_date: str


# ---------- Routes ----------


@router.post("/data.get_range", response_model=GetRangeResult)
async def mcp_data_get_range(body: GetRangeRequest):
    result = await tool_get_range(
        city=body.city,
        start_date=body.start_date,
        end_date=body.end_date,
        limit=body.limit or 500,
    )
    return result


@router.post("/data.get_dataset_overview", response_model=DatasetOverviewResult)
async def mcp_data_get_dataset_overview(body: DatasetOverviewRequest):
    result = await tool_get_dataset_overview()
    return result


@router.post("/data.check_coverage", response_model=CoverageResult)
async def mcp_data_check_coverage(body: CoverageRequest):
    result = await tool_check_coverage(
        city=body.city,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return result


@router.post("/data.custom_query", response_model=CustomQueryResult)
async def mcp_data_custom_query(body: CustomQueryRequest):
    result = await tool_custom_query(
        fields=body.fields or [],
        city=body.city,
        start_date=body.start_date,
        end_date=body.end_date,
        limit=body.limit or 200,
    )
    return result


@router.post("/data.update_city_range", response_model=UpdateCityRangeResult)
async def mcp_data_update_city_range(body: UpdateCityRangeRequest):
    result = await tool_update_city_range(
        city=body.city,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return result
