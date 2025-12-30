import asyncio
import json

import httpx

BASE_URL = "http://localhost:8080"


async def call(client: httpx.AsyncClient, path: str, payload: dict):
    resp = await client.post(f"{BASE_URL}{path}", json=payload)
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    print(f"=== {path} ===")
    print(f"status: {resp.status_code}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()


async def main():
    async with httpx.AsyncClient(timeout=20) as client:
        await call(client, "/mcp/data.get_dataset_overview", {})
        await call(
            client,
            "/mcp/data.get_range",
            {"city": "北京", "start_date": "2025-11-01", "end_date": "2025-12-02", "limit": 5},
        )
        await call(
            client,
            "/mcp/data.check_coverage",
            {"city": "北京", "start_date": "2025-11-01", "end_date": "2025-12-02"},
        )
        await call(
            client,
            "/mcp/data.custom_query",
            {
                "fields": ["city", "date", "temp_max"],
                "city": "北京",
                "start_date": "2025-11-01",
                "end_date": "2025-12-02",
                "limit": 5,
            },
        )


if __name__ == "__main__":
    asyncio.run(main())
