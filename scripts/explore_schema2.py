#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聚焦探查：mall-points-products 全字段、query-lottery-info 单个奖品全字段 + drawDecision。"""
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


def dump(obj, indent=0, maxlen=200):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                print("  " * indent + f"{k}: {type(v).__name__}({len(v)})")
                dump(v, indent + 1, maxlen)
            else:
                s = str(v)
                if len(s) > maxlen:
                    s = s[:maxlen] + "…"
                print("  " * indent + f"{k}: {s!r}")
    elif isinstance(obj, list):
        if obj:
            print("  " * indent + f"[0] of {len(obj)}:")
            dump(obj[0], indent + 1, maxlen)


def main():
    cfg = load_env_local()
    mcp = McdMCP(cfg["MCD_MCP_ENDPOINT"], cfg["MCD_MCP_TOKEN"])
    mcp.connect()

    print("#" * 60)
    print("# mall-points-products 全字段")
    res = mcp.call_tool("mall-points-products", {})
    data = extract_json(extract_text(res))
    print("top type:", type(data).__name__)
    if isinstance(data, dict):
        for k in data:
            v = data[k]
            print(f"  top-key {k}: {type(v).__name__}({len(v) if hasattr(v,'__len__') else '?'})")
        # 找到商品列表
        prod_list = None
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                prod_list = v
                print(f"  → 商品列表疑似在 key={k}")
                break
        if prod_list:
            print("  样本商品全字段：")
            dump(prod_list[0], 2)
            print(f"  商品总数: {len(prod_list)}")
    else:
        print("  原始文本前 500：", extract_text(res)[:500])

    print("#" * 60)
    print("# query-lottery-info 单奖品全字段 + drawDecision")
    res = mcp.call_tool("query-lottery-info", {})
    data = extract_json(extract_text(res))
    if data and "data" in data:
        d = data["data"]
        print("  drawPoint:", d.get("drawPoint"))
        print("  activityName:", d.get("activityName"))
        print("  drawDecision.nextConsumption 全字段:")
        dc = d.get("drawDecision", {}).get("nextConsumption", {})
        dump(dc, 2)
        prizes = d.get("prizes", [])
        print(f"  prizes 数量: {len(prizes)}")
        if prizes:
            print("  单个奖品全字段：")
            dump(prizes[0], 2)


if __name__ == "__main__":
    main()
