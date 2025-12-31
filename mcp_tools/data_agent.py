"""
Data Agent MCP tools.
Implements data-related tool functions for MCP wiring:
- data.get_range: fetch weather time series by city/date range
- data.get_dataset_overview: dataset stats
- data.check_coverage: missing-date coverage check
- data.custom_query: restricted DSL query
- data.update_city_range: placeholder hook for future crawler

This module can be invoked as a script for quick testing:
  python mcp_tools/data_agent.py --tool data.get_range --city 北京 --start-date 2020-01-01 --end-date 2020-01-10 --limit 5
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.models import WeatherData

# ----- helpers -----


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


async def _get_session() -> AsyncSession:
    return AsyncSessionLocal()


# ----- crawler helpers -----


_CITY_PINYIN = {
    'kunming': '昆明', 'beijing': '北京', 'shanghai': '上海',
    'guangzhou': '广州', 'shenzhen': '深圳', 'chengdu': '成都',
    'chongqing': '重庆', 'tianjin': '天津', 'hangzhou': '杭州',
    'nanjing': '南京', 'wuhan': '武汉', 'xian': '西安',
    'changsha': '长沙', 'zhengzhou': '郑州', 'jinan': '济南',
    'qingdao': '青岛', 'dalian': '大连', 'shenyang': '沈阳',
    'haerbin': '哈尔滨', 'changchun': '长春', 'fuzhou': '福州',
    'xiamen': '厦门', 'nanning': '南宁', 'haikou': '海口',
    'guiyang': '贵阳', 'hefei': '合肥', 'lanzhou': '兰州',
    'shijiazhuang': '石家庄', 'taiyuan': '太原', 'nanchang': '南昌'
}


def _normalize_city_name(city: Optional[str]) -> Optional[str]:
    """Normalize city names so that 'Beijing'/'beijing' match '北京'.

    Uses the shared _CITY_PINYIN mapping. If input is already a known Chinese
    name (any casing), it is returned as-is; if it matches a pinyin key, the
    corresponding Chinese name is returned; otherwise the original string.
    """
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


def _find_city_pinyin(city: str) -> Optional[str]:
    city = city.strip()
    # exact Chinese match
    for p, cn in _CITY_PINYIN.items():
        if city == cn:
            return p
    # pinyin key match
    if city in _CITY_PINYIN:
        return city
    return None


def _iter_months(start: date, end: date):
    cur = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cur <= last:
        yield cur.year, f"{cur.month:02d}"
        # next month
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)


def _parse_temp(temp_raw: str) -> tuple[Optional[float], Optional[float]]:
    if not temp_raw:
        return None, None
    temp_raw = temp_raw.replace(' ', '').replace('℃', '')
    # handle formats like '7-16' or '16-7' or '16/7'
    for sep in ['-', '/', '~']:
        if sep in temp_raw:
            parts = temp_raw.split(sep)
            if len(parts) == 2:
                try:
                    a, b = float(parts[0]), float(parts[1])
                    return min(a, b), max(a, b)
                except Exception:
                    return None, None
    try:
        v = float(temp_raw)
        return v, v
    except Exception:
        return None, None


def _fetch_month(city_pinyin: str, city_name: str, year: int, month: str) -> List[Dict[str, Any]]:
    url = f"http://www.tianqihoubao.com/lishi/{city_pinyin}/month/{year}{month}.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.content, 'html.parser', from_encoding='gbk')
        table = soup.find('table')
        if not table:
            return []
        rows = table.find_all('tr')
        out = []
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) < 4:
                continue
            date_str = cols[0].get_text().strip()
            if not date_str:
                continue
            weather_cond = cols[1].get_text().strip() or None
            temp_raw = cols[2].get_text().strip()
            wind_info = cols[3].get_text().strip() or None
            t_min, t_max = _parse_temp(temp_raw)
            out.append(
                {
                    "city": city_name,
                    "date": date_str,
                    "weather_condition": weather_cond,
                    "temp_min": t_min,
                    "temp_max": t_max,
                    "wind_info": wind_info,
                }
            )
        return out
    except Exception:
        return []


# ----- tool impls -----


async def tool_get_range(city: Optional[str], start_date: Optional[str], end_date: Optional[str], limit: int = 500) -> Dict[str, Any]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if city:
        city = _normalize_city_name(city)
    async with await _get_session() as db:
        query = select(WeatherData)
        if city:
            query = query.where(func.lower(WeatherData.city) == func.lower(city.strip()))
        if start:
            query = query.where(WeatherData.date >= start)
        if end:
            query = query.where(WeatherData.date <= end)
        query = query.order_by(WeatherData.date.desc()).limit(limit)
        rows = (await db.execute(query)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "city": r.city,
                "date": r.date.isoformat(),
                "weather_condition": r.weather_condition,
                "temp_min": r.temp_min,
                "temp_max": r.temp_max,
                "wind_info": r.wind_info,
            }
            for r in rows
        ],
    }


async def tool_get_dataset_overview() -> Dict[str, Any]:
    async with await _get_session() as db:
        total = (await db.execute(select(func.count(WeatherData.id)))).scalar()
        cities = (await db.execute(select(WeatherData.city).distinct().order_by(WeatherData.city))).scalars().all()
        dr = (
            await db.execute(
                select(func.min(WeatherData.date).label("start"), func.max(WeatherData.date).label("end"))
            )
        ).one_or_none()
    return {
        "total_records": total,
        "cities": cities,
        "date_range": {"start": dr[0].isoformat() if dr and dr[0] else None, "end": dr[1].isoformat() if dr and dr[1] else None},
    }


async def tool_check_coverage(city: str, start_date: str, end_date: str) -> Dict[str, Any]:
    city = _normalize_city_name(city)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not (city and start and end):
        return {"ok": False, "error": "city, start_date, end_date are required"}

    async with await _get_session() as db:
        query = select(WeatherData.date).where(
            func.lower(WeatherData.city) == func.lower(city.strip()),
            WeatherData.date >= start,
            WeatherData.date <= end,
        )
        dates = [d[0] for d in (await db.execute(query)).all()]

    have = set(dates)
    missing = []
    cur = start
    while cur <= end:
        if cur not in have:
            missing.append(cur.isoformat())
        cur += timedelta(days=1)

    return {
        "city": city,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_days": (end - start).days + 1,
        "available_days": len(dates),
        "missing_days": missing,
    }


ALLOWED_FIELDS = {"city", "date", "weather_condition", "temp_min", "temp_max", "wind_info"}


async def tool_custom_query(fields: List[str], city: Optional[str], start_date: Optional[str], end_date: Optional[str], limit: int = 200) -> Dict[str, Any]:
    selected = [f for f in fields if f in ALLOWED_FIELDS]
    if not selected:
        selected = ["city", "date", "temp_min", "temp_max", "weather_condition", "wind_info"]
    if city:
        city = _normalize_city_name(city)
    start = _parse_date(start_date)
    end = _parse_date(end_date)

    async with await _get_session() as db:
        cols = [getattr(WeatherData, f) for f in selected]
        query = select(*cols)
        if city:
            query = query.where(func.lower(WeatherData.city) == func.lower(city.strip()))
        if start:
            query = query.where(WeatherData.date >= start)
        if end:
            query = query.where(WeatherData.date <= end)
        query = query.order_by(WeatherData.date.desc()).limit(limit)
        res = await db.execute(query)
        rows = res.all()

    items = [dict(zip(selected, row)) for row in rows]
    # Serialize date objects
    for item in items:
        for k, v in list(item.items()):
            if isinstance(v, (date, datetime)):
                item[k] = v.isoformat()
    return {"count": len(items), "fields": selected, "rows": items}


async def tool_update_city_range(city: str, start_date: str, end_date: str) -> Dict[str, Any]:
    city = _normalize_city_name(city)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not (city and start and end):
        return {
            "ok": False,
            "message": "city/start_date/end_date are required",
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
        }

    city_pinyin = _find_city_pinyin(city)
    if not city_pinyin:
        return {
            "ok": False,
            "message": "city not supported by crawler",
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
        }

    fetched: List[Dict[str, Any]] = []
    for y, m in _iter_months(start, end):
        month_rows = _fetch_month(city_pinyin, _CITY_PINYIN[city_pinyin], y, m)
        fetched.extend(month_rows)

    # Filter to requested range and parse date
    filtered = []
    for r in fetched:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date()
        except Exception:
            continue
        if d < start or d > end:
            continue
        filtered.append({
            "city": r["city"],
            "date": d,
            "weather_condition": r.get("weather_condition"),
            "temp_min": r.get("temp_min"),
            "temp_max": r.get("temp_max"),
            "wind_info": r.get("wind_info"),
        })

    if not filtered:
        return {
            "ok": False,
            "message": "no data fetched for the given range",
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "fetched": 0,
            "saved": 0,
        }

    async with await _get_session() as db:
        # remove existing rows for this city/range to avoid duplicates
        from sqlalchemy import delete

        await db.execute(
            delete(WeatherData).where(
                func.lower(WeatherData.city) == func.lower(city.strip()),
                WeatherData.date >= start,
                WeatherData.date <= end,
            )
        )
        db.add_all([WeatherData(**item) for item in filtered])
        await db.commit()

    return {
        "ok": True,
        "message": "update_city_range completed",
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "fetched": len(fetched),
        "saved": len(filtered),
    }


# ----- CLI entry for manual testing -----


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Data Agent MCP tool runner")
    p.add_argument("--tool", required=True, help="Tool name: data.get_range | data.get_dataset_overview | data.check_coverage | data.custom_query | data.update_city_range")
    p.add_argument("--city")
    p.add_argument("--start-date")
    p.add_argument("--end-date")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--fields", nargs="*", default=[])
    return p


def main():
    args = _build_parser().parse_args()
    if args.tool == "data.get_range":
        coro = tool_get_range(args.city, args.start_date, args.end_date, args.limit)
    elif args.tool == "data.get_dataset_overview":
        coro = tool_get_dataset_overview()
    elif args.tool == "data.check_coverage":
        coro = tool_check_coverage(args.city, args.start_date, args.end_date)
    elif args.tool == "data.custom_query":
        coro = tool_custom_query(args.fields, args.city, args.start_date, args.end_date, args.limit)
    elif args.tool == "data.update_city_range":
        coro = tool_update_city_range(args.city, args.start_date, args.end_date)
    else:
        raise SystemExit(f"Unknown tool: {args.tool}")

    result = asyncio.run(coro)
    print(result)


if __name__ == "__main__":
    main()
