"""Local MCP host test for analysis agent (stdio)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from typing import Any, Dict


def _build_packet(message: Dict[str, Any]) -> bytes:
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def _read_response(stream, timeout: float = 10.0) -> Dict[str, Any]:
    deadline = time.time() + timeout
    while True:
        if time.time() > deadline:
            raise TimeoutError("Timed out waiting for JSON response")
        line = stream.readline()
        if not line:
            raise RuntimeError("Stream closed while waiting for response")
        try:
            return json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            continue


def main():
    cmd = [sys.executable, "-u", "mcp_servers/analysis_agent_server.py"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.stdin is None or proc.stdout is None:
        raise RuntimeError("Failed to open pipes")

    try:
        init_req = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"clientInfo": {"name": "local-test", "version": "0.0.1"}, "capabilities": {}},
        }
        proc.stdin.write(_build_packet(init_req))
        proc.stdin.flush()
        init_resp = _read_response(proc.stdout)
        print("=== initialize ===")
        print(json.dumps(init_resp, ensure_ascii=False, indent=2))

        list_req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        proc.stdin.write(_build_packet(list_req))
        proc.stdin.flush()
        list_resp = _read_response(proc.stdout)
        print("=== tools/list ===")
        print(json.dumps(list_resp, ensure_ascii=False, indent=2))

        call_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "analysis_describe_timeseries",
                "arguments": {
                    "city": "北京",
                    "metric": "temp_max",
                    "start_date": "2025-11-01",
                    "end_date": "2025-11-15",
                },
            },
        }
        proc.stdin.write(_build_packet(call_req))
        proc.stdin.flush()
        call_resp = _read_response(proc.stdout)
        print("=== tools/call analysis_describe_timeseries ===")
        print(json.dumps(call_resp, ensure_ascii=False, indent=2))
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        if proc.stderr is not None:
            err = proc.stderr.read()
            if err:
                sys.stderr.buffer.write(err)


if __name__ == "__main__":
    main()
