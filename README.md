# coc-qq-bot — 部落冲突 QQ 群助手（官方平台 · 被动回复版）

QQ 群机器人：群里 `@机器人 <指令>`，查询绑定部落的公开信息（成员、部落战敌我情况等）。
数据来自 **Supercell 官方 Clash of Clans API**（免费），消息通道走 **QQ 开放平台官方接口**（合规、不封号）。
不做主动播报，纯被动问答 —— 不需要 LLM，**零 AI 费用**。

> ⚠️ **平台现状（2026-07）**：QQ 开放平台 2026-01-31 起关闭了沙箱 QQ 群配置，
> 所有新机器人暂时只能**私聊**（沙箱消息列表成员）和频道使用，群场景官方标注"敬请期待"。
> 本项目私聊/群聊两套 handler 都已实现：现在私聊可用，平台开放群配置后群聊自动生效。

## 指令设计

指令体系：**主 tag + 横杠子功能**（如 `联赛-积分榜`）。带 `[#TAG]` 的指令可查任意部落，不带则查已绑定的。

| 分类 | 指令 | 说明 |
|---|---|---|
| 部落 | `绑定 #TAG` / `解绑` | 换绑直接重新绑定即可覆盖 |
| | `部落 [#TAG]` | 概况：等级/段位/胜平负/连胜/首都 |
| | `成员 [#TAG]` | 成员列表（大本/奖杯/捐兵） |
| | `捐兵` / `摸鱼榜` | 捐兵榜 / 0捐兵+联赛漏刀+部落战未出刀 三合一点名 |
| | `突袭` / `突袭-催刀` | 都城突袭统计 / 没打满6刀的名单 |
| | `搜索 部落名` | 按名字找部落 TAG |
| 部落战 | `部落战`（=`战况`） | 比分 + 剩余时间 + 未出刀 + 胜率预估 |
| | `部落战-对阵` | 对位本数表 |
| | `部落战-催刀` / `部落战-敌刀` | 剩余刀数名单（普通战每人2刀） |
| | `部落战-复盘` | 打完后逐人战报（每刀星数/摧毁率/目标） |
| | `部落战-战绩`（=`战绩 [#TAG]`） | 最近部落战日志 |
| 联赛 | `联赛` | 分组与同组部落 |
| | `联赛-积分榜` | 小组排名（胜场含+10⭐） |
| | `联赛-奖章` | 奖章计算器：按段位/排名/个人星数预估每人所得 |
| | `联赛-对阵` / `联赛-2` | 备战日=对位本数表+胜率预估；战斗日=紧凑战报（比分、双方未出刀 x/n、胜率、我方催刀名单） |
| | `联赛-催刀` / `联赛-敌刀` | 我方/敌方未出刀名单（一行一个，方便@人） |
| | `联赛-复盘 [场次]` | 已结束场次逐人复盘：星数/摧毁率/打高打低、三星榜、漏刀名单 |
| | `联赛-总结` | 赛季结算：最终排名、逐场胜负、MVP、全员奖章 |
| 玩家 | `玩家 #TAG` | 详情：本/奖杯/战争星/英雄一览/职位 |
| | `玩家-英雄/部队/法术 #TAG` | 全部英雄/兵种(含攻城/宠物)/法术的等级与满级 |
| | `玩家-建议 #TAG` / `我-建议` | 升级建议：英雄缺口 > 主流兵种 > 关键法术 + 本级段提示 |
| 我 | `绑定玩家 #TAG` / `解绑玩家` | 绑定自己的账号 |
| | `我` / `我-英雄/部队/法术` | 查自己（工人/升级队列官方 API 不提供，做不了） |
| | `我-成长` | 成长追踪：奖杯/战争星/英雄总级等随时间变化（机器人每12h自动快照） |

旧扁平指令（`对阵`/`积分榜`/`奖章`）保留为别名。私聊直接发指令；群聊 @ 机器人后发。

## 架构

```
QQ 群消息 (@bot xxx)
   → QQ 开放平台 Webhook 回调（HTTPS POST，Ed25519 验签）
   → FastAPI (app/main.py) 解析指令
   → CoC API 客户端 (app/coc.py，带 60s 缓存)
   → 组装文本 → 调 QQ v2 API 被动回复（带 msg_id，不占主动消息配额）
```

- `app/main.py` — Webhook 入口：验签、回调地址校验（op=13）、消息分发
- `app/qq_api.py` — 获取 access_token、发送群消息
- `app/coc.py` — Clash of Clans API 封装 + 简单缓存
- `app/commands.py` — 指令解析与文本排版
- `app/store.py` — SQLite 存 群↔部落 绑定关系

## 上线前置步骤

