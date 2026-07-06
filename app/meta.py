"""版本 meta 数据：流行流派 + 阵型资源。

⚠️ 这是人工维护的数据文件，随版本平衡性调整需要更新（建议每月联赛前刷新一次）。
troops/spells 用 API 英文名（用于检查玩家等级）；超级兵按原兵种登记。
来源：BlueprintCoC / cocbasedrop / TapTap / bilibili 流派统计。
"""

META_UPDATED = "2026-07-06"

STRATEGIES = [
    {
        "key": "隐龙龙骑",
        "aliases": ["隐龙", "公爵龙骑", "隐身龙骑"],
        "th": (17, 18),
        "desc": "龙公爵隐身开场吃掉核心防御，龙骑士主力推进，当前 T0 空军",
        "heroes": "龙公爵(Dragon Duke) + 女皇(巨箭)；隐身法术保公爵",
        "troops": ["Dragon Rider"],
        "spells": ["Invisibility Spell", "Overgrowth Spell", "Revive Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h6p17e43_49-2m1p16e4_34-4p4e6_13-7p10e52_59i2x65-1x5-1x188d1x70-1x98u1x0-4x1-7x57-1x23-3x63-8x65-1x17-1x10-1x6s2x5-6x35-2x120-1x9",
    },
    {
        "key": "超投碾压",
        "aliases": ["超级投石手", "超投", "投石碾压"],
        "th": (18, 18),
        "desc": "公爵开场 + 超级投石手地面碾压，被称为当前最超模的地面推进",
        "heroes": "龙公爵 + 女皇(火箭背包)",
        "troops": ["Bowler"],  # 超级投石手按投石手等级
        "spells": ["Rage Spell", "Healing Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h6p16e43_44-1p3e48_39-2p7e19_4-7p10e59_52i1x64-1x147-2x188d2x2u2x1-2x28-1x5-5x7-1x23-1x58-6x80-1x97-1x95-1x10-1x75-1x135-1x87s6x35-2x120-1x17-1x98",
    },
    {
        "key": "九头蛇",
        "aliases": ["hydra", "杂交龙流", "图腾九头蛇"],
        "th": (17, 18),
        "desc": "飞龙+龙骑士+喷火龙宝宝+火箭气球全面施压，靠图腾/冰冻控场",
        "heroes": "龙公爵(火箭背包) + 女皇(巨箭)",
        "troops": ["Dragon", "Dragon Rider", "Baby Dragon", "Balloon"],
        "spells": ["Freeze Spell", "Skeleton Spell", "Revive Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h1p9e17_48-2p16e4_34-6p4e43_49-7p11e52_53i3x63-2x5-1x188d1x70-1x98u2x0-4x1-4x57-1x23-3x63-9x65-1x17-2x10-1x75-1x87-1x91s2x5-3x120-1x9-4x10-1x17",
    },
    {
        "key": "超龙流",
        "aliases": ["超级飞龙", "超龙"],
        "th": (18, 18),
        "desc": "超级飞龙正面平推 + 火箭气球开路，冰冻/图腾压制单点高伤",
        "heroes": "龙公爵(火箭背包) + 女皇(巨箭) + 守护 + 亡灵王子",
        "troops": ["Dragon", "Balloon", "Minion"],
        "spells": ["Freeze Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h7p11e52_53-2p16e4_34-1p9e17_48-6p4e43_49i1x81-3x5-1x188d2x10-2x5u7x81-2x23-5x57s5x120-1x9-1x17-1x70-1x98",
    },
    {
        "key": "火球超雪怪",
        "aliases": ["超雪怪", "火球雪怪", "雪怪碾压"],
        "th": (17, 17),
        "desc": "守护火球轰核心 + 滚木机戈仑抗伤 + 超级雪怪倾泻，容错极高",
        "heroes": "守护(火球) + 皇家战士冲锋",
        "troops": ["Yeti", "Golem"],
        "spells": ["Rage Spell", "Healing Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h0p4e14_8-1p9e17_48-2p16e22_24-4p10e40_13i1x147-1x58-1x5-1x135d1x9-1x3u3x1-3x5-1x6-4x7-2x10-1x12-1x23-2x28-1x53-2x58-3x82-4x147-1x150s4x35-2x10-1x2-2x5-1x17",
    },
    {
        "key": "战士古藤",
        "aliases": ["古藤流", "RC古藤", "根骑士", "古藤骑士流"],
        "th": (15, 17),
        "desc": "皇家战士先手拆关键防御，古藤骑士海推进，藤蔓法术锁大本",
        "heroes": "皇家战士(游走) + 守护跟推",
        "troops": ["Root Rider", "Valkyrie"],
        "spells": ["Overgrowth Spell", "Rage Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h0p9e14_32-1p16e17_48-2p8e4_24-4p10e40_13i1x110-3x57-2x5-1x0-1x135d1x70-1x9u4x1-5x26-4x57-4x4-3x5-5x7-1x23-4x110-1x10-4x12-2x58-2x82-1x97s6x35-1x53-1x70-1x5",
    },
    {
        "key": "RC双龙",
        "aliases": ["双龙", "战士双龙", "隐闰双龙"],
        "th": (16, 17),
        "desc": "皇家战士先手清防空/单头，双倍飞龙收割，17本高强度打法",
        "heroes": "皇家战士 + 守护",
        "troops": ["Dragon", "Balloon"],
        "spells": ["Rage Spell", "Freeze Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h1p9e17_48-2m1p16e4_34-6p4e35_43-4p10e40_12i4x84-1x5-1x10-1x75d1x10-1x35-1x9u1x28-11x8-2x23-1x82-1x58-8x57-2x10-3x1s11x35",
    },
    {
        "key": "火球火箭气球",
        "aliases": ["火箭气球", "火球气球"],
        "th": (17, 17),
        "desc": "守护火球点核心 + 火箭气球定点爆破防空链，节奏快",
        "heroes": "守护(火球) + 女皇(巨箭)",
        "troops": ["Balloon", "Minion"],
        "spells": ["Lightning Spell", "Freeze Spell"],
        "army": "https://link.clashofclans.com/en/?action=CopyArmy&army=h0p4e8_14-1p9e48_39-2p16e22_24-4p10e13_6i1x10-1x5-4x84-1x75-1x91d1x2-1x9u1x0-2x1-2x28-2x5-16x57-2x6-5x7-1x23-7x10-3x150-1x58-2x82-1x135-1x75-1x91s1x2-1x5-5x35-2x10-1x109",
    },
    {
        "key": "野猪矿工混合",
        "aliases": ["混合流", "猪矿", "hybrid"],
        "th": (13, 16),
        "desc": "女皇冲锋开路 + 野猪/矿工混合收割，多年常青树，中本必学",
        "heroes": "女皇冲锋(隐身辅助) + 守护跟主力",
        "troops": ["Hog Rider", "Miner"],
        "spells": ["Healing Spell", "Rage Spell", "Poison Spell"],
        "army": None,  # 常青流派，进游戏军队页搜 Hybrid 或看 blueprintcoc.com
    },
    {
        "key": "天狗气球",
        "aliases": ["lavaloon", "狗球", "熔岩气球"],
        "th": (11, 14),
        "desc": "熔岩猎犬抗伤 + 气球海拆防御，低中本空军经典",
        "heroes": "王皇看星级需求出击",
        "troops": ["Lava Hound", "Balloon", "Minion"],
        "spells": ["Rage Spell", "Haste Spell", "Freeze Spell"],
        "army": None,
    },
]

# 公众号/中文社区精选文章（人工收录：看到好文把链接发给 Claude 加进来）
# 格式: (标题, 链接, 适用大本下限, 适用大本上限)
WECHAT_ARTICLES: list[tuple[str, str, int, int]] = [
    # 暂无收录——微信文章无法自动搜索，靠人工投喂
]

# 阵型资源站（分级列表页，进去挑选后一键复制到游戏）
def base_links(th: int, fun: bool) -> list[tuple[str, str]]:
    if fun:
        links = [("艺术/整活阵合集(含皮卡丘/爱心/文字类)",
                  f"https://clashofclans-layouts.com/plans/th_{th}/troll/")]
        if th >= 18:
            links.append(("TH18 全类型阵型(含 Art 分区)",
                          "https://clashofclans-baselinks.com/th18-base-link/"))
        return links
    links = [
        ("Blueprint 本月 CWL 阵型(全大本,月更)",
         "https://blueprintcoc.com/blogs/coc-base-layouts/best-cwl-base-every-th"),
        (f"TH{th} 部落战阵型合集",
         f"https://clashofclans-layouts.com/plans/th_{th}/war/"),
        ("黑羽COC 阵型分享站(中文)", "http://coc.6oh.cn/"),
        (f"B站 {th}本阵型视频(链接在简介)",
         f"https://search.bilibili.com/all?keyword=部落冲突{th}本阵型"),
    ]
    if th in (17, 18):
        links.append((f"ClashCodes TH{th} 防三星阵",
                      f"https://clashcodes.com/bases/th{th}" + ("-war" if th == 17 else "")))
    links += [(f"📰 {t}", u) for t, u, lo, hi in WECHAT_ARTICLES if lo <= th <= hi]
    return links


def find_strategy(name: str) -> dict | None:
    name = name.strip().lower()
    for s in STRATEGIES:
        if name == s["key"].lower() or name in [a.lower() for a in s["aliases"]]:
            return s
    return None


def strategies_for_th(th: int) -> list[dict]:
    return [s for s in STRATEGIES if s["th"][0] <= th <= s["th"][1]]
