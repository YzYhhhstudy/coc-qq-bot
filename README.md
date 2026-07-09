# coc-qq-bot — 部落冲突 QQ 群助手（官方平台 · 被动回复版）

> A QQ bot for Clash of Clans clans, built on the official QQ Bot Open Platform (WebSocket) and the official CoC API.
> Features: clan/war/CWL queries, war-day nudges, enemy scouting, medal calculator, win-probability estimate, weekly clan reports, official leaderboards, Legend daily logs, player growth tracking, and monthly-curated meta (strategies & base layouts). MIT licensed.

QQ 机器人：私聊发指令（或群里 `@机器人 <指令>`），查询部落的公开信息——成员、部落战、联赛、玩家详情、流派攻略。
数据来自 **Supercell 官方 Clash of Clans API**（免费），消息通道走 **QQ 开放平台官方接口**（合规、不封号）。
不做主动播报，纯被动问答 —— 不需要 LLM，**零 AI 费用**；跑在任何一台常开的电脑上即可，**无需服务器**。

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
| | `突袭-历史` | 近6期突袭趋势：掠夺环比、攻防奖章、出刀数 |
| | `都城` | 部落都城：首都大厅/积分/各区等级 |
| | `周报` | 近7天全员增量：捐兵榜/奖杯/战争星/挂机名单/成员进出（每日快照，需积累数据） |
| | `搜索 部落名` | 按名字找部落 TAG |
| 部落战 | `部落战`（=`战况`） | 比分 + 剩余时间 + 未出刀 + 胜率预估 |
| | `部落战-对阵` | 对位本数表 |
| | `部落战-进度` | 逐人对位进度（每人两刀都显示） |
| | `部落战-催刀` / `部落战-敌刀` | 剩余刀数名单（普通战每人2刀） |
| | `部落战-复盘` | 打完后逐人战报（每刀星数/摧毁率/目标） |
| | `部落战-战绩`（=`战绩 [#TAG]`） | 最近部落战日志 |
| | `部落战-侦查` | 敌情侦查：对面全员英雄摸底、软柿子标记、双方实力对比 |
| 联赛 | `联赛` | 分组与同组部落 |
| | `联赛-积分榜` | 小组排名（胜场含+10⭐） |
| | `联赛-奖章` | 奖章计算器：按段位/排名/个人星数预估每人所得 |
| | `联赛-对阵` / `联赛-2` | 备战日=对位本数表+胜率预估；战斗日=紧凑战报（比分、双方未出刀 x/n、胜率、我方催刀名单） |
| | `联赛-进度 [场次]` | 逐人对位进度：`1. AAA ⭐⭐⭐100% VS BBB ⭐49%`，默认正在打的一场 |
| | `联赛-催刀` / `联赛-敌刀` | 我方/敌方未出刀名单（一行一个，方便@人） |
| | `联赛-复盘 [场次]` | 已结束场次逐人复盘：星数/摧毁率/打高打低、三星榜、漏刀名单 |
| | `联赛-总结` | 赛季结算：最终排名、逐场胜负、MVP、全员奖章 |
| | `联赛-分配 [场次]`（部落战同款） | 作战计划：按实力分错位匹配"几号打几号"+ 难度标注；战斗日只给未出刀的人派活、自动排除已三星目标 |
| | `联赛-侦查 [场次]` | 联赛版敌情侦查（默认最新场次） |
| | `联赛-阵容 [15\|30]` | 按 大本→英雄总级→战争星 推荐参战名单（非联赛周也可用） |
| 日程 | `日程` | 赛季结束/联赛/突袭周末 倒计时（北京时间） |
| 排行 | `排行-部落 [国服\|全球]` | 官方地区部落榜 TOP10 + 已绑定部落名次（榜单仅前200） |
| | `排行-玩家 [国服\|全球]` / `排行-传奇` | 玩家奖杯榜（即传奇榜）+ 已绑定玩家名次 |
| 玩法 | `玩法-流派-17` | 该大本流行流派列表（含一键复制配兵链接），meta 数据人工月更 |
| | `玩法-阵型-17` | 阵型站分级页链接（Blueprint 月更 CWL 阵、黑羽COC、B站视频等）+ 群友分享 |
| | `玩法-个性阵-17` | 艺术/整活阵合集（皮卡丘/爱心/文字阵） |
| | `我-流派名`（如 `我-隐龙龙骑`） | 按流派检查你的英雄/兵种/法术等级缺口 + 配兵链接 |
| | `玩法-阵型收录 链接 [备注]` | 分享公众号/B站的阵型文——存进共享库，**所有用户**查阵型推荐都能看到；备注写"17本"则只推给对应大本 |
| | `玩法-流派收录 链接 [备注]` | 同上，流派文/视频，出现在流派推荐里 |
| | `玩法-收录列表` / `玩法-收录删除 编号` | 管理共享收录（自动署名为分享人的绑定玩家名） |
| 玩家 | `玩家 #TAG` | 详情：本/奖杯/战争星/英雄一览/职位 |
| | `玩家-英雄/部队/法术 #TAG` | 全部英雄/兵种(含攻城/宠物)/法术的等级与满级 |
| | `玩家-建议 #TAG` / `我-建议` | 升级建议：英雄缺口 > 主流兵种 > 关键法术 + 本级段提示 |
| 我 | `绑定玩家 #TAG` / `解绑玩家` | 绑定自己的账号 |
| | `我` / `我-英雄/部队/法术` | 查自己（工人/升级队列官方 API 不提供，做不了） |
| | `我-成长` | 成长追踪：奖杯/战争星/英雄总级等随时间变化（机器人每12h自动快照） |
| | `我-传奇`（=`传奇 [#TAG]`） | 传奇战报：逐日杯数净变化+攻防胜场（需在传奇杯，靠每日快照积累） |

