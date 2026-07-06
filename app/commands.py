"""指令解析与回复文本排版。

指令体系：主 tag + 横杠子功能，如 联赛-积分榜、联赛-2、玩家-英雄 #TAG、我-部队。
旧的扁平指令（对阵/积分榜/奖章）保留为别名。
"""
import asyncio
import math
from datetime import datetime, timezone

import httpx

from . import coc, store

# ---------------- 数据表 ----------------

# 联赛奖章表（社区公认经典表）：段位 → (第1名基础奖章, 每名次递减)
# 个人所得 = 基础值 × 产出率(20% + 每星10%, 8星封顶100%)
MEDAL_TABLE = {
    "Bronze League III": (34, 4), "Bronze League II": (46, 4), "Bronze League I": (58, 4),
    "Silver League III": (76, 6), "Silver League II": (94, 6), "Silver League I": (112, 6),
    "Gold League III": (136, 8), "Gold League II": (160, 8), "Gold League I": (184, 8),
    "Crystal League III": (214, 10), "Crystal League II": (244, 10), "Crystal League I": (274, 10),
    "Master League III": (310, 12), "Master League II": (346, 12), "Master League I": (382, 12),
    "Champion League III": (424, 14), "Champion League II": (466, 14), "Champion League I": (508, 14),
}
LEAGUE_CN = {"Bronze": "青铜", "Silver": "白银", "Gold": "黄金",
             "Crystal": "水晶", "Master": "大师", "Champion": "冠军"}

HERO_CN = {"Barbarian King": "蛮王", "Archer Queen": "女皇", "Grand Warden": "大守护者",
           "Royal Champion": "皇家战士", "Minion Prince": "亡灵王子",
           "Battle Machine": "战争机器", "Battle Copter": "战争直升机"}
TROOP_CN = {
    "Barbarian": "野蛮人", "Archer": "弓箭手", "Giant": "巨人", "Goblin": "哥布林",
    "Wall Breaker": "炸弹人", "Balloon": "气球兵", "Wizard": "法师", "Healer": "天使",
    "Dragon": "飞龙", "P.E.K.K.A": "皮卡", "Baby Dragon": "飞龙宝宝", "Miner": "掘地矿工",
    "Electro Dragon": "雷电飞龙", "Yeti": "大雪怪", "Dragon Rider": "飞龙骑士",
    "Electro Titan": "电磁泰坦", "Root Rider": "古藤骑士", "Thrower": "投掷手",
    "Minion": "亡灵", "Hog Rider": "野猪骑士", "Valkyrie": "瓦基丽武神", "Golem": "戈仑石人",
    "Witch": "女巫", "Lava Hound": "熔岩猎犬", "Bowler": "投石手", "Ice Golem": "寒冰戈仑",
    "Headhunter": "猎头者", "Apprentice Warden": "见习守护者", "Druid": "德鲁伊",
}
SPELL_CN = {
    "Lightning Spell": "闪电", "Healing Spell": "治疗", "Rage Spell": "狂暴",
    "Jump Spell": "弹跳", "Freeze Spell": "冰冻", "Clone Spell": "复制",
    "Invisibility Spell": "隐身", "Recall Spell": "召回", "Revive Spell": "复活",
    "Poison Spell": "毒药", "Earthquake Spell": "地震", "Haste Spell": "加速",
    "Skeleton Spell": "骷髅", "Bat Spell": "蝙蝠", "Overgrowth Spell": "藤蔓",
}
PET_CN = {"L.A.S.S.I": "拉西", "Electro Owl": "电鸮", "Mighty Yak": "猛牦牛",
          "Unicorn": "独角兽", "Frosty": "小雪怪", "Diggy": "穿山甲",
          "Poison Lizard": "毒蜥蜴", "Phoenix": "凤凰", "Spirit Fox": "灵狐",
          "Angry Jelly": "怒灵水母", "Sneezy": "喷嚏怪"}
SIEGE = {"Wall Wrecker", "Battle Blimp", "Stone Slammer", "Siege Barracks",
         "Log Launcher", "Flame Flinger", "Battle Drill", "Troop Launcher"}
SUPER_TROOPS = {"Sneaky Goblin", "Rocket Balloon", "Inferno Dragon", "Ice Hound"}
ROLE_CN = {"leader": "首领", "coLeader": "副首领", "admin": "长老", "member": "成员"}
WAR_STATE = {"preparation": "备战日", "inWar": "战斗日", "warEnded": "已结束",
             "notInWar": "当前没有部落战"}

HELP = (
    "🛡️ 部落冲突助手（子功能用 - 连接）\n"
    "【部落】绑定 #TAG｜解绑｜部落 [#TAG]｜成员 [#TAG]｜捐兵｜摸鱼榜｜突袭｜突袭-催刀｜搜索 名字\n"
    "【部落战】部落战(=战况)｜部落战-对阵｜部落战-催刀｜部落战-敌刀｜部落战-复盘｜部落战-战绩\n"
    "【联赛】联赛｜联赛-积分榜｜联赛-奖章｜联赛-对阵｜联赛-2(第2场)｜联赛-催刀｜联赛-敌刀｜联赛-复盘 [场次]｜联赛-总结\n"
    "【玩家】玩家 #TAG｜玩家-英雄/部队/法术/建议 #TAG\n"
    "【我】绑定玩家 #TAG｜解绑玩家｜我｜我-英雄/部队/法术/建议/成长\n"
    "带 [#TAG] 的指令可以查任意部落，不带就查已绑定的\n"
    "换绑：直接重新「绑定」即可覆盖"
)


# ---------------- 入口 ----------------