1. **QQ 开放平台**：[q.qq.com](https://q.qq.com) 注册**个人开发者**（免费）→ 创建机器人 → 拿到 `AppID` / `AppSecret` → 开发设置里配置 Webhook 回调地址（必须是 HTTPS + 域名）。先用**沙箱环境**（拉一个测试群）开发，过审后正式发布。
   - 个人开发者限制：机器人可加入的群数量有上限、部分高级接口仅企业可用；纯被动问答不受影响。
2. **Supercell 开发者**：[developer.clashofclans.com](https://developer.clashofclans.com) 注册（免费）→ 创建 API Key，**Key 绑定服务器出口 IP**。
   - 如果服务器 IP 可能变，用社区通行的 [RoyaleAPI 代理](https://docs.royaleapi.com/proxy.html)：把 `45.79.218.79` 加入 Key 白名单，请求发往 `https://cocproxy.royaleapi.dev`（本项目 `COC_BASE_URL` 可配）。
3. **服务器 + 域名 + HTTPS**（见下方费用）。本地开发期用 `cloudflared tunnel` 免费获得临时 HTTPS 地址即可，不用先买服务器。

## 💰 费用明细（重点）

| 项目 | 费用 | 说明 |
|---|---|---|
| QQ 开放平台 | **¥0** | 个人开发者注册、沙箱、发布均免费 |
| Clash of Clans API | **¥0** | 官方免费，有限流（够用） |
| LLM / AI | **¥0** | 查询式回答不需要大模型 |
| 服务器（必需） | **~¥15–40/月** | Webhook 必须有公网 HTTPS。推荐**境外便宜 VPS**（$3–5/月，如 RackNerd/Vultr）：① 免域名备案 ② 访问 Supercell API（境外服务器）反而更快更稳 |
| 域名（必需） | **~¥10–70/年** | Webhook 回调要求域名 HTTPS；`.top/.xyz` 首年几块钱，`.com` ~¥65/年 |
| HTTPS 证书 | **¥0** | Let's Encrypt / Caddy 自动签 |
| （可选）国内服务器路线 | ¥99–300/年 | 腾讯云轻量新用户促销价；但域名需 **ICP 备案**（免费、耗时 2–4 周），且访问 CoC API 可能不稳，需自架代理 —— **不推荐** |

**结论：全年总成本 ≈ ¥200–400（一台小 VPS + 一个便宜域名），开发期 ¥0。**
唯一的"隐性费用"是时间：QQ 机器人正式发布需要平台审核（免费，数天）。

## 运行（两种模式）

### ✅ WebSocket 模式（开发期首选，2026-07 实测可用）

出站长连接，**不需要公网 IP / 域名 / 备案 / 隧道**，换网络也能跑：

```bash
.venv/bin/python -m app.ws_main
```

沙箱模式写在 `ws_main.py`（`is_sandbox=True`），过审上线后改为 `False`。
注意：官方宣布 WebSocket 在逐步下线（2026-07 仍可用），若某天连不上，切换到 Webhook 模式。

### Webhook 模式（正式部署备用，app/main.py）

平台要求回调地址为**已备案域名 + HTTPS**，适合部署到服务器后使用：

```bash
.venv/bin/uvicorn app.main:app --port 8787
```

两种模式共用同一套指令逻辑（`app/commands.py`），随时可切换。

### 冒烟测试

```bash
.venv/bin/python scripts/local_smoke.py   # 不碰 QQ 群，测指令逻辑 + 验签
```

## 迁移 / 常驻部署

机器人同一时间**只在一台机器上跑**（WebSocket 会话冲突），迁移后记得停掉旧机器的进程。
`.env`（密钥）和 `bindings.db`（绑定+成长快照）不在 git 里，迁移时手动拷贝这两个文件。

### Windows（家里常开的机器）

```bat
:: 1. 装 Python 3.11+（python.org，勾选 Add to PATH）和 Git
:: 2. 克隆并安装
git clone https://github.com/YzYhhhstudy/coc-qq-bot.git
cd coc-qq-bot
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
:: 3. 把旧机器的 .env 和 bindings.db 拷到项目根目录
:: 4. 启动（带断线自动重启）
scripts\run_windows.bat
```

开机自启：任务计划程序 → 创建基本任务 → 触发器"登录时" → 操作"启动程序"选 `scripts\run_windows.bat`。
（设置里记得关掉系统自动睡眠。）

### Linux / VPS

```bash
git clone https://github.com/YzYhhhstudy/coc-qq-bot.git && cd coc-qq-bot
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# 拷入 .env 和 bindings.db 后：
sudo cp deploy/coc-qq-bot.service /etc/systemd/system/   # 先改里面的路径
sudo systemctl enable --now coc-qq-bot
```

## 参考文档

- QQ 机器人官方文档（v2 API / Webhook）：https://bot.q.qq.com/wiki/develop/api-v2/
- CoC API 文档：https://developer.clashofclans.com/#/documentation
- coc.py（如果以后想换成熟封装）：https://github.com/mathsman5133/coc.py
