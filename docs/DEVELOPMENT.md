# 开发指南与踩坑记录

面向维护者（人或 Claude）。用户向的安装/部署/命令说明在 [README](../README.md)。

## 1. 官方 API 能拿到什么、拿不到什么（做新功能前先看）

| 能拿到 | 端点 | 已用在 |
|---|---|---|
| 部落概况、成员列表（本/奖杯/捐兵/收兵/职位） | `/clans/{tag}` | 部落、成员、捐兵、周报快照 |
| 当前部落战：双方名单、每刀星数/摧毁率/目标、时间 | `/clans/{tag}/currentwar` | 部落战 全家族 |
| 战争日志（对方需公开，否则 403） | `/clans/{tag}/warlog` | 战绩 |
| 联赛分组、每场对战（只在联赛周有，否则 404） | `.../currentwar/leaguegroup`、`/clanwarleagues/wars/{warTag}` | 联赛 全家族 |
| 玩家档案：英雄/兵种/攻城/宠物/法术/装备的等级、战争星、攻防胜场、段位、成就 | `/players/{tag}` | 玩家、我、进度、侦查、阵容 |
| 都城突袭历史（每人出刀数与掠夺，只含参与者） | `/clans/{tag}/capitalraidseasons?limit=N` | 突袭、突袭-催刀、突袭-历史 |
| 都城大厅与各区等级 | `/clans/{tag}` 的 `clanCapital` | 都城 |
| 地区排行（部落/玩家，**只有前 200**） | `/locations/{id}/rankings/...` | 排行 |
| 赛季/金票时间 | `/goldpass/seasons/current` | 日程 |
| 按名字搜部落（玩家不能按名字搜，只能 TAG） | `/clans?name=` | 搜索 |

| 拿不到（游戏外没有任何途径） | 影响 |
|---|---|
| 防御建筑、城墙、陷阱的等级 | 「进度」只能算进攻侧（英雄+实验室），防御进度做不了 |
| 工人数量、升级队列、实验室在研项目 | 「我-工人」直接回复做不了 |
| 传奇杯逐场攻防记录 | 「传奇」用每日快照差分近似 |
| **按大本的等级上限**：`maxLevel` 是全游戏最高，不分本 | 需要 `app/th_caps.json`（见 §4） |
| 排行 200 名以外、成员历史数据 | 「我们第几名」只能在前 200 时回答；周报/成长靠自建快照 |

因此项目自建了两样东西：**每日快照**（`ws_main._snapshot_loop`，每 12h 存绑定玩家与绑定部落全员，`store.snapshots` / `store.member_snapshots`）和**各大本上限表**（`th_caps.json`）。凡是"变化趋势"类需求都要先积累快照，首日只能回复"数据积累中"。

## 2. 代码约定

- **指令语法**：`主命令-子命令 [参数]`，全在 `commands.handle()` 里分发。放置顺序有讲究：
  - 不需要绑定部落的顶层命令（`排行`、`传奇`、`玩家`、`我`、`玩法`）放在 `clan_cmds` 分支**之前**；
  - 联赛子命令在 `coc.get_league_group()` **之后**（非联赛周它 404，统一回复"不在联赛期"），但非联赛周也要能用的（如 `联赛-阵容`）必须放它之前；
  - `周报` 这类"主命令-子命令"共用主命令的（`部落-周报`），要放在 `部落` 的分发之前。
- **回复是纯文本**，QQ 单条消息别太长：榜单取前 10，名单取前 15 再加"…另有 N 人"，一行一人的输出（成员、侦查）控制在 50 行内。风格：emoji 开头一行标题、每行一条、结尾一行"注："。
- **缓存与限流**：`coc._get(path, ttl=60)` 按路径缓存；批量拉档案用 `coc.get_players(tags, ttl=600, concurrency=10)`（侦查/阵容/周报共用），后台快照任务用 `concurrency=5`。已结束的联赛场次缓存 1 小时。
- **失败降级**：单个档案拉取失败返回 None，输出里显示"档案?"/按本排序，不让整条命令失败；非战期、非联赛周、无快照都要有明确文案。
- **不加运行时依赖**：只有 `qq-botpy`、`httpx`、`python-dotenv`（webhook 模式另有 fastapi）。生成脚本需要的库（coc.py）在临时 venv 里装，README 写明。
- **人工维护的数据**（大版本更新后校对）：`meta.py`（流派/阵型，月更）、`MEDAL_TABLE`（奖章表）、`LOCATION_IDS`（地区 ID）、`TH_CAPS_MANUAL`（静态数据未收录的新单位上限）、`HERO_CN`/`TROOP_CN`/`SIEGE_CN`/`PET_CN`/`SPELL_CN`（新单位要补中文名，否则输出英文；显示统一走 `_unit_cn()`，官方译名查 coc.py 4.x `static/translations.json` 的 `CN` 字段）。**生成的数据**：`th_caps.json`（`scripts/gen_th_caps.py`）。

## 3. 开发、测试、发布流程

1. 从 main 开分支 → 提交 → 推送 → 开 PR → **本地审查**（部署机会自动跑 main，合并即上线）→ 合并。
2. 部署机（Windows）每天自动比对 GitHub main 并更新重启；想立即生效双击 `scripts\update.bat`。
3. 发「版本」确认部署机已到最新提交。

