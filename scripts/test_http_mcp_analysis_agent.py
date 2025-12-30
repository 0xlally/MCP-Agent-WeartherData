"""Smoke tests for MCP analysis agent HTTP endpoints."""
from __future__ import annotations

import requests

BASE = "http://localhost:8080/mcp/analysis"


def pretty(title, resp):
    print(f"\n=== {title} ({resp.status_code}) ===")
    try:
        print(resp.json())
    except Exception:
        print(resp.text)


def main():
    # describe
    r1 = requests.post(
        f"{BASE}/describe_timeseries",
        json={"city": "北京", "metric": "temp_max", "start_date": "2025-11-01", "end_date": "2025-11-15"},
    )
    pretty("describe_timeseries", r1)

    # group by month
    r2 = requests.post(
        f"{BASE}/group_by_period",
        json={"city": "北京", "metric": "temp_max", "period": "month", "start_date": "2025-10-01", "end_date": "2025-12-02"},
    )
    pretty("group_by_period", r2)

    # compare cities
    r3 = requests.post(
        f"{BASE}/compare_cities",
        json={"cities": ["北京", "上海", "广州"], "metric": "temp_max", "start_date": "2025-11-01", "end_date": "2025-11-30"},
    )
    pretty("compare_cities", r3)

    # extreme event stats
    r4 = requests.post(
        f"{BASE}/extreme_event_stats",
        json={"city": "北京", "metric": "temp_max", "threshold": 30, "comparison": ">=", "start_date": "2025-06-01", "end_date": "2025-09-30"},
    )
    pretty("extreme_event_stats", r4)

    # simple forecast
    r5 = requests.post(
        f"{BASE}/simple_forecast",
        json={"city": "北京", "metric": "temp_max", "horizon_days": 5},
    )
    pretty("simple_forecast", r5)


if __name__ == "__main__":
    main()
