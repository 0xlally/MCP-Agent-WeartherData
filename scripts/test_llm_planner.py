"""Quick test script to verify LLM returns clean JSON for planner prompts.

Usage (set env before run):
  $env:DEEPSEEK_API_KEY="sk-..."; python scripts/test_llm_planner.py
Optional:
  $env:DEEPSEEK_BASE="https://api.deepseek.com/v1"
"""
from __future__ import annotations

import json
import os
import sys
import textwrap
import urllib.request
import urllib.error

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
BASE = os.getenv("DEEPSEEK_BASE", "https://api.deepseek.com/v1")
KEY = os.getenv("DEEPSEEK_API_KEY")

PROMPT = textwrap.dedent(
    """
    你是一个工具规划器。仅返回 JSON 对象，格式如下：
    {"tool": "data_get_range", "arguments": {"city": "北京", "start_date": "2025-11-01", "end_date": "2025-11-15", "limit": 200}}
    工具列表：
      - data_get_range(city,start_date,end_date,limit)
      - data_get_dataset_overview()
      - data_check_coverage(city,start_date,end_date)
      - data_custom_query(fields,city,start_date,end_date,limit)
      - data_update_city_range(city,start_date,end_date)
    只返回 JSON，不要包含任何额外文本、代码块或解释。
    请为“北京 2025-11-01 到 2025-11-15 的天气，列出每天最高温” 生成调用计划。
    """
).strip()


def main() -> int:
    if not KEY:
        print("Missing DEEPSEEK_API_KEY env", file=sys.stderr)
        return 1

    body = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": PROMPT},
        ],
        "temperature": 0,
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE.rstrip('/')}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        print(f"HTTPError {e.code}: {e.reason}", file=sys.stderr)
        print("--- raw response ---")
        print(raw)
        return 1
    print("--- raw response ---")
    print(raw)

    try:
        js = json.loads(raw)
        content = js.get("choices", [{}])[0].get("message", {}).get("content", "")
        print("--- extracted content ---")
        print(content)
        parsed = json.loads(content)
        print("--- parsed JSON ---")
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except Exception as e:
        print("Failed to parse JSON:", e, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
