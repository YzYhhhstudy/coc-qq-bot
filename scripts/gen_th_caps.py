"""从 coc.py（>=4.0）自带的游戏静态数据推导「每个大本的单位等级上限」，写入 app/th_caps.json。

官方 API 的 maxLevel 是全游戏最高等级、不区分大本，所以「进度」「侦查」需要这张表。
coc.py 4.x 的 static/static_data.json 由官方游戏资源文件转换而来，英雄/兵种/攻城/法术/宠物/装备
每一级都带 required_townhall（该级要求的大本），据此直接得到每本上限。

用法（生成时才需要 coc.py，运行机器人不需要）：
    python3 -m venv /tmp/gen && /tmp/gen/bin/pip install "coc.py>=4"
    /tmp/gen/bin/python scripts/gen_th_caps.py
游戏大版本更新后，等 coc.py 发新版再重跑一次即可；表里没有的新单位会自动退回 API 的全游戏最高等级。
"""
import json
import os
import sys
from datetime import date

try:
    import coc
except ImportError:
    sys.exit("需要先 pip install 'coc.py>=4'（仅生成用）")

STATIC = os.path.join(os.path.dirname(coc.__file__), "static", "static_data.json")
OUT = os.path.join(os.path.dirname(__file__), "..", "app", "th_caps.json")

if not os.path.exists(STATIC):
    sys.exit(f"没找到 {STATIC}：需要 coc.py 4.0 以上版本（pip install 'coc.py>=4'）")
with open(STATIC, encoding="utf-8") as f:
    data = json.load(f)

MAX_TH = len(next(b for b in data["buildings"] if b["name"] == "Town Hall")["levels"])


def caps_by_th(unit: dict) -> dict[str, int]:
    """每级要求的大本 → {大本: 该本可升到的最高等级}。"""
    req = [lv.get("required_townhall") or 0 for lv in unit.get("levels", [])]
    out = {}
    for th in range(1, MAX_TH + 1):
        cap = sum(1 for r in req if r <= th)
        if cap:
            out[str(th)] = cap
    return out


def build(kind: str) -> dict[str, dict[str, int]]:
    result = {}
    for unit in data[kind]:
        if unit.get("village", "home") != "home":  # 夜世界单位不要
            continue
        name = unit["name"]
        if name in result:  # 同名衍生单位排在正式单位之后，首个优先
            continue
        caps = caps_by_th(unit)
        if caps:
            result[name] = caps
    return result


out = {
    "source": f"coc.py {coc.__version__} static game data",
    "generated": date.today().isoformat(),
    "max_th": MAX_TH,
    **{kind: build(kind) for kind in ("heroes", "troops", "spells", "pets", "equipment")},
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print(f"已生成 {os.path.normpath(OUT)}：数据到 {MAX_TH} 本，"
      + "，".join(f"{k}{len(v)}项" for k, v in out.items() if isinstance(v, dict)))
