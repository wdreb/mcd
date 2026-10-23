#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读探查：打印各读工具返回的 JSON 结构（键名 + 样例），用于编写解析逻辑。绝不调用写工具。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from mcd_mcp import McdMCP, extract_text, extract_json  # noqa


def load_env_local():
    cfg = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def summarize(obj, depth=0, maxlen=120):
    """紧凑展示 JSON 结构，不刷屏。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                n = len(v)
                print("  " * depth + f"- {k}: {type(v).__name__}({n})")
                if depth < 2:
                    summarize(v, depth + 1, maxlen)
            else:
                s = str(v)
                if len(s) > maxlen:
                    s = s[:maxlen] + "…"
                print("  " * depth + f"- {k}: {s!r}")
    elif isinstance(obj, list):
        if obj:
            print("  " * depth + f"[0] of {len(obj)}:")
            summarize(obj[0], depth + 1, maxlen)


def main():
    cfg = load_env_local()
    mcp = McdMCP(cfg["MCD_MCP_ENDPOINT"], cfg["MCD_MCP_TOKEN"])
    mcp.connect()
    print("已连接。开始探查只读工具结构……\n")

    targets = [
        "query-my-account",
        "mall-points-products",
        "query-lottery-info",
        "query-my-prizes",
        "campaign-calendar",
        "query-my-coupons",
    ]
    for name in targets:
        if not mcp.has_tool(name):
            print(f"[跳过] 无工具 {name}")
            continue
        print("=" * 60)
        print(f"工具: {name}")
        try:
            res = mcp.call_tool(name, {})
            text = extract_text(res)
            data = extract_json(text)
            if data is None:
                print("  ⚠ 未能解析出 JSON，原始文本前 300 字符：")
                print("  ", text[:300].replace("\n", " "))
            else:
                summarize(data)
        except Exception as e:
            print(f"  ✗ 调用异常: {e}")
        print()


if __name__ == "__main__":
    main()
