"""MCP server exposing analysis tools via fastmcp."""
from __future__ import annotations

import os
import sys

# ensure project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastmcp import FastMCP

from mcp_tools.analysis_agent import (
    tool_describe_timeseries,
    tool_group_by_period,
    tool_compare_cities,
    tool_extreme_event_stats,
    tool_simple_forecast,
)

mcp = FastMCP("WeatherAnalysis")


@mcp.tool()
async def analysis_describe_timeseries(city: str, metric: str, start_date: str, end_date: str):
    """基础统计：均值、极值、标准差。"""
    return await tool_describe_timeseries(city, metric, start_date, end_date)


@mcp.tool()
async def analysis_group_by_period(city: str, metric: str, period: str, start_date: str, end_date: str):
    """按月/季/年聚合统计。"""
    return await tool_group_by_period(city, metric, period, start_date, end_date)


@mcp.tool()
async def analysis_compare_cities(cities: list[str], metric: str, start_date: str, end_date: str):
    """多城市同指标对比。"""
    return await tool_compare_cities(cities, metric, start_date, end_date)


@mcp.tool()
async def analysis_extreme_event_stats(city: str, metric: str, threshold: float, comparison: str, start_date: str, end_date: str):
    """极端事件统计（阈值比较）。"""
    return await tool_extreme_event_stats(city, metric, threshold, comparison, start_date, end_date)


@mcp.tool()
async def analysis_simple_forecast(city: str, metric: str, horizon_days: int = 7):
    """简单线性趋势预测。"""
    return await tool_simple_forecast(city, metric, horizon_days)


if __name__ == "__main__":
    mcp.run(transport="stdio")
