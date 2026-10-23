#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 advisor.run_all 的结构化结果渲染成一份可读的 Markdown 策略报告。"""


def _fmt_points(x):
    if x is None:
        return "—"
    return f"{x:g}"


def build_markdown(r):
    acc = r["account"]
    ranked, free, total_products = r["mall"]
    lot = r["lottery"]
    prizes = r["prizes"]
    camp_titles, camp_dates = r["campaigns"]
    coupon_count, coupon_names, coupon_valids, expiring_today = r["coupons"]

    L = []
    L.append("# 麦麦积分理财师 · 个人积分策略报告\n")
    L.append("> 本报告由 WorkBuddy Skill「麦麦积分理财师」基于你的麦当劳账号**只读**数据生成，"
             "未执行任何抽奖、下单或兑换写操作。所有结论均为建议，最终决策由你本人确认。\n")

    # 一、积分体检
    L.append("## 一、积分体检\n")
    L.append(f"- 账户积分类型：{acc['currency']}")
    L.append(f"- **当前可用积分：{_fmt_points(acc['available'])}**")
    L.append(f"- 累计获得积分：{_fmt_points(acc['accumulative'])}")
    L.append(f"- 已过期积分：{_fmt_points(acc['expired'])}（历史蒸发率 {acc['burn_rate_pct']}%）")
    L.append(f"- 本月将过期：{_fmt_points(acc['current_month_expire'])}　下月将过期：{_fmt_points(acc['next_month_expire'])}")
    L.append(f"- 累计已消耗：{_fmt_points(acc['used'])}")
    if acc["expired"] and acc["available"] is not None and acc["expired"] > (acc["available"] or 0):
        L.append("\n**止损提醒**：你的积分存在「按月清零」机制，已蒸发积分远高于当前可用余额。"
                 "请优先在到期前把可用积分花出去，别让它们继续沉睡。\n")

    # 二、商城性价比
    L.append("## 二、积分商城性价比榜\n")
    L.append(f"共检索到 {total_products} 件商城商品，按「人民币参考价值 ÷ 消耗积分」排序，元/积分 越高越划算：\n")
    L.append("| 排名 | 商品 | 消耗积分 | 参考价值 | 性价比(元/积分) | 分类 |")
    L.append("| --- | --- | ---: | ---: | ---: | --- |")
    for i, p in enumerate(ranked, 1):
        val = _fmt_points(p['value'])
        L.append(f"| {i} | {p['name']} | {_fmt_points(p['point'])} | "
                 f"¥{val} | {p['ratio']:.3f} | {p['cat']} |")
    if free:
        L.append(f"\n另有 {len(free)} 件为「0 积分现金购」商品（如 `{free[0]['name']}`），"
                 "多为现金+积分组合或限时活动，按需关注。\n")

    # 三、抽奖机会成本
    L.append("## 三、抽奖机会成本分析\n")
    L.append(f"- 抽奖活动：{lot['activity']}")
    L.append(f"- 单次抽奖消耗：**{_fmt_points(lot['draw_point'])} 积分**")
    L.append(f"- 当前可用积分可抽约：**{lot['times']} 次**")
    if lot["prize_types"]:
        comp = "、".join(f"{k}×{v}" for k, v in lot["prize_types"].items())
        L.append(f"- 奖池构成（共 {lot['prize_count']} 项）：{comp}")
    L.append("\n**重要说明**：麦当劳 MCP 的抽奖接口**不返回各奖项中奖概率**，"
             "因此本工具**无法计算真实期望收益（EV）**，也不做任何「抽奖必赚」的承诺。"
             "下面是「机会成本」视角：\n")
    if lot["draw_point"] and ranked:
        best = ranked[0]
        cost_once = lot["draw_point"]
        equiv = f"换 1 份「{best['name']}」（{_fmt_points(best['point'])}积分）"
        L.append(f"- 每抽 1 次 = 花掉 {_fmt_points(cost_once)} 积分，这些积分在商城约可 {equiv}；")
        L.append(f"- 抽满 {lot['times']} 次 = 消耗 {_fmt_points(cost_once * lot['times'])} 积分，"
                 "相当于把一笔可观的「确定性兑换额度」换成「极低概率的实物奖」；")
        L.append("- **结论**：把积分用于高性价比商城兑换是「确定性收益」，抽奖是「娱乐性消费」。"
                 "建议先兑确定性好物，闲余积分再当娱乐抽着玩。\n")

    # 四、我的奖品 & 优惠券
    L.append("## 四、我的奖品与优惠券\n")
    if prizes:
        L.append(f"已中奖品 {len(prizes)} 件：")
        for p in prizes:
            L.append(f"- {p['name']}（{p['type']}）· 状态：{p['status']} · 获得于 {p['time']}")
    else:
        L.append("- 暂无中奖记录。")
    L.append("")
    if coupon_count is not None:
        flag = "（含**今日到期**，请尽快用掉！）" if expiring_today else ""
        L.append(f"可用优惠券 {coupon_count} 张{flag}")
        for n, v in zip(coupon_names, coupon_valids):
            L.append(f"- {n}　有效期：{v}")

    # 五、本月活动
    L.append("\n## 五、近期活动（来自活动日历）\n")
    if camp_titles:
        L.append(f"共识别到 {len(camp_titles)} 个活动标题，例如：")
        for t in camp_titles[:8]:
            L.append(f"- {t}")
    else:
        L.append("- 当前活动日历未返回可解析的标题。")

    # 六、综合策略
    L.append("\n## 六、给你的三点行动建议\n")
    tips = []
    if acc["expired"] and (acc["available"] or 0) < acc["expired"]:
        tips.append("**先止损**：可用积分远少于已蒸发积分，说明过去有积分白白过期。"
                    "本月/下月将过期的积分，立刻排进兑换清单。")
    if ranked:
        b = ranked[0]
        tips.append(f"**兑确定性好物**：当前性价比最高的是「{b['name']}」（{b['ratio']:.2f} 元/积分），"
                    "优先用它把积分变现。")
    tips.append("**抽奖当娱乐**：积分抽奖无概率、无真 EV，闲余积分抽着玩即可，别把「必中大奖」当理财。")
    if expiring_today:
        tips.append("**今日到期优惠券**：列表里有今日到期的券，今天不用就废了。")
    for i, t in enumerate(tips, 1):
        L.append(f"{i}. {t}")

    L.append("\n---\n*报告生成于只读模式；如需执行真实兑换/抽奖，请在本人确认下单独操作，"
             "本 Skill 默认不自动触发任何写操作。*")
    return "\n".join(L)
