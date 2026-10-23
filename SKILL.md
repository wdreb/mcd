---
name: mcd-points-advisor
description: 基于麦当劳官方 MCP，只读分析用户的麦享会积分，生成「积分体检 + 商城性价比榜 + 抽奖机会成本 + 止损建议」策略报告。适用于帮助用户理性管理积分、避免积分过期、识别高性价比兑换、理性看待积分抽奖的场景。
---

# 麦麦积分理财师（McPoints Advisor）

一个只读、安全、可复现的麦当劳积分策略 Skill。它连接用户的麦当劳账号（通过官方 MCP），
把所有「看不见的积分账本」变成一份可执行的兑换建议。

## 何时使用

- 用户想了解自己的麦当劳积分「值多少钱」「怎么花最划算」。
- 用户担心积分过期、不知道有哪些兑换更值。
- 用户问「积分抽奖划不划算」「抽奖能不能算期望收益」。
- 需要一份可落地的「本月该做啥」积分行动清单。

## 核心原则（务必遵守）

1. **只读优先，绝不自动写**：默认只调用读工具（`query-my-account` /
   `mall-points-products` / `mall-product-detail` / `query-lottery-info` /
   `query-my-prizes` / `query-my-coupons` / `campaign-calendar`）。
   **绝不在未获用户显式确认的情况下调用** `draw-lottery` / `mall-create-order` /
   `create-order` 等写操作。
2. **诚实披露边界**：麦当劳抽奖接口**不返回中奖概率**，因此**不能计算真实期望收益（EV）**。
   只能做「机会成本」分析，并明确告知用户这一点。不得暗示「抽奖必赚」。
3. **凭据不出本地**：Token 仅从环境变量 `MCD_MCP_TOKEN` 读取，写入本地 `.env`（gitignore），
   任何提交文件只用 `${MCD_MCP_TOKEN}` 占位。

## 运行方式

```bash
# 配置 .env: MCD_MCP_ENDPOINT=https://mcp.mcd.cn, MCD_MCP_TOKEN=<用户本地Token>
python mcp_points_advisor.py            # 报告输出到终端
python mcp_points_advisor.py --save     # 额外写入 reports/strategy_report.md
```

## 模块说明

- `src/mcd_mcp.py`：麦当劳 MCP Streamable HTTP 客户端（零依赖）。
- `src/advisor.py`：分析核心，全部只读调用，返回结构化结果。
- `src/report.py`：将结构化结果渲染为 Markdown 策略报告。

## 输出样例（节选）

> **积分体检**：当前可用 137.2，累计 600.1，**已蒸发 462.9（蒸发率 77.1%）**。
> **商城性价比榜**：18.8元麦辣鸡腿汉堡两件套（50 积分，0.376 元/积分）最划算。
> **抽奖机会成本**：单次 24 积分，可抽约 5 次；API 无概率，无法算 EV，建议「先兑确定性好物，闲余积分当娱乐」。

完整样例见 `examples/sample_report.md`。