**离线测试（不需要 token，推荐先跑）**：monkeypatch `coc._get`，用固定 JSON 走 `commands.handle()`，`DB_PATH` 指到临时文件防止污染 `bindings.db`：

```python
import asyncio, os, sys
os.environ["DB_PATH"] = "/tmp/offline.db"
sys.path.insert(0, ".")
from app import coc, commands

FIXTURES = {"/clans/%23CLAN": {...}, "/players/%23P1": {...}}   # 路径与 coc.py 里拼的一致（# 已编码为 %23）
async def fake_get(path, ttl=60):
    return FIXTURES[path]          # 想模拟 404 就 raise httpx.HTTPStatusError(...)
coc._get = fake_get

async def main():
    print(await commands.handle("test-user", "绑定 #CLAN"))
    reply = await commands.handle("test-user", "部落战-侦查")
    assert len(reply.splitlines()) <= 60
asyncio.run(main())
```

快照类功能（周报、成长、传奇）需要"几天前"的数据：直接往 sqlite 插回填日期的行（`INSERT INTO member_snapshots(clan_tag, day, data) VALUES(?, '2026-08-25', ?)`），顺便构造捐兵赛季清零（旧值 > 新值）和零活跃成员两种情况。

**真实 API 冒烟**：`DB_PATH=/tmp/smoke.db .venv/bin/python scripts/local_smoke.py [#部落TAG]`（默认 `#2GP9CGR8Q`，一个 9 到 18 本都有的活跃部落，适合抽样）。非战期/非联赛期看到降级文案即算通过。

**验收清单**：新命令进了 HELP 和 README 命令表；非战期/非联赛期/无快照/档案失败四种降级都试过；输出行数与字数看过；新单位的中文名映射补了。

## 4. 踩坑记录

**地区 ID（2026-07）**：`32000059` 是哥伦比亚，中国是 `32000056`。改 `LOCATION_IDS` 必须发一次「排行-部落 国服」实测榜单内容。

**`maxLevel` 不是当前大本上限（2026-09）**：16 本和 18 本玩家的英雄 `maxLevel` 总和都是 480。要算"16 本 100%"必须有按本的上限表，于是有了 `th_caps.json`。使用规则：最高本直接用 API 值（全游戏最高即它的上限，且比静态表及时）；表里没有的新单位退回 API 值；`max(上限, 当前等级)` 兜底防止超过 100%。

**coc.py 静态数据的坑**：
- 3.x 的 `static/*.json` 是游戏 CSV 直转，用内部名（`Minion Hero`、`Unipony`、`Siege Machine Ram`），要经 `TID` → `texts_EN.json` 映射成 API 用的显示名，而且只到 17 本；4.x 改成单文件 `static_data.json`，显示名直接可用、每级带 `required_townhall`，覆盖 18 本——**生成脚本只支持 4.x**。
- 用系统 Python 3.9 建 venv 时 pip 只会装到 3.9.1（4.x 要 3.10+），要用项目的 `.venv` 或 3.11+ 建。
- 活动/衍生单位（`Pumpkin Barbarian Bare`、`ProtoSpell2`、`AirSpawnerPet`）和正式单位共用显示名且排在后面，生成时**首个出现的优先**，否则野蛮人 16 本上限会变成 7。
- 数据滞后于游戏：18 本多了一级、地震 6 级、Dragon Duke 整个缺失。新英雄手工写进 `TH_CAPS_MANUAL`（`setdefault` 合并，生成数据一旦收录自动覆盖）。

**update.bat 不拉起机器人（2026-09）**：用 PowerShell `Get-CimInstance Win32_Process | Where-Object CommandLine -like '*app.ws_main*'` 找机器人进程，会把**运行这条命令的 PowerShell 自己**也匹配进去（它的命令行里也含这个字符串），于是"机器人是否在跑"恒为真，永远不启动 `run_windows.bat`。修法：`$_.ProcessId -ne $PID` 排除自身、只匹配 `python*`；杀完后轮询最多 20 秒等守护循环重启，没有守护循环再新开窗口启动。macOS 的 `pgrep -f` 默认就排除自身，没这个问题。

**进度功能的取舍**：英雄装备不计入总进度（大多数装备本来就不需要练满，只单独显示一行）；总进度向下取整，避免 99.6% 显示成 100%；未解锁的单位 API 里没有，所以低本"100%"不代表兵种全解锁。

**联赛数据的形状**：`leaguegroup` 404 就是非联赛周；`rounds[].warTags` 为 `#0` 表示该轮还没生成；单场对战里 `clan`/`opponent` 谁是我方要按 tag 判断（`_find_cwl_war` 会交换）；战斗日与下一场备战日并存，催刀要定位到 `state == "inWar"` 的那场。

**突袭数据**：`members` 只含已参与的人，没参与的在 API 里看不到，"催刀"名单天然缺席这部分人。

**QQ 平台**：2026-01 起新机器人不能配沙箱群，只能私聊（沙箱消息列表最多 20 人）；回复必须带 `msg_id`（被动回复不占主动消息配额）；`is_sandbox=True` 过审后改 False。
