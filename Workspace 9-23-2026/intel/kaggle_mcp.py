#!/usr/bin/env python3
"""Kaggle MCP client (bash-only, no extra deps).
Usage: python3 kaggle_mcp.py <tool_name> '<json args>'
Env: KAGGLE_API_TOKEN (default: our token A)."""
import json, os, sys, urllib.request

TOK = os.environ.get("KAGGLE_API_TOKEN", "KGAT_174ebff7462e0b34526c2936d51a2fc0")
URL = "https://www.kaggle.com/mcp"

def rpc(method, params, iid):
    body = json.dumps({"jsonrpc": "2.0", "id": iid, "method": method,
                       "params": params}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + TOK,
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
    for line in raw.split("\n"):
        if line.startswith("data: "):
            d = json.loads(line[6:])
            if "error" in d:
                raise RuntimeError(json.dumps(d["error"])[:400])
            return d.get("result", {})
    raise RuntimeError("no data line in response: " + raw[:200])

def main():
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    res = rpc("tools/call", {"name": tool, "arguments": args}, 1)
    # MCP content format: [{type: text, text: ...}]
    for c in res.get("content", []):
        if c.get("type") == "text":
            txt = c["text"]
            try:
                print(json.dumps(json.loads(txt), indent=1)[:6000])
            except Exception:
                print(txt[:6000])
        elif c.get("type") == "resource":
            blob = c.get("resource", {}).get("text", "")
            try:
                print(json.dumps(json.loads(blob), indent=1)[:6000])
            except Exception:
                print(blob[:6000])

if __name__ == "__main__":
    main()
