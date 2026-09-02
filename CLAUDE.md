# coc-qq-bot 项目说明（给 Claude）

部落冲突（Clash of Clans）QQ 机器人：官方 QQ 机器人 WebSocket（botpy）+ 官方 CoC API，纯被动文本回复，无 LLM。
面向新用户的安装与命令说明在 `README.md`；开发约定、API 能力边界、测试方法、踩坑记录在 `docs/DEVELOPMENT.md`——**做新功能前先读它的 §1 和 §4**。

## 关键文件

- `app/commands.py` — 全部业务逻辑：`handle()` 按「主命令-子命令」分发，`_fmt_*` 负责排版；`HELP` 常量是帮助文案
- `app/coc.py` — CoC API 封装（60s 缓存、`get_players` 限并发批量拉档案）
- `app/store.py` — SQLite：绑定关系、玩家/部落全员每日快照、共享收录
- `app/ws_main.py` — 入口 + 后台任务（每日快照、每日自动更新）
- `app/meta.py`（人工月更）、`app/th_caps.json`（`scripts/gen_th_caps.py` 生成）— 数据表
- `scripts/local_smoke.py` — 真实 API 冒烟；`scripts/update.bat` / `run_windows.bat` — Windows 更新与守护

## 必须遵守

- 不加运行时依赖；回复是纯文本，控制长度（榜单前 10、名单前 15 加"…另有 N 人"、一行一人不超过 50 行）。
- 新命令要同时更新 `HELP` 和 README 命令表；新单位要补 `HERO_CN`/`TROOP_CN`/`SIEGE_CN`/`PET_CN`/`SPELL_CN` 中文名（显示统一走 `_unit_cn()`，官方译名可从 coc.py 4.x 的 `static/translations.json` 的 `CN` 字段查）。
- `handle()` 里的分发顺序有约束（不需绑定的顶层命令在 `clan_cmds` 之前；非联赛周也要能用的联赛子命令放 `get_league_group()` 之前），见 DEVELOPMENT.md §2。
- 每种降级都要有文案：非战期、非联赛周、无快照、单个档案拉取失败。
- 改动先离线测（monkeypatch `coc._get`，`DB_PATH` 指到临时文件），再跑 `local_smoke.py`；测试时**不要**用项目根目录的 `bindings.db`。
- 开分支 → PR → 用户本地审查 → 合并。**main 会自动部署到用户的 Windows 机器**，不要直接推 main。提交信息用中文，说明"为什么"。

## 常见误区（详见 DEVELOPMENT.md §4）

- API 的 `maxLevel` 是全游戏最高等级，不是当前大本上限；按本上限查 `th_caps.json`。
- API 没有防御建筑等级、工人/升级队列、传奇逐场记录；排行只有前 200。
- 国服地区 ID 是 `32000056`（`32000059` 是哥伦比亚）；改地区 ID 必须实测。
- Windows 脚本里用 PowerShell 按命令行匹配进程时要排除 `$PID` 自身。
