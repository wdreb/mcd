#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦积分理财师 —— 分析核心（仅只读调用麦当劳 MCP）。
所有函数只调用读工具：query-my-account / mall-points-products / mall-product-detail /
query-lottery-info / query-my-prizes / campaign-calendar / query-my-coupons。
绝不在此触发 draw-lottery / mall-create-order / create-order 等写操作。
"""
import re

from mcd_mcp import extract_text, extract_json


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 积分体检
def account_checkup(mcp):
    res = mcp.call_tool("query-my-account", {})
    data = (extract_json(extract_text(res)) or {}).get("data", {})
    avail = _f(data.get("availablePoint"))
    acc = _f(data.get("accumulativePoint"))
    expired = _f(data.get("expiredPoint"))
    next_exp = _f(data.get("nextMouthExpirePoint"))
    cur_exp = _f(data.get("currentMouthExpirePoint"))
    used = _f(data.get("usedPoint"))
    currency = data.get("currency", "麦享会积分")
    burn_rate = (expired / acc * 100) if (acc and acc > 0) else 0.0
    return {
        "currency": currency,
        "available": avail,
        "accumulative": acc,
        "expired": expired,
        "next_month_expire": next_exp,
        "current_month_expire": cur_exp,
        "used": used,
        "burn_rate_pct": round(burn_rate, 1),
    }


# ---------------------------------------------------------------- 商城性价比
def _extract_cash(text):
    """从商品名/描述里抽取「X元」的人民币价值（接口 price 字段对积分兑换品恒为 0，
    真实价值写在标题里，如『18.8元2份麦辣鸡翅』）。"""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*元", text)
    return float(m.group(1)) if m else None


def mall_ranking(mcp, top=10):
    res = mcp.call_tool("mall-points-products", {})
    data = extract_json(extract_text(res)) or {}
    products = data.get("data", []) if isinstance(data, dict) else []
    rows = []
    for p in products:
        point = _f(p.get("point"))
        cash_field = _f(p.get("price"))
        if point is None:
            continue
        name = p.get("spuName", "")
        selling = p.get("selling", "")
        # 真实价值来源：优先标题/描述里的「X元」，其次用接口 price 字段
        value = _extract_cash(name) or _extract_cash(selling) or cash_field
        if point > 0 and value:
            ratio = value / point
        else:
            ratio = None
        rows.append({
            "name": name,
            "point": point,
            "cash_field": cash_field,
            "value": value,
            "ratio": ratio,
            "cat": p.get("catName", ""),
            "down": p.get("downTime", ""),
        })
    ranked = sorted([r for r in rows if r["ratio"] is not None],
                    key=lambda r: r["ratio"], reverse=True)
    # point=0 的是「现金购」类（0 积分 + 现金），单列
    cash_only = [r for r in rows if r["point"] == 0]
    return ranked[:top], cash_only, len(rows)


# ---------------------------------------------------------------- 抽奖机会成本
def lottery_analysis(mcp):
    res = mcp.call_tool("query-lottery-info", {})
    data = (extract_json(extract_text(res)) or {}).get("data", {})
    draw_point = _f(data.get("drawPoint"))
    avail = _f(data.get("availablePoint"))
    prizes = data.get("prizes", [])
    types = {}
    for p in prizes:
        t = p.get("typeText", "未知")
        types[t] = types.get(t, 0) + 1
    times = int(avail // draw_point) if (draw_point and avail is not None) else 0
    return {
        "activity": data.get("activityName", ""),
        "draw_point": draw_point,
        "available": avail,
        "times": times,
        "prize_count": len(prizes),
        "prize_types": types,
        # API 不返回中奖概率，无法计算真实 EV —— 如实标注
        "has_probability": False,
    }


def my_prizes(mcp):
    res = mcp.call_tool("query-my-prizes", {})
    data = (extract_json(extract_text(res)) or {}).get("data", {})
    prizes = data.get("prizes", [])
    out = []
    for p in prizes:
        out.append({
            "name": p.get("name", ""),
            "type": p.get("prizeTypeText", ""),
            "status": p.get("statusText", ""),
            "time": p.get("recordTime", ""),
        })
    return out


# ---------------------------------------------------------------- 活动 & 优惠券
def campaigns(mcp):
    res = mcp.call_tool("campaign-calendar", {})
    text = extract_text(res)
    titles = re.findall(r"活动标题\*\*：([^\n]+)", text)
    dates = re.findall(r"####\s*([^\n]+)", text)
    clean = lambda s: re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", s).strip()
    return [clean(t) for t in titles if t.strip()], [d.strip() for d in dates if d.strip()]


def my_coupons(mcp):
    res = mcp.call_tool("query-my-coupons", {})
    text = extract_text(res)
    m = re.search(r"共\s*(\d+)\s*张", text)
    count = int(m.group(1)) if m else None
    names = [n.strip() for n in re.findall(r"##\s*([^\n]+)", text) if n.strip()]
    valids = [v.strip() for v in re.findall(r"有效期\*\*：([^\n<]+)", text) if v.strip()]
    expiring_today = "今日到期" in text
    return count, names, valids, expiring_today


# ---------------------------------------------------------------- 汇总
def run_all(mcp):
    """一次性执行全部只读分析，返回结构化结果。"""
    return {
        "account": account_checkup(mcp),
        "mall": mall_ranking(mcp),
        "lottery": lottery_analysis(mcp),
        "prizes": my_prizes(mcp),
        "campaigns": campaigns(mcp),
        "coupons": my_coupons(mcp),
    }
