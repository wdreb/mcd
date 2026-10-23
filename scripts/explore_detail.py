#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
from mcd_mcp import McdMCP, extract_text, extract_json

def load_env_local():
    cfg = {}
    for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1); cfg[k.strip()]=v.strip()
    return cfg

cfg = load_env_local()
mcp = McdMCP(cfg["MCD_MCP_ENDPOINT"], cfg["MCD_MCP_TOKEN"])
mcp.connect()
res = mcp.call_tool("mall-product-detail", {"spuId": "1830"})
data = extract_json(extract_text(res))
def dump(o, ind=0, ml=200):
    if isinstance(o, dict):
        for k,v in o.items():
            if isinstance(v,(dict,list)):
                print("  "*ind+f"{k}: {type(v).__name__}({len(v)})"); dump(v,ind+1,ml)
            else:
                s=str(v); print("  "*ind+f"{k}: {s[:ml]!r}" if len(s)>ml else f"{k}: {s!r}")
    elif isinstance(o,list) and o:
        print("  "*ind+f"[0] of {len(o)}:"); dump(o[0],ind+1,ml)
dump(data)
