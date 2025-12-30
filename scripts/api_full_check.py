import requests
from datetime import datetime

BASE = "http://localhost:8080"


def req(method, path, **kwargs):
    url = f"{BASE}{path}"
    try:
        resp = requests.request(method, url, timeout=15, **kwargs)
    except Exception as exc:
        return {"path": path, "ok": False, "error": str(exc)}
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    return {"path": path, "status": resp.status_code, "ok": 200 <= resp.status_code < 300, "body": body}


def main():
    results = []

    # 1) Health
    results.append(req("get", "/health"))

    # 2) Stats (get cities/date range)
    stats = req("get", "/weather/stats")
    results.append(stats)

    cities = []
    date_start = "2016-01-01"
    date_end = datetime.today().strftime("%Y-%m-%d")
    if stats.get("ok") and isinstance(stats.get("body"), dict):
        cities = stats["body"].get("cities", []) or []
        dr = stats["body"].get("date_range") or {}
        date_start = dr.get("start") or date_start
        date_end = dr.get("end") or date_end

    # 3) Query up to 3 sample cities
    sample_cities = cities[:3] if cities else [None]
    for c in sample_cities:
        params = {
            "city": c,
            "start_date": date_start,
            "end_date": date_end,
            "limit": 5,
        }
        results.append(req("get", "/weather", params=params))

    # Print results
    for r in results:
        print("---")
        for k, v in r.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
