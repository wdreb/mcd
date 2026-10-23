#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦积分理财师 —— 命令行入口（只读 / dry-run）。

用法:
    python mcp_points_advisor.py            # 连接真实账号，生成策略报告到 stdout
    python mcp_points_advisor.py --save     # 同时写入 reports/strategy_report.md

安全约定:
    - 仅读取 query-my-account / mall-points-products / query-lottery-info /
      query-my-prizes / campaign-calendar / query-my-coupons。
    - 绝不调用 draw-lottery / mall-create-order / create-order 等写操作。
    - Token 从 .env 的 MCD_MCP_TOKEN 读取，不出现在任何输出里。
"""
import os
import sys
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from mcd_mcp import McdMCP  # noqa
from advisor import run_all  # noqa
from report import build_markdown  # noqa


def load_env(path):
    cfg = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def main():
    ap = argparse.ArgumentParser(description="麦麦积分理财师 (只读)")
    ap.add_argument("--save", action="store_true", help="同时写入 reports/strategy_report.md")
    args = ap.parse_args()

    cfg = load_env(os.path.join(HERE, ".env"))
    endpoint = cfg.get("MCD_MCP_ENDPOINT", "https://mcp.mcd.cn")
    token = cfg.get("MCD_MCP_TOKEN", "")
    if not token:
        print("✗ 未找到 MCD_MCP_TOKEN，请检查 .env（该文件已被 .gitignore 忽略，禁止提交）")
        sys.exit(2)

    print("→ 正在连接麦当劳 MCP（只读模式）…")
    mcp = McdMCP(endpoint, token)
    mcp.connect()
    print("✓ 连接成功，开始只读分析…\n")

    result = run_all(mcp)
    md = build_markdown(result)

    print(md)

    if args.save:
        out_dir = os.path.join(HERE, "reports")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "strategy_report.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n→ 报告已写入: {out_path}")


if __name__ == "__main__":
    main()
