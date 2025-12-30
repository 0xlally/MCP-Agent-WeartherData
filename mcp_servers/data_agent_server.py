"""MCP server exposing weather data tools via fastmcp."""
from __future__ import annotations

import os
import sys

# Ensure project root is on sys.path when launched via `python mcp_servers/...`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastmcp import FastMCP

from mcp_tools.data_agent import (
    tool_get_range,
    tool_get_dataset_overview,
    tool_check_coverage,
    tool_custom_query,
    tool_update_city_range,
)

mcp = FastMCP("WeatherData")


@mcp.tool()
async def data_get_range(
    city: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 500,
):
    """Return daily weather records filtered by city and date range."""
    return await tool_get_range(city, start_date, end_date, limit)


@mcp.tool()
async def data_get_dataset_overview():
    """Dataset summary including record counts, cities, and date range."""
    return await tool_get_dataset_overview()


@mcp.tool()
async def data_check_coverage(city: str, start_date: str, end_date: str):
    """Report missing dates for a city within a range."""
    return await tool_check_coverage(city, start_date, end_date)


@mcp.tool()
async def data_custom_query(
    fields: list[str] | None = None,
    city: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 200,
):
    """Run a restricted field query over weather records."""
    fields = fields or []
    return await tool_custom_query(fields, city, start_date, end_date, limit)


@mcp.tool()
async def data_update_city_range(city: str, start_date: str, end_date: str):
    """Fetch and upsert weather data for a city/date range via crawler."""
    return await tool_update_city_range(city, start_date, end_date)


if __name__ == "__main__":
    mcp.run(transport="stdio")