async def handle(group_openid: str, content: str) -> str:
    parts = content.split()
    if not parts:
        return HELP
    cmd = parts[0].replace("－", "-").replace("—", "-")
    args = parts[1:]
    main, _, sub = cmd.partition("-")

    try:
        # ---- 绑定管理 ----
        if main == "绑定":
            if not args:
                return "用法：绑定 #部落TAG"
            clan = await coc.get_clan(args[0])
            store.bind(group_openid, clan["tag"])
            return f"✅ 已绑定部落：{clan['name']} ({clan['tag']})"
        if main == "解绑":
            return "✅ 已解绑部落" if store.unbind(group_openid) else "本来就没绑定部落"
        if main == "绑定玩家":
            if not args:
                return "用法：绑定玩家 #你的玩家TAG（游戏内点头像可复制）"
            p = await coc.get_player(args[0])
            store.bind_player(group_openid, p["tag"])
            return f"✅ 已绑定玩家：{p['name']} ({p['tag']})，发「我」随时查看"
        if main == "解绑玩家":
            return "✅ 已解绑玩家" if store.unbind_player(group_openid) else "本来就没绑定玩家"

        # ---- 玩家 ----
        if main == "玩家":
            if not args:
                return "用法：玩家 #玩家TAG（子功能：玩家-英雄/部队/法术 #TAG）"
            return _fmt_player_sub(await coc.get_player(args[0]), sub)
        if main == "我":
            ptag = store.get_player_tag(group_openid)
            if not ptag:
                return "还没绑定玩家，先发：绑定玩家 #你的玩家TAG"
            if sub == "工人":
                return ("😢 官方 API 不提供工人/升级队列数据（游戏外无法获取），"
                        "这个只能进游戏看。能查的有：我-英雄 / 我-部队 / 我-法术")
            if sub == "成长":
                return await _fmt_growth(ptag)
            return _fmt_player_sub(await coc.get_player(ptag), sub)

        if main == "搜索":
            if not args:
                return "用法：搜索 部落名"
            return _fmt_search(await coc.search_clans(" ".join(args)))

        # ---- 部落类（可带 #TAG 查任意部落，否则用绑定的） ----
        # 纯数字参数（如 对阵 2）不是 TAG
        tag_arg = None
        if args and (args[0].startswith("#")
                     or (not args[0].isdigit() and len(args[0]) >= 5)):
            tag_arg = args[0]
        bound = store.get_clan_tag(group_openid)
        clan_cmds = ("部落", "成员", "战况", "战绩", "突袭", "捐兵", "部落战",
                     "摸鱼榜", "摸鱼", "活跃",
                     "联赛", "对阵", "积分榜", "排名", "奖章")
        if main in clan_cmds:
            tag = tag_arg or bound
            if not tag:
                return "还没绑定部落，先发：绑定 #部落TAG（或在指令后直接带 #TAG）"

            if main == "部落":
                return _fmt_clan(await coc.get_clan(tag))
            if main == "成员":
                return _fmt_members(await coc.get_clan(tag))
            if main == "战绩" or (main == "部落战" and sub == "战绩"):
                return _fmt_warlog(await coc.get_war_log(tag))
            if main in ("战况", "部落战"):
                war = await coc.get_current_war(tag)
                if war.get("state", "notInWar") == "notInWar":
                    return "当前没有部落战"
                if sub == "对阵":
                    return _fmt_war_matchup(war)
                if sub == "催刀":
                    return _fmt_war_idle(war, enemy=False)
                if sub in ("敌刀", "敌方"):
                    return _fmt_war_idle(war, enemy=True)
                if sub == "复盘":
                    return _fmt_war_review(war)
                return _fmt_war(war)
            if main == "突袭":
                if sub == "催刀":
                    return _fmt_raid_idle(await coc.get_capital_raids(tag))
                return _fmt_raids(await coc.get_capital_raids(tag))
            if main == "捐兵":
                return _fmt_donations(await coc.get_clan(tag))
            if main in ("摸鱼榜", "摸鱼", "活跃"):
                return await _fmt_slackers(tag)

            # 联赛族（含旧别名）
            try:
                group = await coc.get_league_group(tag)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return "当前不在联赛期（CWL 每月月初进行）"
                raise
            if main in ("积分榜", "排名") or sub in ("积分榜", "排名"):
                return _fmt_standings(tag, await _cwl_standings(group))
            if main == "奖章" or sub == "奖章":
                return await _fmt_medals(tag, group)
            if main == "对阵" or sub == "对阵":
                round_no = int(args[0]) if (main == "对阵" and args and args[0].isdigit()) else None
                return await _fmt_cwl_matchup(tag, group, round_no)
            if sub.isdigit():
                return await _fmt_cwl_matchup(tag, group, int(sub))
            if sub == "催刀":
                return await _fmt_idle(tag, group, enemy=False)
            if sub in ("敌刀", "敌方"):
                return await _fmt_idle(tag, group, enemy=True)
            if sub == "复盘":
                round_no = int(args[0]) if args and args[0].isdigit() else None
                return await _fmt_review(tag, group, round_no)
            if sub == "总结":
                return await _fmt_season_summary(tag, group)
            if main == "联赛" and not sub:
                return _fmt_league(group)
            return HELP

        return HELP

    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 404:
            return "❌ 找不到该 TAG，检查一下拼写（0 和 O 会自动纠正）"
        if code == 403:
            return "❌ CoC API 拒绝访问：检查 Token 或 IP 白名单；战争日志可能未公开"
        return f"❌ CoC API 错误 ({code})，稍后再试"


# ---------------- 通用工具 ----------------

def _league_cn(name: str) -> str:
    for en, cn in LEAGUE_CN.items():
        if name.startswith(en):
            return name.replace(f"{en} League", f"{cn}联赛")
    return name


def _norm_tag(tag: str) -> str:
    return tag.upper().replace("O", "0").lstrip("#")


def _parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc)


