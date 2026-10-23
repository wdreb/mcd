# 麦麦积分理财师 · McPoints Advisor

> 基于麦当劳官方 MCP 能力开发的 WorkBuddy Skill：把你的「麦享会积分」从一笔糊涂账，变成一份可执行的兑换策略。
> 参赛作品 · 麦当劳 × 腾讯 WorkBuddy「程序员创意开发大赛」（2026）。

---

## 一句话介绍

**麦麦积分理财师** 连接你的麦当劳账号（只读），自动完成四件事：

1. **积分体检**——可用 / 累计 / 已蒸发积分，算出你的「积分蒸发率」。
2. **商城性价比榜**——把积分商城 50 件商品按「人民币价值 ÷ 消耗积分」排序，告诉你哪件最划算。
3. **抽奖机会成本**——基于真实抽奖接口，算出「每抽一次 = 花掉多少积分」，并诚实标注：API 不返回中奖概率，**本工具绝不谎称能算期望收益**。
4. **止损建议**——结合即将过期的积分、今日到期的优惠券、近期活动，给出 3~4 条可落地动作。

所有分析**默认只读、绝不自动抽奖或下单**。

---

## 为什么做这个（差异化）

大赛里大多数作品扎堆在「点餐 / 省钱 / 卡路里」。我们选了一条**蓝海 + 安全 + 易传播**的赛道：

- **积分经济是被忽视的金矿**：积分按月清零、过期不提醒，绝大多数人根本不知道自己亏了多少。
- **诚实是最大卖点**：抽奖接口不暴露中奖概率，竞品常暗示「抽奖必赚」；我们反其道而行，做「机会成本」视角的理性分析，反而更可信、更适合技术自媒体传播。
- **纯只读、零风险**：只用读接口，不碰支付与下单，账号安全无虞。

---

## 功能特性

| 模块 | 调用的麦当劳 MCP 工具 | 输出 |
| --- | --- | --- |
| 积分体检 | `query-my-account` | 可用/累计/已蒸发积分、蒸发率、止损提醒 |
| 商城性价比 | `mall-points-products` + `mall-product-detail` | 元/积分 排序榜、现金购清单 |
| 抽奖机会成本 | `query-lottery-info` + `query-my-prizes` | 单次成本、可抽次数、奖池构成、诚实声明 |
| 优惠券 / 活动 | `query-my-coupons` + `campaign-calendar` | 到期提醒、活动清单 |

---

## 安装与运行

**环境要求**：Python 3.10+，**零第三方依赖**（仅用标准库 `urllib` / `json` / `re`）。

```bash
# 1. 克隆仓库
git clone <your-repo-url> && cd maidanglao

# 2. 配置 Token（仅本地，禁止提交）
cp .env.example .env
#   然后编辑 .env，填入你的麦当劳 MCP Token：
#   MCD_MCP_TOKEN=你的真实Token（从 https://open.mcd.cn/mcp 获取）
#   MCD_MCP_ENDPOINT=https://mcp.mcd.cn

# 3. 运行（只读分析，不抽奖不下单）
python mcp_points_advisor.py            # 报告输出到终端
python mcp_points_advisor.py --save     # 同时写入 reports/strategy_report.md
```

> ⚠️ Token 是个人账号凭据，**仅存于本地 `.env`**（已被 `.gitignore` 忽略）。
> 提交到 GitHub 前请确认 `.env` 不会被推送；仓库内只保留 `.env.example` 占位。

---

## 目录结构

```
maidanglao/
├── README.md                  # 本文件
├── CONTEST_DECLARATION.md     # 参赛声明（官方模板，未修改）
├── MCP_INTEGRATION.md         # MCP 接入说明
├── mcp-config.example.json    # WorkBuddy/MCP 客户端配置示例（仅环境变量占位）
├── SKILL.md                   # WorkBuddy Skill 定义
├── workbuddy.md               # WorkBuddy 专项奖励：完整开发对话记录
├── mcp_points_advisor.py      # 命令行入口（只读）
├── src/
│   ├── mcd_mcp.py             # 麦当劳 MCP Streamable HTTP 客户端（零依赖）
│   ├── advisor.py             # 分析核心（仅只读调用）
│   └── report.py              # Markdown 报告渲染
├── scripts/                   # 开发期探针与 schema 探查（透明可复现）
├── examples/
│   └── sample_report.md       # 一次真实运行的样例报告
├── .env.example               # Token 配置模板
└── .gitignore
```

---

## 安全与合规

- **只读优先**：默认只调用读工具；抽奖、下单、积分商城兑换等写操作**需要用户本人显式确认**，Skill 不会自动触发。
- **不落盘个人数据**：所有账号数据仅在内存中用于本次报告，不写入任何文件（除用户主动 `--save` 的本地报告）。
- **无凭据硬编码**：仓库内无任何 Token / 密钥，配置文件一律使用 `${MCD_MCP_TOKEN}` 占位。
- 详见 `CONTEST_DECLARATION.md` 与 `MCP_INTEGRATION.md`。

---

## 已知边界（如实披露）

- 抽奖接口**不返回中奖概率**，故无法计算真实期望收益（EV）；本工具以「机会成本」替代，并明确标注。
- 商城商品的「人民币价值」从商品标题中解析（如「18.8元2份麦辣鸡翅」），个别无明确标价的商品会被跳过或单列。
- 活动日历 / 优惠券接口返回的是富文本，解析基于常见版式正则，极端格式可能漏解析，但不影响主流程。

---

## 许可证

本项目以开源形式发布，供参赛与学习使用。
