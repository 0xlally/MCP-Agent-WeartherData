"""Analysis Agent MCP tools.
Provides analysis utilities over weather data.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.models import WeatherData
from mcp_tools.data_agent import _CITY_PINYIN


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


async def _get_session() -> AsyncSession:
    return AsyncSessionLocal()


def _normalize_city_name(city: str) -> str:
    if not city:
        return city
    raw = city.strip()
    low = raw.lower()
    # pinyin/en key -> Chinese name
    if low in _CITY_PINYIN:
        return _CITY_PINYIN[low]
    # already Chinese match or other casing
    for p, cn in _CITY_PINYIN.items():
        if low == cn.lower():
            return cn
    return raw


_VALID_METRIC = {"temp_min", "temp_max"}
_VALID_PERIOD = {"month", "season", "year"}
_COMPARISONS = {
    ">": lambda col, t: col > t,
    "gt": lambda col, t: col > t,
    "greater": lambda col, t: col > t,
    "<": lambda col, t: col < t,
    "lt": lambda col, t: col < t,
    "less": lambda col, t: col < t,
    ">=": lambda col, t: col >= t,
    "gte": lambda col, t: col >= t,
    "ge": lambda col, t: col >= t,
    "greater_equal": lambda col, t: col >= t,
    "<=": lambda col, t: col <= t,
    "lte": lambda col, t: col <= t,
    "le": lambda col, t: col <= t,
    "less_equal": lambda col, t: col <= t,
}


async def tool_describe_timeseries(city: str, metric: str, start_date: str, end_date: str) -> Dict[str, Any]:
    if metric not in _VALID_METRIC:
        return {"ok": False, "error": "metric must be temp_min or temp_max"}
    city = _normalize_city_name(city)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not (city and start and end):
        return {"ok": False, "error": "city/start_date/end_date required"}

    async with await _get_session() as db:
        col = getattr(WeatherData, metric)
        query = (
            select(
                func.count(col),
                func.min(col),
                func.max(col),
                func.avg(col),
                func.stddev_samp(col),
            )
            .where(
                func.lower(WeatherData.city) == func.lower(city.strip()),
                WeatherData.date >= start,
                WeatherData.date <= end,
                col.isnot(None),
            )
        )
        c, mn, mx, avg, std = (await db.execute(query)).one()

    return {
        "ok": True,
        "city": city,
        "metric": metric,
        "start_date": start_date,
        "end_date": end_date,
        "count": c or 0,
        "min": mn,
        "max": mx,
        "mean": float(avg) if avg is not None else None,
        "stddev": float(std) if std is not None else None,
    }


async def tool_group_by_period(city: str, metric: str, period: str, start_date: str, end_date: str) -> Dict[str, Any]:
    if metric not in _VALID_METRIC:
        return {"ok": False, "error": "metric must be temp_min or temp_max"}
    if period not in _VALID_PERIOD:
        return {"ok": False, "error": "period must be month|season|year"}
    city = _normalize_city_name(city)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not (city and start and end):
        return {"ok": False, "error": "city/start_date/end_date required"}

    async with await _get_session() as db:
        col = getattr(WeatherData, metric)
        rows = (
            await db.execute(
                select(WeatherData.date, col)
                .where(
                    func.lower(WeatherData.city) == func.lower(city.strip()),
                    WeatherData.date >= start,
                    WeatherData.date <= end,
                    col.isnot(None),
                )
                .order_by(WeatherData.date)
            )
        ).all()

    buckets: Dict[str, List[float]] = defaultdict(list)
    for d, v in rows:
        if v is None:
            continue
        if period == "year":
            key = f"{d.year}"
        elif period == "month":
            key = f"{d.year}-{d.month:02d}"
        else:  # season
            season = (d.month - 1) // 3 + 1
            key = f"{d.year}-Q{season}"
        buckets[key].append(float(v))

    series = []
    for k in sorted(buckets.keys()):
        vals = buckets[k]
        series.append(
            {
                "period": k,
                "count": len(vals),
                "min": min(vals),
                "max": max(vals),
                "mean": sum(vals) / len(vals) if vals else None,
            }
        )

    return {
        "ok": True,
        "city": city,
        "metric": metric,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "series": series,
    }


async def tool_compare_cities(cities: List[str], metric: str, start_date: str, end_date: str) -> Dict[str, Any]:
    if metric not in _VALID_METRIC:
        return {"ok": False, "error": "metric must be temp_min or temp_max"}
    if not cities:
        return {"ok": False, "error": "cities required"}
    cities = [_normalize_city_name(c) for c in cities if c]
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not (start and end):
        return {"ok": False, "error": "start_date/end_date required"}

    city_norm = [c.strip() for c in cities if c and c.strip()]
    async with await _get_session() as db:
        col = getattr(WeatherData, metric)
        query = (
            select(
                WeatherData.city,
                func.count(col),
                func.min(col),
                func.max(col),
                func.avg(col),
            )
            .where(
                func.lower(WeatherData.city).in_([func.lower(c) for c in city_norm]),
                WeatherData.date >= start,
                WeatherData.date <= end,
                col.isnot(None),
            )
            .group_by(WeatherData.city)
        )
        rows = (await db.execute(query)).all()

    results = [
        {
            "city": r[0],
            "count": r[1],
            "min": r[2],
            "max": r[3],
            "mean": float(r[4]) if r[4] is not None else None,
        }
        for r in rows
    ]
    return {
        "ok": True,
        "metric": metric,
        "start_date": start_date,
        "end_date": end_date,
        "results": results,
    }


async def tool_extreme_event_stats(city: str, metric: str, threshold: float, comparison: str, start_date: str, end_date: str) -> Dict[str, Any]:
    if metric not in _VALID_METRIC:
        return {"ok": False, "error": "metric must be temp_min or temp_max"}
    if comparison not in _COMPARISONS:
        return {"ok": False, "error": "comparison must be one of >,<,>=,<="}
    city = _normalize_city_name(city)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not (city and start and end):
        return {"ok": False, "error": "city/start_date/end_date required"}

    col = getattr(WeatherData, metric)
    cond = _COMPARISONS[comparison](col, threshold)

    async with await _get_session() as db:
        query = select(func.count(col)).where(
            func.lower(WeatherData.city) == func.lower(city.strip()),
            WeatherData.date >= start,
            WeatherData.date <= end,
            col.isnot(None),
            cond,
        )
        count = (await db.execute(query)).scalar() or 0

    return {
        "ok": True,
        "city": city,
        "metric": metric,
        "comparison": comparison,
        "threshold": threshold,
        "start_date": start_date,
        "end_date": end_date,
        "event_days": count,
    }


async def tool_simple_forecast(city: str, metric: str, horizon_days: int = 7) -> Dict[str, Any]:
    if metric not in _VALID_METRIC:
        return {"ok": False, "error": "metric must be temp_min or temp_max"}
    if not city:
        return {"ok": False, "error": "city required"}
    city = _normalize_city_name(city)
    horizon_days = max(1, min(int(horizon_days or 7), 30))

    async with await _get_session() as db:
        col = getattr(WeatherData, metric)
        rows = (
            await db.execute(
                select(WeatherData.date, col)
                .where(func.lower(WeatherData.city) == func.lower(city.strip()), col.isnot(None))
                .order_by(WeatherData.date.desc())
                .limit(120)
            )
        ).all()

    # use latest 120 points in chronological order
    rows = list(reversed(rows))

    if len(rows) < 2:
        return {"ok": False, "error": "not enough data for forecast", "city": city, "metric": metric}

    # Use simple linear trend over available points
    xs = list(range(len(rows)))
    ys = [float(r[1]) for r in rows]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs) or 1.0
    slope = num / den
    intercept = mean_y - slope * mean_x

    last_date = rows[-1][0]
    forecast = []
    for i in range(1, horizon_days + 1):
        y_hat = intercept + slope * (n - 1 + i)
        d = last_date + timedelta(days=i)
        forecast.append({"date": d.isoformat(), metric: round(y_hat, 2)})

    return {
        "ok": True,
        "city": city,
        "metric": metric,
        "horizon_days": horizon_days,
        "method": "simple_linear_trend",
        "forecast": forecast,
    }


# ----- CLI -----

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Analysis Agent MCP tool runner")
    p.add_argument("--tool", required=True)
    p.add_argument("--city")
    p.add_argument("--cities", nargs="*")
    p.add_argument("--metric")
    p.add_argument("--start-date")
    p.add_argument("--end-date")
    p.add_argument("--period")
    p.add_argument("--threshold", type=float)
    p.add_argument("--comparison")
    p.add_argument("--horizon", type=int, default=7)
    p.add_argument("--limit", type=int)
    p.add_argument("--fields", nargs="*")
    return p


def main():
    args = _build_parser().parse_args()
    if args.tool == "analysis.describe_timeseries":
        coro = tool_describe_timeseries(args.city, args.metric, args.start_date, args.end_date)
    elif args.tool == "analysis.group_by_period":
        coro = tool_group_by_period(args.city, args.metric, args.period, args.start_date, args.end_date)
    elif args.tool == "analysis.compare_cities":
        coro = tool_compare_cities(args.cities or [], args.metric, args.start_date, args.end_date)
    elif args.tool == "analysis.extreme_event_stats":
        coro = tool_extreme_event_stats(args.city, args.metric, args.threshold, args.comparison, args.start_date, args.end_date)
    elif args.tool == "analysis.simple_forecast":
        coro = tool_simple_forecast(args.city, args.metric, args.horizon)
    else:
        raise SystemExit(f"Unknown tool: {args.tool}")

    result = asyncio.run(coro)
    print(result)


if __name__ == "__main__":
    main()
