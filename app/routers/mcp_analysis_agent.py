"""
HTTP-facing wrappers for Analysis Agent MCP tools.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from mcp_tools.analysis_agent import (
    tool_compare_cities,
    tool_describe_timeseries,
    tool_extreme_event_stats,
    tool_group_by_period,
    tool_simple_forecast,
)

router = APIRouter(prefix="/mcp/analysis", tags=["mcp-analysis-agent"])

VALID_METRIC = {"temp_min", "temp_max"}
VALID_COMPARISON = {">", "<", ">=", "<=", "gt", "lt", "gte", "lte", "ge", "le", "greater", "less", "greater_equal", "less_equal"}


class DescribeRequest(BaseModel):
    city: str
    metric: str
    start_date: str
    end_date: str


class DescribeResult(BaseModel):
    ok: bool
    city: str
    metric: str
    start_date: str
    end_date: str
    count: int | None = None
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    stddev: float | None = None
    error: Optional[str] = None


class GroupByRequest(BaseModel):
    city: str
    metric: str
    period: str
    start_date: str
    end_date: str


class PeriodPoint(BaseModel):
    period: str
    count: int
    min: float | None = None
    max: float | None = None
    mean: float | None = None


class GroupByResult(BaseModel):
    ok: bool
    city: str
    metric: str
    period: str
    start_date: str
    end_date: str
    series: List[PeriodPoint] = []
    error: Optional[str] = None


class CompareRequest(BaseModel):
    cities: List[str]
    metric: str
    start_date: str
    end_date: str


class CompareItem(BaseModel):
    city: str
    count: int
    min: float | None = None
    max: float | None = None
    mean: float | None = None


class CompareResult(BaseModel):
    ok: bool
    metric: str
    start_date: str
    end_date: str
    results: List[CompareItem] = []
    error: Optional[str] = None


class ExtremeRequest(BaseModel):
    city: str
    metric: str
    threshold: float
    comparison: str
    start_date: str
    end_date: str


class ExtremeResult(BaseModel):
    ok: bool
    city: str
    metric: str
    comparison: str
    threshold: float
    start_date: str
    end_date: str
    event_days: int | None = None
    error: Optional[str] = None


class ForecastRequest(BaseModel):
    city: str
    metric: str
    horizon_days: int = 7


class ForecastPoint(BaseModel):
    date: str
    temp_min: float | None = None
    temp_max: float | None = None


class ForecastResult(BaseModel):
    ok: bool
    city: str
    metric: str
    horizon_days: int
    method: str | None = None
    forecast: List[ForecastPoint] = []
    error: Optional[str] = None


@router.post("/describe_timeseries", response_model=DescribeResult)
async def analysis_describe_timeseries(body: DescribeRequest):
    if body.metric not in VALID_METRIC:
        raise HTTPException(status_code=400, detail="metric must be temp_min or temp_max")
    return await tool_describe_timeseries(body.city, body.metric, body.start_date, body.end_date)


@router.post("/group_by_period", response_model=GroupByResult)
async def analysis_group_by_period(body: GroupByRequest):
    if body.metric not in VALID_METRIC:
        raise HTTPException(status_code=400, detail="metric must be temp_min or temp_max")
    return await tool_group_by_period(body.city, body.metric, body.period, body.start_date, body.end_date)


@router.post("/compare_cities", response_model=CompareResult)
async def analysis_compare_cities(body: CompareRequest):
    if body.metric not in VALID_METRIC:
        raise HTTPException(status_code=400, detail="metric must be temp_min or temp_max")
    return await tool_compare_cities(body.cities, body.metric, body.start_date, body.end_date)


@router.post("/extreme_event_stats", response_model=ExtremeResult)
async def analysis_extreme_event_stats(body: ExtremeRequest):
    if body.metric not in VALID_METRIC:
        raise HTTPException(status_code=400, detail="metric must be temp_min or temp_max")
    if body.comparison not in VALID_COMPARISON:
        raise HTTPException(status_code=400, detail="comparison must be one of >,<,>=,<=,gt,lt,gte,lte,greater,less,greater_equal,less_equal")
    return await tool_extreme_event_stats(body.city, body.metric, body.threshold, body.comparison, body.start_date, body.end_date)


@router.post("/simple_forecast", response_model=ForecastResult)
async def analysis_simple_forecast(body: ForecastRequest):
    if body.metric not in VALID_METRIC:
        raise HTTPException(status_code=400, detail="metric must be temp_min or temp_max")
    return await tool_simple_forecast(body.city, body.metric, body.horizon_days)
