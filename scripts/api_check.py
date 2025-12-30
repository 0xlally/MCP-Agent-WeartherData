import requests

BASE = "http://localhost:8080"


def check(path, **kwargs):
    url = f"{BASE}{path}"
    try:
        resp = requests.request(kwargs.pop("method", "get"), url, timeout=15, **kwargs)
    except Exception as exc:
        return {"path": path, "ok": False, "error": str(exc)}
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    return {"path": path, "status": resp.status_code, "ok": 200 <= resp.status_code < 300, "body": body}


def main():
    results = []
    results.append(check("/health"))
    results.append(check("/weather/stats"))
    params = {
        "city": "Beijing",
        "start_date": "2020-02-11",
        "end_date": "2022-03-22",
        "limit": 50,
    }
    results.append(check("/weather", params=params))

    for r in results:
        print("---")
        for k, v in r.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
