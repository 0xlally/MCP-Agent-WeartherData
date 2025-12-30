"""
MCP tool listing endpoints.
Provides a structured list of available Data/Analysis Agent tools.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["MCP"])

TOOLS = {
    "data": [
        {
            "name": "data.get_range",
            "description": "按城市+时间段返回逐日天气数据",
            "params": {
                "city": "string (必填)",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD",
                "limit": "int，可选，默认500"
            }
        },
        {
            "name": "data.get_dataset_overview",
            "description": "返回数据总量、城市列表、日期范围",
            "params": {}
        },
        {
            "name": "data.check_coverage",
            "description": "检查某城市在时间段内的缺失日期",
            "params": {
                "city": "string (必填)",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD"
            }
        },
        {
            "name": "data.custom_query",
            "description": "受控字段集合的自定义查询 (city/date/temp_min/temp_max/weather_condition/wind_info)",
            "params": {
                "fields": "string array，可选，默认全字段",
                "city": "string，可选",
                "start_date": "YYYY-MM-DD，可选",
                "end_date": "YYYY-MM-DD，可选",
                "limit": "int，可选，默认200"
            }
        },
        {
            "name": "data.update_city_range",
            "description": "占位：为指定城市/时间段更新数据（待接入爬虫）",
            "params": {
                "city": "string",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD"
            }
        }
    ],
    "analysis": [
        {
            "name": "analysis.describe_timeseries",
            "description": "时间序列基础统计（均值/极值/标准差）",
            "params": {
                "city": "string",
                "metric": "temp_min|temp_max",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD"
            }
        },
        {
            "name": "analysis.group_by_period",
            "description": "按月/季/年聚合统计",
            "params": {
                "city": "string",
                "metric": "temp_min|temp_max",
                "period": "month|season|year",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD"
            }
        },
        {
            "name": "analysis.compare_cities",
            "description": "多城市同一指标对比",
            "params": {
                "cities": "string array",
                "metric": "temp_min|temp_max",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD"
            }
        },
        {
            "name": "analysis.extreme_event_stats",
            "description": "极端事件统计（如高温天数）",
            "params": {
                "city": "string",
                "metric": "temp_max|temp_min",
                "threshold": "float",
                "comparison": ">|<|>=|<=",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD"
            }
        },
        {
            "name": "analysis.build_chart_series",
            "description": "输出 ECharts 友好结构",
            "params": {
                "series": "数据序列定义",
                "chart_type": "line|bar|stack"
            }
        },
        {
            "name": "analysis.simple_forecast",
            "description": "简单预测占位（后续实现）",
            "params": {
                "city": "string",
                "metric": "temp_max|temp_min",
                "horizon_days": "int"
            }
        }
    ]
}


@router.get("/tools")
async def list_tools():
    return {"tools": TOOLS}
