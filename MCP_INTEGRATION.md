# MCP 接入说明（MCP_INTEGRATION.md）

## 1. 使用的麦当劳 MCP Server

- **服务地址**：`https://mcp.mcd.cn`
- **协议**：MCP Streamable HTTP（JSON-RPC 2.0）
- **鉴权**：`Authorization: Bearer <Token>`，Token 由用户在 `https://open.mcd.cn/mcp` 登录后获取，与个人麦当劳账号绑定。
- **会话**：首次 `initialize` 后服务端返回 `Mcp-Session-Id`，后续请求须在请求头携带。

> 客户端实现见 `src/mcd_mcp.py`，仅依赖 Python 标准库（`urllib` / `json`），无第三方依赖，便于评委直接运行。

## 2. 实际使用的工具（Tools）

本项目**仅调用只读工具**，共 7 个：

| 工具名 | 用途 | 是否写操作 |
| --- | --- | --- |
| `query-my-account` | 查询积分余额、累计、已过期、按月过期情况 | 否 |
| `mall-points-products` | 拉取积分商城商品列表（含积分价、参考价） | 否 |
| `mall-product-detail` | 拉取单品详情（校验积分价/现金价字段语义） | 否 |
| `query-lottery-info` | 抽奖活动信息：单次消耗积分、奖池构成 | 否 |
| `query-my-prizes` | 查询本人已中奖品 | 否 |
| `query-my-coupons` | 查询本人可用优惠券及有效期 | 否 |
| `campaign-calendar` | 近期营销活动日历 | 否 |

**明确不调用**（写操作，需用户本人显式授权才可能在扩展中实现）：`draw-lottery`、`mall-create-order`、`create-order`、`cancel-order`、`party-order-create`、`auto-bind-coupons` 等。

## 3. 调用流程（Call Flow）

```
用户运行 python mcp_points_advisor.py
        │
        ├─ 读取本地 .env（仅 MCD_MCP_TOKEN / MCD_MCP_ENDPOINT）
        ▼
   McdMCP.connect()
        ├─ initialize  → 建立会话，拿到 Mcp-Session-Id
        └─ notifications/initialized
        ▼
   advisor.run_all(mcp)  ——  全部只读调用
        ├─ account_checkup      → query-my-account
        ├─ mall_ranking         → mall-points-products (+ mall-product-detail 校验)
        ├─ lottery_analysis     → query-lottery-info
        ├─ my_prizes            → query-my-prizes
        ├─ campaigns            → campaign-calendar
        └─ my_coupons           → query-my-coupons
        ▼
   report.build_markdown(result)  →  Markdown 策略报告
        ▼
   输出到终端 / reports/strategy_report.md（本地，不落盘个人敏感数据）
```

## 4. 业务价值

- **止损**：用 `query-my-account` 的逐月过期字段，把「积分会蒸发」这件事量化成「蒸发率 77%」这种刺眼数字，驱动用户行动。
- **确定性收益最大化**：用 `mall-points-products` 解析出每件商品的「人民币价值 ÷ 消耗积分」，给出可执行的兑换优先级。
- **理性看待抽奖**：`query-lottery-info` 暴露单次成本与奖池，但**不暴露概率**；本项目据此做「机会成本」分析并诚实声明无法算 EV，规避误导，反而建立信任。
- **临期提醒**：结合 `query-my-coupons` 的「今日到期」与 `campaign-calendar` 的近期活动，把策略落成当下的动作。

## 5. 配置示例

见 `mcp-config.example.json`：Token 一律以 `${MCD_MCP_TOKEN}` 环境变量占位，真实凭据不进入任何提交文件。