def _time_left(war: dict) -> str:
    state = war.get("state")
    if state == "preparation" and war.get("startTime"):
        delta, label = _parse_ts(war["startTime"]) - datetime.now(timezone.utc), "距开战"
    elif state == "inWar" and war.get("endTime"):
        delta, label = _parse_ts(war["endTime"]) - datetime.now(timezone.utc), "距结束"
    else:
        return ""
    mins = max(0, int(delta.total_seconds() // 60))
    return f"{label} {mins // 60}小时{mins % 60:02d}分"


def _chunk(items: list[str], n: int = 4) -> list[str]:
    return ["  ".join(items[i:i + n]) for i in range(0, len(items), n)]


# ---------------- 部落 ----------------

def _fmt_clan(c: dict) -> str:
    league = (c.get("warLeague") or {}).get("name", "")
    cap = (c.get("clanCapital") or {}).get("capitalHallLevel")
    lines = [
        f"🏰 {c['name']} ({c['tag']})",
        f"等级 {c['clanLevel']} | 成员 {c['members']}/50 | 段位 {_league_cn(league)}",
        f"对战 胜{c.get('warWins', '?')}" +
        (f" 平{c['warTies']} 负{c['warLosses']}" if "warTies" in c else "（日志未公开）") +
        f" | 连胜 {c.get('warWinStreak', 0)}",
        f"所需奖杯 {c['requiredTrophies']} | 部落积分 {c['clanPoints']}" +
        (f" | 首都{cap}本" if cap else ""),
    ]
    if c.get("description"):
        lines.append(f"📢 {c['description'][:60]}")
    return "\n".join(lines)


def _fmt_members(c: dict) -> str:
    lines = [f"👥 {c['name']} 成员 ({c['members']}/50)"]
    for i, m in enumerate(c["memberList"][:50], 1):
        role = {"leader": "👑", "coLeader": "⭐", "admin": "🔹"}.get(m["role"], "")
        th = f"{m['townHallLevel']}本 " if m.get("townHallLevel") else ""
        lines.append(f"{i}. {role}{m['name']} {th}🏆{m['trophies']} 捐{m['donations']}")
    return "\n".join(lines)


def _fmt_war(w: dict) -> str:
    state = w.get("state", "notInWar")
    if state == "notInWar":
        return "当前没有部落战"
    us, them = w["clan"], w["opponent"]
    left = _time_left(w)
    lines = [
        f"⚔️ {WAR_STATE.get(state, state)} {w['teamSize']}v{w['teamSize']}" +
        (f" | {left}" if left else ""),
        f"我方 {us['name']}：⭐{us.get('stars', 0)} {us.get('destructionPercentage', 0):.1f}% "
        f"(已进攻 {us.get('attacks', 0)})",
        f"敌方 {them['name']}：⭐{them.get('stars', 0)} {them.get('destructionPercentage', 0):.1f}% "
        f"(已进攻 {them.get('attacks', 0)})",
    ]
    if state == "inWar":
        idle = [m["name"] for m in us.get("members", []) if not m.get("attacks")]
        if idle:
            lines.append("还没打的：" + "、".join(idle[:15]))
    if state in ("preparation", "inWar"):
        lines.append(_predict_line(w))
    return "\n".join(lines)


def _fmt_warlog(log: dict) -> str:
    lines = ["📜 最近部落战"]
    for item in log.get("items", []):
        r = {"win": "✅胜", "lose": "❌负", "tie": "🤝平"}.get(item.get("result"), "?")
        opp = item.get("opponent", {}).get("name", "联赛")
        lines.append(f"{r} vs {opp} ⭐{item['clan']['stars']}-{item.get('opponent', {}).get('stars', '?')}")
    return "\n".join(lines) if len(lines) > 1 else "战争日志未公开或暂无记录"


def _fmt_search(res: dict) -> str:
    items = res.get("items", [])
    if not items:
        return "没搜到，换个关键词试试"
    lines = ["🔍 搜索结果（查详情发：部落 #TAG）"]
    for c in items:
        lines.append(
            f"{c['name']} {c['tag']} | 等级{c['clanLevel']} "
            f"成员{c['members']}/50 需🏆{c['requiredTrophies']}"
        )
    return "\n".join(lines)


def _fmt_donations(c: dict) -> str:
    members = c.get("memberList", [])
    ranked = sorted(members, key=lambda m: -m.get("donations", 0))
    lines = [f"📦 捐兵榜 | {c['name']}（本赛季）"]
    for i, m in enumerate(ranked[:10], 1):
        d, r = m.get("donations", 0), m.get("donationsReceived", 0)
        ratio = f"{d / r:.1f}" if r else ("∞" if d else "-")
        lines.append(f"{i}. {m['name']} 捐{d} 收{r} 比{ratio}")
    lazy = sum(1 for m in members if not m.get("donations"))
    if lazy:
        lines.append(f"⚠️ 0捐兵：{lazy} 人")
    return "\n".join(lines)


def _fmt_raids(res: dict) -> str:
    items = res.get("items", [])
    if not items:
        return "还没有都城突袭记录"
    r = items[0]
    state = "进行中 🔥" if r.get("state") == "ongoing" else "已结束"
    lines = [
        f"⚡ 都城突袭（{state}）",
        f"总掠夺 {r.get('capitalTotalLoot', 0):,} | 出刀 {r.get('totalAttacks', 0)} 次",
        f"完成突袭 {r.get('raidsCompleted', 0)} 轮 | 摧毁敌区 {r.get('enemyDistrictsDestroyed', 0)} 个",
        f"进攻奖章 {r.get('offensiveReward', 0)} | 防守奖章 {r.get('defensiveReward', 0)}",
    ]
    members = r.get("members") or []
    if members:
        top = sorted(members, key=lambda m: -m.get("capitalResourcesLooted", 0))[:5]
        lines.append("掠夺前五：" + "、".join(
            f"{m['name']}({m['capitalResourcesLooted']:,})" for m in top))
    return "\n".join(lines)


# ---------------- 联赛 ----------------

def _fmt_league(g: dict) -> str:
    state = {"preparation": "备战中", "inWar": "进行中", "ended": "已结束"}.get(
        g.get("state"), g.get("state", "?"))
    lines = [f"🏆 联赛 {g.get('season', '')} | {state}", "同组部落："]
    for c in g.get("clans", []):
        lines.append(f"· {c['name']} ({c['tag']}) 等级{c['clanLevel']}")
    lines.append("子功能：联赛-积分榜 / 联赛-奖章 / 联赛-对阵 / 联赛-催刀 / 联赛-敌刀")
    return "\n".join(lines)


async def _cwl_wars(group: dict) -> list[dict]:
    """并发拉取本次联赛所有已生成的对战。"""
    tags = [wt for rnd in group.get("rounds", [])
            for wt in rnd.get("warTags", []) if wt != "#0"]
    return list(await asyncio.gather(*(coc.get_cwl_war(t) for t in tags)))


def _ready_rounds(group: dict) -> list[int]:
    return [i for i, r in enumerate(group.get("rounds", []), 1)
            if any(t != "#0" for t in r.get("warTags", []))]


async def _find_cwl_war(clan_tag: str, group: dict, round_no: int | None):
    """定位某一轮里我们参加的对战。返回 (round_no, war, 错误提示)。"""
    rounds = group.get("rounds", [])
    ready = _ready_rounds(group)
    if not ready:
        return None, None, "联赛对阵还没生成，稍后再查"
    if round_no is None:
        round_no = ready[-1]
    if round_no < 1 or round_no > len(rounds):
        return None, None, f"本次联赛共 {len(rounds)} 场，没有第 {round_no} 场"
    if round_no not in ready:
        return None, None, f"第 {round_no} 场对阵还没生成（当前打到第 {ready[-1]} 场）"
    for wt in rounds[round_no - 1]["warTags"]:
        if wt == "#0":
            continue
        w = await coc.get_cwl_war(wt)
        if _norm_tag(w["clan"]["tag"]) == _norm_tag(clan_tag):
            return round_no, w, None
        if _norm_tag(w["opponent"]["tag"]) == _norm_tag(clan_tag):
            w["clan"], w["opponent"] = w["opponent"], w["clan"]
            return round_no, w, None
    return None, None, f"第 {round_no} 场没找到我们的对战（轮空或数据未生成）"


async def _fmt_cwl_matchup(clan_tag: str, group: dict, round_no: int | None) -> str:
    round_no, war, err = await _find_cwl_war(clan_tag, group, round_no)
    if err:
        return err
    us, them = war["clan"], war["opponent"]
    state = war.get("state")
    left = _time_left(war)
    ours = sorted(us.get("members", []), key=lambda m: m.get("mapPosition", 99))
    theirs = sorted(them.get("members", []), key=lambda m: m.get("mapPosition", 99))
    size = len(ours) or war.get("teamSize", 0)

    # 战斗日：紧凑战报（比分 + 双方未出刀统计 + 我方催刀名单），不再列对位表
    if state == "inWar":
        idle_us = [(i, m["name"]) for i, m in enumerate(ours, 1) if not m.get("attacks")]
        idle_th = sum(1 for m in theirs if not m.get("attacks"))
        lines = [
            f"⚔️ 第{round_no}场 战斗日 | {left}",
            f"我方 {us['name']} {us.get('stars', 0)}⭐ "
            f"{us.get('destructionPercentage', 0):.1f}%（未出刀 {len(idle_us)}/{size}）"
            f" VS 敌方 {them['name']} {them.get('stars', 0)}⭐ "
            f"{them.get('destructionPercentage', 0):.1f}%（未出刀 {idle_th}/{size}）",
            _predict_line(war),
        ]
        if idle_us:
            lines.append("我方未出刀：")
            lines += [f"{i}号 {n}" for i, n in idle_us]
        else:
            lines.append("我方全部出刀完毕 ✅")
        return "\n".join(lines)

    # 备战日/已结束：对位本数表
    lines = [f"⚔️ 联赛第{round_no}场 对阵 {them['name']} ({them['tag']}) | "
             f"{WAR_STATE.get(state, state)}" + (f" | {left}" if left else "")]
    for i, (a, b) in enumerate(zip(ours, theirs), 1):
        lines.append(
            f"{i}. {a['name']} {a['townhallLevel']}本 VS {b['name']} {b['townhallLevel']}本")
    if state == "warEnded":
        lines.append(
            f"比分 ⭐{us.get('stars', 0)}-{them.get('stars', 0)} | "
            f"{us.get('destructionPercentage', 0):.1f}% - {them.get('destructionPercentage', 0):.1f}%"
            f"（详细复盘：联赛-复盘 {round_no}）")
    if state == "preparation":
        lines.append(_predict_line(war))
    return "\n".join(lines)


async def _fmt_idle(clan_tag: str, group: dict, enemy: bool) -> str:
    """未出刀名单（一行一个名字，方便复制去群里@人）。

    联赛战斗日和下一场备战日并存，催刀要定位到正在打的那场。
    """
    round_no = war = None
    for r in reversed(_ready_rounds(group)):
        rn, w, err = await _find_cwl_war(clan_tag, group, r)
        if w and w.get("state") == "inWar":
            round_no, war = rn, w
            break
    if war is None:
        round_no, war, err = await _find_cwl_war(clan_tag, group, None)
        if err:
            return err
    state = war.get("state")
    if state == "preparation":
        return f"第{round_no}场还在备战日（{_time_left(war)}），开战后再来催"
    side = war["opponent"] if enemy else war["clan"]
    idle = [m["name"] for m in
            sorted(side.get("members", []), key=lambda m: m.get("mapPosition", 99))
            if not m.get("attacks")]
    who = "敌方" if enemy else "我方"
    if not idle:
        return f"第{round_no}场{who}全部出刀完毕 ✅"
    left = _time_left(war)
    head = f"⏰ 第{round_no}场 {who}未出刀 {len(idle)}人" + (f"（{left}）" if left else "")
    return "\n".join([head] + idle)


async def _cwl_standings(group: dict) -> list[dict]:
    """小组积分：总星数（胜场+10⭐奖励）→ 摧毁率 排序。"""
    stats = {_norm_tag(c["tag"]): {"name": c["name"], "tag": c["tag"],
                                   "stars": 0, "dest": 0.0, "wins": 0}
             for c in group.get("clans", [])}
    for w in await _cwl_wars(group):
        if w.get("state") not in ("inWar", "warEnded"):
            continue
        for side, other in (("clan", "opponent"), ("opponent", "clan")):
            st = stats.get(_norm_tag(w[side]["tag"]))
            if not st:
                continue
            st["stars"] += w[side].get("stars", 0)
            st["dest"] += w[side].get("destructionPercentage", 0)
            if w.get("state") == "warEnded" and (
                (w[side].get("stars", 0), w[side].get("destructionPercentage", 0))
                > (w[other].get("stars", 0), w[other].get("destructionPercentage", 0))
            ):
                st["wins"] += 1
                st["stars"] += 10  # 联赛胜场奖励星
    return sorted(stats.values(), key=lambda s: (-s["stars"], -s["dest"]))


def _fmt_standings(clan_tag: str, table: list[dict]) -> str:
    lines = ["🏆 联赛积分榜（胜场含+10⭐）"]
    medals_icon = {1: "🥇", 2: "🥈", 3: "🥉"}
    for i, s in enumerate(table, 1):
        me = " ←我们" if _norm_tag(s["tag"]) == _norm_tag(clan_tag) else ""
        icon = medals_icon.get(i, f"{i}.")
        lines.append(f"{icon} {s['name']} ⭐{s['stars']} "
                     f"胜{s['wins']} {s['dest']:.0f}%{me}")
    return "\n".join(lines)


async def _fmt_medals(clan_tag: str, group: dict) -> str:
    clan = await coc.get_clan(clan_tag)
    league = (clan.get("warLeague") or {}).get("name", "")
    entry = MEDAL_TABLE.get(league)
    if not entry:
        return f"未知联赛段位：{league}，奖章表待补充"
    first, step = entry

    table = await _cwl_standings(group)
    rank = next((i for i, s in enumerate(table, 1)
                 if _norm_tag(s["tag"]) == _norm_tag(clan_tag)), None)
    base_now = first - (rank - 1) * step if rank else None

    players = await _cwl_member_stats(group, clan_tag)

    lines = [f"🎖️ 奖章预估 | {_league_cn(league)} | 当前第{rank}名" if rank
             else f"🎖️ 奖章预估 | {_league_cn(league)}"]
    lines.append("名次→基础奖章：" + " ".join(
        f"{i}:{first - (i - 1) * step}" for i in range(1, 9)))
    lines.append("个人所得=基础×(20%+每星10%，8星满额)")
    if base_now and players:
        lines.append(f"—— 按当前第{rank}名（基础{base_now}）预估 ——")
        ranked = sorted(players.values(), key=lambda p: -p["stars"])
        for p in ranked:
            y = min(1.0, 0.2 + 0.1 * p["stars"])
            lines.append(f"{p['name']} {p['stars']}⭐ 出场{p['wars']} "
                         f"→ 约{int(base_now * y)}枚")
    lines.append("(社区公认数值，最终以游戏内为准)")
    return "\n".join(lines)


# ---------------- 玩家 ----------------

def _fmt_player_sub(p: dict, sub: str) -> str:
    if sub == "英雄":
        return _fmt_heroes(p)
    if sub == "部队":
        return _fmt_troops(p)
    if sub == "法术":
        return _fmt_spells(p)
    if sub == "建议":
        return _fmt_advice(p)
    return _fmt_player(p)


def _fmt_player(p: dict) -> str:
    heroes = [h for h in p.get("heroes", []) if h.get("village") == "home"]
    hero_line = " ".join(
        f"{HERO_CN.get(h['name'], h['name'])}{h['level']}" for h in heroes)
    clan = p.get("clan", {})
    role = ROLE_CN.get(p.get("role", ""), "")
    lines = [
        f"👤 {p['name']} ({p['tag']})",
        f"{p['townHallLevel']}本 | 经验 {p['expLevel']} | "
        f"🏆{p['trophies']}（最高 {p.get('bestTrophies', '?')}）",
        f"⭐战争星 {p.get('warStars', 0)} | 进攻胜 {p.get('attackWins', 0)} | "
        f"防守胜 {p.get('defenseWins', 0)}",
        f"捐兵 {p.get('donations', 0)} | 收兵 {p.get('donationsReceived', 0)} | "
        f"首都贡献 {p.get('clanCapitalContributions', 0):,}",
    ]
    if hero_line:
        lines.append(f"英雄：{hero_line}")
    lines.append(f"部落：{clan.get('name', '无')}" + (f"（{role}）" if role else ""))
    lines.append("更多：玩家-英雄 / 玩家-部队 / 玩家-法术")
    return "\n".join(lines)


def _fmt_heroes(p: dict) -> str:
    home = [h for h in p.get("heroes", []) if h.get("village") == "home"]
    builder = [h for h in p.get("heroes", []) if h.get("village") == "builderBase"]
    if not home and not builder:
        return f"{p['name']} 还没有英雄"
    lines = [f"🦸 {p['name']} 的英雄（等级/满级）"]
    for h in home:
        full = "✅" if h["level"] == h.get("maxLevel") else ""
        lines.append(f"{HERO_CN.get(h['name'], h['name'])} {h['level']}/{h.get('maxLevel', '?')}{full}")
    if builder:
        lines.append("— 夜世界 —")
        for h in builder:
            lines.append(f"{HERO_CN.get(h['name'], h['name'])} {h['level']}/{h.get('maxLevel', '?')}")
    return "\n".join(lines)


def _fmt_troops(p: dict) -> str:
    troops, pets, sieges = [], [], []
    for t in p.get("troops", []):
        if t.get("village") != "home":
            continue
        name = t["name"]
        if name.startswith("Super ") or name in SUPER_TROOPS:
            continue  # 超级兵等级跟随原兵种，不重复列
        entry = f"{TROOP_CN.get(name, PET_CN.get(name, name))}{t['level']}/{t.get('maxLevel', '?')}"
        if name in SIEGE:
            sieges.append(entry)
        elif name in PET_CN:
            pets.append(entry)
        else:
            troops.append(entry)
    lines = [f"⚔️ {p['name']} 的部队（等级/满级）"]
    lines += _chunk(troops)
    if sieges:
        lines.append("— 攻城机器 —")
        lines += _chunk(sieges)
    if pets:
        lines.append("— 宠物 —")
        lines += _chunk(pets)
    return "\n".join(lines)


def _fmt_spells(p: dict) -> str:
    spells = [f"{SPELL_CN.get(s['name'], s['name'])}{s['level']}/{s.get('maxLevel', '?')}"
              for s in p.get("spells", []) if s.get("village") == "home"]
    if not spells:
        return f"{p['name']} 还没解锁法术"
    return "\n".join([f"🧪 {p['name']} 的法术（等级/满级）"] + _chunk(spells))


# ---------------- 胜率预估 / 复盘 / 总结 / 成长 ----------------

def _predict_line(war: dict) -> str:
    """简单模型：每刀新星效率（无数据用大本差先验）× 剩余刀数 → 投影星差 → 逻辑函数。"""
    us, them = war["clan"], war["opponent"]
    size = war.get("teamSize") or len(us.get("members", [])) or 1
    per = war.get("attacksPerMember", 1)
    total = size * per

    th_us = sum(m.get("townhallLevel", 0) for m in us.get("members", []))
    th_them = sum(m.get("townhallLevel", 0) for m in them.get("members", []))
    edge = (th_us - th_them) / size * 0.5  # 平均大本差 → 每刀星数修正

    a_us, s_us = us.get("attacks", 0), us.get("stars", 0)
    a_th, s_th = them.get("attacks", 0), them.get("stars", 0)
    prior = 1.9
    rate_us = s_us / a_us if a_us else prior + edge
    rate_th = s_th / a_th if a_th else prior - edge
    proj_us = min(3 * size, s_us + rate_us * max(0, total - a_us))
    proj_th = min(3 * size, s_th + rate_th * max(0, total - a_th))
    diff = (proj_us - proj_th) + (
        us.get("destructionPercentage", 0) - them.get("destructionPercentage", 0)) * 0.01
    sigma = 0.9 * math.sqrt(max(1, (total - a_us) + (total - a_th)))
    p = 1 / (1 + math.exp(-diff / sigma))
    p = min(0.97, max(0.03, p))
    basis = "按阵容本数先验" if war.get("state") == "preparation" else "按当前效率+剩余刀数"
    return f"📈 胜率预估 我方{p * 100:.0f}% : {(1 - p) * 100:.0f}%敌方（{basis}，仅供参考）"


async def _cwl_member_stats(group: dict, clan_tag: str) -> dict:
    """我方每个成员本次联赛的出场次数与总星数。"""
    players: dict[str, dict] = {}
    my = _norm_tag(clan_tag)
    for w in await _cwl_wars(group):
        if w.get("state") not in ("inWar", "warEnded"):
            continue
        for side in ("clan", "opponent"):
            if _norm_tag(w[side]["tag"]) != my:
                continue
            ended = w.get("state") == "warEnded"
            for m in w[side].get("members", []):
                p = players.setdefault(m["tag"], {"name": m["name"], "stars": 0,
                                                  "wars": 0, "atk": 0, "missed": 0})
                p["wars"] += 1
                p["atk"] += len(m.get("attacks", []))
                if ended and not m.get("attacks"):
                    p["missed"] += 1  # 只统计已结束场次的漏刀
                for atk in m.get("attacks", []):
                    p["stars"] += atk.get("stars", 0)
    return players


async def _fmt_review(clan_tag: str, group: dict, round_no: int | None) -> str:
    """对战复盘：默认最近一场已结束的，也可指定场次。"""
    if round_no is None:
        for r in reversed(_ready_rounds(group)):
            _, w, err = await _find_cwl_war(clan_tag, group, r)
            if w and w.get("state") == "warEnded":
                round_no, war = r, w
                break
        else:
            return "还没有打完的场次，打完再来复盘"
    else:
        round_no, war, err = await _find_cwl_war(clan_tag, group, round_no)
        if err:
            return err
        if war.get("state") != "warEnded":
            return f"第{round_no}场还没打完（{WAR_STATE.get(war.get('state'), '')}），先看：联赛-{round_no}"

    us, them = war["clan"], war["opponent"]
    win = (us.get("stars", 0), us.get("destructionPercentage", 0)) > \
          (them.get("stars", 0), them.get("destructionPercentage", 0))
    result = "✅ 胜" if win else "❌ 负"
    theirs_sorted = sorted(them.get("members", []), key=lambda m: m.get("mapPosition", 99))
    theirs_by_tag = {m["tag"]: {**m, "no": i} for i, m in enumerate(theirs_sorted, 1)}
    ours = sorted(us.get("members", []), key=lambda m: m.get("mapPosition", 99))

    lines = [f"📋 第{round_no}场复盘 vs {them['name']} | {result} "
             f"⭐{us.get('stars', 0)}-{them.get('stars', 0)} "
             f"{us.get('destructionPercentage', 0):.1f}%-{them.get('destructionPercentage', 0):.1f}%"]
    three, missed = [], []
    for m in ours:
        atks = m.get("attacks", [])
        if not atks:
            missed.append(m["name"])
            lines.append(f"❌ {m['name']}({m['townhallLevel']}本) 漏刀")
            continue
        a = atks[0]
        d = theirs_by_tag.get(a.get("defenderTag"), {})
        star_icon = "⭐" * a.get("stars", 0) or "0星"
        diff = d.get("townhallLevel", 0) - m["townhallLevel"]
        updown = f"打高{diff}本" if diff > 0 else (f"打低{-diff}本" if diff < 0 else "同本")
        lines.append(f"{star_icon} {m['name']}({m['townhallLevel']}本)"
                     f" → {d.get('no', '?')}号{d.get('townhallLevel', '?')}本"
                     f" {a.get('destructionPercentage', 0)}% {updown}")
        if a.get("stars", 0) == 3:
            three.append(m["name"])
    tail = f"三星 {len(three)} 人"
    if missed:
        tail += f" | 漏刀 {len(missed)} 人：" + "、".join(missed)
    lines.append(tail)
    return "\n".join(lines)


async def _fmt_season_summary(clan_tag: str, group: dict) -> str:
    """联赛结算：最终(或当前)排名、逐场胜负、全员奖章、MVP。"""
    clan = await coc.get_clan(clan_tag)
    league = (clan.get("warLeague") or {}).get("name", "")
    ended = group.get("state") == "ended"

    table = await _cwl_standings(group)
    rank = next((i for i, s in enumerate(table, 1)
                 if _norm_tag(s["tag"]) == _norm_tag(clan_tag)), None)

    # 逐场胜负
    results = []
    my = _norm_tag(clan_tag)
    for r in _ready_rounds(group):
        _, w, _err = await _find_cwl_war(clan_tag, group, r)
        if not w or w.get("state") != "warEnded":
            continue
        win = (w["clan"].get("stars", 0), w["clan"].get("destructionPercentage", 0)) > \
              (w["opponent"].get("stars", 0), w["opponent"].get("destructionPercentage", 0))
        results.append("✅" if win else "❌")

    head = "🏁 联赛总结" if ended else "🏁 联赛总结（进行中，当前累计）"
    lines = [f"{head} {group.get('season', '')}",
             f"{_league_cn(league)} | 第{rank}名 | 逐场：{''.join(results) or '—'}"]

    players = await _cwl_member_stats(group, clan_tag)
    entry = MEDAL_TABLE.get(league)
    if players:
        ranked = sorted(players.values(), key=lambda p: (-p["stars"], -p["wars"]))
        mvp = ranked[0]
        lines.append(f"🏅 MVP：{mvp['name']}（{mvp['stars']}⭐/{mvp['wars']}场）")
        if entry and rank:
            base = entry[0] - (rank - 1) * entry[1]
            lines.append(f"奖章（基础{base}，按第{rank}名）：")
            for p in ranked:
                y = min(1.0, 0.2 + 0.1 * p["stars"])
                lines.append(f"{p['name']} {p['stars']}⭐ → 约{int(base * y)}枚")
    if not ended:
        lines.append("联赛结束后再发一次可得最终结算")
    return "\n".join(lines)


# ---------------- 普通部落战（与联赛功能对齐） ----------------

def _fmt_war_matchup(w: dict) -> str:
    us, them = w["clan"], w["opponent"]
    ours = sorted(us.get("members", []), key=lambda m: m.get("mapPosition", 99))
    theirs = sorted(them.get("members", []), key=lambda m: m.get("mapPosition", 99))
    left = _time_left(w)
    lines = [f"⚔️ 部落战 对阵 {them['name']} | {WAR_STATE.get(w.get('state'), '')}" +
             (f" | {left}" if left else "")]
    for i, (a, b) in enumerate(zip(ours, theirs), 1):
        lines.append(f"{i}. {a['name']} {a['townhallLevel']}本 VS "
                     f"{b['name']} {b['townhallLevel']}本")
    if w.get("state") != "preparation":
        lines.append(f"比分 ⭐{us.get('stars', 0)}-{them.get('stars', 0)} | "
                     f"{us.get('destructionPercentage', 0):.1f}% - "
                     f"{them.get('destructionPercentage', 0):.1f}%")
    return "\n".join(lines)


def _fmt_war_idle(w: dict, enemy: bool) -> str:
    if w.get("state") == "preparation":
        return f"还在备战日（{_time_left(w)}），开战后再来催"
    per = w.get("attacksPerMember", 2)
    side = w["opponent"] if enemy else w["clan"]
    members = sorted(side.get("members", []), key=lambda m: m.get("mapPosition", 99))
    pending = [(i, m["name"], per - len(m.get("attacks", [])))
               for i, m in enumerate(members, 1) if len(m.get("attacks", [])) < per]
    who = "敌方" if enemy else "我方"
    if not pending:
        return f"{who}全部出刀完毕 ✅"
    left = _time_left(w)
    head = f"⏰ 部落战 {who}剩余刀数（共{per}刀/人）" + (f" | {left}" if left else "")
    return "\n".join([head] + [f"{i}号 {n} 剩{r}刀" for i, n, r in pending])


def _fmt_war_review(w: dict) -> str:
    if w.get("state") != "warEnded":
        return "这场还没打完，先看：部落战"
    us, them = w["clan"], w["opponent"]
    win = (us.get("stars", 0), us.get("destructionPercentage", 0)) > \
          (them.get("stars", 0), them.get("destructionPercentage", 0))
    theirs_sorted = sorted(them.get("members", []), key=lambda m: m.get("mapPosition", 99))
    no_by_tag = {m["tag"]: i for i, m in enumerate(theirs_sorted, 1)}
    ours = sorted(us.get("members", []), key=lambda m: m.get("mapPosition", 99))
    lines = [f"📋 部落战复盘 vs {them['name']} | {'✅ 胜' if win else '❌ 负'} "
             f"⭐{us.get('stars', 0)}-{them.get('stars', 0)}"]
    three = missed = 0
    for m in ours:
        atks = m.get("attacks", [])
        if not atks:
            missed += 1
            lines.append(f"❌ {m['name']}({m['townhallLevel']}本) 漏刀")
            continue
        parts = []
        for a in atks:
            if a.get("stars", 0) == 3:
                three += 1
            parts.append(f"{a.get('stars', 0)}⭐{a.get('destructionPercentage', 0)}%"
                         f"({no_by_tag.get(a.get('defenderTag'), '?')}号)")
        lines.append(f"{m['name']}({m['townhallLevel']}本)：" + "、".join(parts))
    lines.append(f"三星进攻 {three} 次 | 漏刀 {missed} 人")
    return "\n".join(lines)


def _fmt_raid_idle(res: dict) -> str:
    items = res.get("items", [])
    if not items or items[0].get("state") != "ongoing":
        return "当前没有进行中的都城突袭（周末开放）"
    r = items[0]
    members = r.get("members") or []
    if not members:
        return "还没人参与本次突袭"
    pending = []
    for m in members:
        limit = m.get("attackLimit", 5) + m.get("bonusAttackLimit", 0)
        if m.get("attacks", 0) < limit:
            pending.append(f"{m['name']} {m.get('attacks', 0)}/{limit}刀")
    if not pending:
        return "参与成员全部打满 ✅（未参与的成员 API 看不到）"
    return "\n".join([f"⚡ 突袭没打满的（{len(pending)}人）"] + pending)


# ---------------- 摸鱼榜 / 升级建议 ----------------

async def _fmt_slackers(tag: str) -> str:
    """管理参考：0捐兵 + 联赛漏刀 + 部落战没打，三合一点名。"""
    clan = await coc.get_clan(tag)
    issues: dict[str, list[str]] = {}

    for m in clan.get("memberList", []):
        if not m.get("donations"):
            issues.setdefault(m["name"], []).append("0捐兵")

    try:
        group = await coc.get_league_group(tag)
        for p in (await _cwl_member_stats(group, tag)).values():
            if p["missed"]:
                issues.setdefault(p["name"], []).append(f"联赛漏{p['missed']}刀")
    except httpx.HTTPStatusError:
        pass  # 不在联赛期

    try:
        war = await coc.get_current_war(tag)
        if war.get("state") == "inWar":
            for m in war["clan"].get("members", []):
                if not m.get("attacks"):
                    issues.setdefault(m["name"], []).append("部落战未出刀")
    except httpx.HTTPStatusError:
        pass

    if not issues:
        return "🎉 全员劳模，无人摸鱼"
    ranked = sorted(issues.items(), key=lambda kv: -len(kv[1]))
    lines = [f"🐟 摸鱼榜 | {clan['name']}（管理参考）"]
    for name, probs in ranked[:15]:
        lines.append(f"{name}：{' | '.join(probs)}")
    if len(ranked) > 15:
        lines.append(f"…另有 {len(ranked) - 15} 人")
    return "\n".join(lines)


# 升级建议的优先级表（经验法则）
ADVICE_TROOPS = ["Root Rider", "Electro Titan", "Dragon Rider", "Electro Dragon",
                 "Dragon", "Yeti", "Hog Rider", "Miner", "Balloon", "Witch",
                 "Lava Hound", "Baby Dragon", "Valkyrie", "Druid"]
ADVICE_SPELLS = ["Rage Spell", "Healing Spell", "Freeze Spell", "Lightning Spell",
                 "Poison Spell", "Earthquake Spell", "Recall Spell", "Overgrowth Spell"]
TH_TIPS = [
    (11, "低本阶段：女皇优先练到位，实验室主升一套主力流派兵，墙慢慢补"),
    (13, "中本阶段：英雄不停工是铁律，攻城机器和狂暴/冰冻跟上"),
    (15, "冲高阶段：宠物屋优先级最高，英雄照旧不停工"),
    (99, "高本阶段：英雄+英雄装备 > 流派主力兵 > 法术，打联赛攒奖章买装备"),
]


def _fmt_advice(p: dict) -> str:
    th = p.get("townHallLevel", 0)
    lines = [f"🧭 升级建议 | {p['name']}（{th}本）"]

    heroes = [h for h in p.get("heroes", []) if h.get("village") == "home"
              and h.get("level", 0) < h.get("maxLevel", 0)]
    if heroes:
        heroes.sort(key=lambda h: h["level"] / max(1, h.get("maxLevel", 1)))
        lines.append("1️⃣ 英雄（永远第一优先，别让他们睡觉）：")
        lines += [f"  {HERO_CN.get(h['name'], h['name'])} {h['level']}/{h['maxLevel']}"
                  f"（差{h['maxLevel'] - h['level']}级）" for h in heroes[:5]]

    troops = {t["name"]: t for t in p.get("troops", []) if t.get("village") == "home"}
    gap_troops = [(n, troops[n]) for n in ADVICE_TROOPS
                  if n in troops and troops[n]["level"] < troops[n].get("maxLevel", 0)]
    if gap_troops:
        lines.append("2️⃣ 主流进攻兵种缺口（挑你在用的流派升）：")
        lines.append("  " + "、".join(
            f"{TROOP_CN.get(n, n)}{t['level']}/{t['maxLevel']}" for n, t in gap_troops[:6]))

    spells = {s["name"]: s for s in p.get("spells", []) if s.get("village") == "home"}
    gap_spells = [(n, spells[n]) for n in ADVICE_SPELLS
                  if n in spells and spells[n]["level"] < spells[n].get("maxLevel", 0)]
    if gap_spells:
        lines.append("3️⃣ 关键法术：")
        lines.append("  " + "、".join(
            f"{SPELL_CN.get(n, n)}{s['level']}/{s['maxLevel']}" for n, s in gap_spells[:6]))

    if len(lines) == 1:
        lines.append("英雄/主力兵/法术全满了，剩下的进游戏清墙和杂兵吧 💪")
    lines.append("💡 " + next(tip for cap, tip in TH_TIPS if th <= cap))
    lines.append("(经验法则排序，具体以你的流派为准；建筑/工人数据 API 不提供)")
    return "\n".join(lines)


SNAP_FIELDS = ("townHallLevel", "expLevel", "trophies", "warStars", "donations")


def snapshot_of(p: dict) -> dict:
    snap = {k: p.get(k, 0) for k in SNAP_FIELDS}
    snap["heroSum"] = sum(h.get("level", 0) for h in p.get("heroes", [])
                          if h.get("village") == "home")
    return snap


async def _fmt_growth(ptag: str) -> str:
    p = await coc.get_player(ptag)
    today = snapshot_of(p)
    store.save_snapshot(p["tag"], today)  # 顺手记录今天
    snaps = store.get_snapshots(p["tag"])
    if len(snaps) < 2:
        return (f"📈 已开始记录 {p['name']} 的成长数据（机器人运行期间每天自动快照），"
                "明天起就能看变化了")
    day0, old = snaps[0]
    labels = [("townHallLevel", "大本"), ("expLevel", "经验"), ("trophies", "奖杯"),
              ("warStars", "战争星"), ("heroSum", "英雄总级"), ("donations", "捐兵(赛季)")]
    lines = [f"📈 {p['name']} 成长（{day0} 起，{len(snaps)} 天记录）"]
    for key, label in labels:
        a, b = old.get(key, 0), today.get(key, 0)
        delta = b - a
        mark = f" (+{delta})" if delta > 0 else (f" ({delta})" if delta < 0 else "")
        lines.append(f"{label} {a} → {b}{mark}")
    lines.append("注：捐兵每赛季清零属正常回落")
    return "\n".join(lines)