旧扁平指令（`对阵`/`积分榜`/`奖章`）保留为别名。私聊直接发指令；群聊 @ 机器人后发。

## 架构

```
QQ 消息（私聊 / 群@）
   → WebSocket 长连接（app/ws_main.py，官方 botpy SDK，出站连接免公网IP）
   → 指令解析 (app/commands.py)
   → CoC API 客户端 (app/coc.py，RoyaleAPI 代理 + 缓存)
   → 被动回复（带 msg_id，不占主动消息配额）
```

- `app/ws_main.py` — **主入口**：WebSocket 连接、私聊/群聊事件、每日快照任务（玩家成长 + 部落全员，周报/传奇战报数据源）
- `app/commands.py` — 指令解析与文本排版（全部业务逻辑）
- `app/coc.py` — Clash of Clans API 封装 + 缓存
- `app/meta.py` — 流派/阵型数据（人工月更，见下文）
- `app/store.py` — SQLite：绑定关系 + 成长快照
- `app/main.py` + `app/qq_api.py` — Webhook 模式备用入口（需备案域名，一般用不到）

## 🚀 快速开始（从零到跑通，约 30 分钟）

1. **注册 QQ 机器人**：[q.qq.com](https://q.qq.com) 注册个人开发者（免费）→ 创建机器人 → 记下 `AppID` 和 `AppSecret`（Secret 只显示一次，妥善保存）
2. **注册 Supercell 开发者**：[developer.clashofclans.com](https://developer.clashofclans.com)（免费）→ Create New Key → **IP 白名单只填 `45.79.218.79`**（[RoyaleAPI 代理](https://docs.royaleapi.com/proxy.html)的固定 IP，这样你家 IP 变了也不影响）→ 记下 Token
3. **安装**：
   ```bash
   git clone https://github.com/YzYhhhstudy/coc-qq-bot.git && cd coc-qq-bot
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # Windows: .venv\Scripts\pip
   cp .env.example .env   # 然后编辑 .env，填入上面三个值
   ```
4. **启动**：`.venv/bin/python -m app.ws_main`（Windows 直接双击 `scripts\run_windows.bat`，自带崩溃重启）
5. **配置沙箱**：q.qq.com 机器人管理端 → 沙箱配置 → **消息列表配置**里把自己的 QQ 加进去（最多 20 人，部落成员也可以加）
6. **开聊**：QQ 消息列表里找到机器人，私聊发 `帮助`，然后 `绑定 #你的部落TAG`

> `.env` 是你的密钥（照 `.env.example` 填，**不要**提交到 git）；`bindings.db` 是运行数据库，首次启动自动创建，无需准备。
>
> 两个脚本的分工：`run_windows.bat` 管**启动**（首次/重启电脑后）；`update.bat` 管**更新**（仓库出新版本时双击，
> 自动拉代码+装依赖+重启机器人）。Linux 对应 `systemctl restart` + `git pull`。

## 💰 费用

| 项目 | 费用 |
|---|---|
| QQ 开放平台 / CoC API / RoyaleAPI 代理 | **¥0** |
| LLM / AI | **¥0**（纯查询，不需要大模型） |
| 运行环境 | **¥0**——任何一台常开的电脑（家里旧笔记本/台式机均可）；想 24h 云端跑再考虑 VPS（~¥15–40/月，仓库带 systemd 配置） |

WebSocket 出站连接**不需要**公网 IP、域名、备案、证书。总成本：¥0。

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

## ❓ 常见问题

**Q：机器人不回消息？** 按顺序排查：① `.env` 是否在项目根目录且三个值都填了；② 你的 QQ 是否已加进沙箱"消息列表配置"；③ 看日志（`bot.log` 或终端输出）——出现`「xxx」启动成功`说明连接正常；④ Windows 首次运行放行防火墙弹窗。

**Q：能拉进 QQ 群吗？** 暂时不能——QQ 开放平台 2026-01-31 起关闭了新机器人的群配置（平台级限制，所有人都一样）。本项目群聊代码已就绪，平台开放后自动生效。目前用法：把部落成员加进沙箱消息列表（最多 20 人），各自私聊使用。

**Q：需要作者的 `.env` / `bindings.db` 吗？** 不需要。`.env` 填你自己注册的密钥（别用别人的）；`bindings.db` 首次启动自动创建。

**Q：报错 403 / accessDenied？** CoC API Key 的 IP 白名单不对——确认填的是 `45.79.218.79` 且 `.env` 里 `COC_BASE_URL=https://cocproxy.royaleapi.dev/v1`。

**Q：奖章/胜率数字和游戏里不一样？** 奖章表是社区公认数值（官方不公布），胜率是简单统计模型，都仅供参考，以游戏内为准。

**Q：怎么知道机器人有没有更新？** 发「版本」查询。默认开启**自动更新**：每天比对一次 GitHub，有新版本自动拉代码+重启（约 1 分钟内完成，期间消息可能漏回）。注意这意味着 main 分支上的代码会自动跑到你的部署机上——合并 PR 前务必审查。不放心就设 `AUTO_UPDATE=0` 改为手动 update.bat。

## Meta 数据维护（流派/阵型）—— 每月一次

`app/meta.py` 是人工维护的版本数据（流派、配兵链接、阵型站），带 `META_UPDATED` 日期，会显示在机器人输出里。

**更新流程（每月联赛前，或 Supercell 发平衡性补丁后）：**

1. 打开 Claude Code，对 **Claude** 说：「更新 meta」——注意是和 Claude 对话，不是和 QQ 机器人对话，机器人只负责读这份数据
2. Claude 会重新调研当月各大本流行流派/配兵链接/阵型资源，更新 `app/meta.py` 和 `META_UPDATED` 日期，然后 commit + push
3. 部署机器上 `git pull` 并重启机器人即生效

> 给 Claude 的提示：更新时调研 Blueprint CoC（有游戏内一键复制的 CopyArmy 链接）、TapTap/bilibili 中文流派统计；
> 覆盖 TH13-18 的主流流派（名称/别名/思路/英雄装备/关键兵种法术的 API 英文名/配兵链接），
> 核对阵型站分级页 URL 是否仍有效；超级兵在 troops 检查里登记为原兵种名。
>
> 除 meta.py 外，`app/commands.py` 里还有三份人工维护数据，大版本更新（新大本/新英雄/联赛改制）后顺带校对：
> `TH_HERO_MAX`（各大本英雄满级总和，侦查功能用）、`MEDAL_TABLE`（联赛奖章表）、`LOCATION_IDS`（地区 ID，改动后必须实测——上次就把哥伦比亚当成了国服）。

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

**日常更新——通常不用管**：机器人每天自动检查一次 GitHub，有新版本会**自动更新并重启**（`.env` 里 `AUTO_UPDATE=0` 可关闭）。
发「版本」可随时查询当前版本和更新状态。想立即更新（不等下一轮检查）就双击 `scripts\update.bat`——拉代码 → 装依赖 → 重启一条龙，只精准杀 bot 进程，不影响其他 Python 程序。

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
