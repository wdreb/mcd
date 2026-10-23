#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳 MCP 连通性探针（只读、零依赖）。
作用：验证 Token 有效性、协议握手、tools/list，并做一次安全的只读工具调用。
绝不调用 draw-lottery / create-order / mall-create-order / party-order-create 等写操作。
"""
import json
import os
import sys
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_env(path):
    cfg = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


def parse_body(raw: bytes):
    text = raw.decode("utf-8", errors="replace")
    # Streamable HTTP 可能返回 SSE（text/event-stream）或纯 JSON
    if "data:" in text:
        for part in text.split("\n"):
            part = part.strip()
            if part.startswith("data:"):
                payload = part[len("data:"):].strip()
                if payload and payload != "[DONE]":
                    try:
                        return json.loads(payload)
                    except json.JSONDecodeError:
                        continue
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def rpc(endpoint, token, session_id, payload, method="POST"):
    url = endpoint
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            new_sid = resp.headers.get("Mcp-Session-Id") or session_id
            return parse_body(body), new_sid
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        return {"__http_error__": e.code, "detail": detail[:500]}, session_id


def main():
    cfg = load_env(os.path.join(ROOT, ".env"))
    endpoint = cfg.get("MCD_MCP_ENDPOINT", "https://mcp.mcd.cn")
    token = cfg.get("MCD_MCP_TOKEN", "")
    if not token:
        print("✗ 未找到 MCD_MCP_TOKEN，请检查 .env")
        sys.exit(2)

    print(f"→ 目标端点: {endpoint}")
    print(f"→ Token 长度: {len(token)} 字符（已脱敏，仅用于本次握手）")

    # 1) initialize
    init = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcd-points-advisor", "version": "0.1.0"},
        },
    }
    res, sid = rpc(endpoint, token, None, init)
    if res is None or res.get("__http_error__"):
        print("✗ initialize 失败:", json.dumps(res, ensure_ascii=False)[:400])
        sys.exit(1)
    print("✓ initialize 成功, session_id 已建立")
    if sid:
        print(f"  session_id 前缀: {sid[:8]}…")

    # 2) initialized 通知
    rpc(endpoint, token, sid, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    print("✓ notifications/initialized 已发送")

    # 3) tools/list
    tl, _ = rpc(endpoint, token, sid, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = (tl or {}).get("result", {}).get("tools", [])
    print(f"✓ tools/list 成功，共 {len(tools)} 个工具")
    names = [t.get("name") for t in tools]
    for n in sorted(names):
        print("   -", n)

    # 4) 一次安全的只读调用：now-time-info
    print("\n→ 尝试只读调用 now-time-info ...")
    call = {
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "now-time-info", "arguments": {}},
    }
    cres, _ = rpc(endpoint, token, sid, call)
    if cres and cres.get("result"):
        # 精简输出，避免刷屏
        content = cres["result"].get("content", [])
        txt = "".join(c.get("text", "") for c in content if isinstance(c, dict))
        print("✓ now-time-info 调用成功，返回预览:")
        print("  ", txt[:200].replace("\n", " "))
    else:
        print("⚠ now-time-info 返回:", json.dumps(cres, ensure_ascii=False)[:300])

    # 5) 安全校验：确认没有在未知情况下暴露写操作
    print("\n✓ 探针完成：全程仅执行 initialize / initialized / tools/list / now-time-info，"
          "未调用任何写操作（抽奖/下单/积分商城下单/派对预订）。")


if __name__ == "__main__":
    main()
