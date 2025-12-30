import argparse
import os
import sys
import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Weather API smoke test")
    parser.add_argument("--api-key", dest="api_key", default=os.getenv("API_KEY"), help="API key for X-API-KEY header")
    parser.add_argument("--base-url", dest="base_url", default=os.getenv("BASE_URL", "http://localhost:8080"), help="Backend base URL")
    parser.add_argument("--city", dest="city", required=True, help="City name")
    parser.add_argument("--start", dest="start_date", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", dest="end_date", help="End date YYYY-MM-DD")
    parser.add_argument("--limit", dest="limit", type=int, default=100, help="Max rows to fetch (1-1000)")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.api_key:
        print("[ERROR] API key is required. Pass --api-key or set API_KEY env var.")
        sys.exit(1)

    url = args.base_url.rstrip("/") + "/weather"
    headers = {"X-API-KEY": args.api_key}
    params = {
        "city": args.city,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "limit": args.limit,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except Exception as exc:
        print(f"[ERROR] Request failed: {exc}")
        sys.exit(1)

    print(f"Status: {resp.status_code}")
    try:
        print(resp.json())
    except ValueError:
        print(resp.text)

    if resp.status_code == 404:
        print("[HINT] Ensure backend is running and route /weather is available.")
    if resp.status_code == 401:
        print("[HINT] API key may be missing or invalid.")


if __name__ == "__main__":
    main()
