"""SQLite 存储：绑定关系 + 玩家成长快照。"""
import json
import os
import sqlite3
from datetime import datetime, timezone

_DB = os.environ.get("DB_PATH", "bindings.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS bindings ("
        " group_openid TEXT PRIMARY KEY,"
        " clan_tag TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS player_bindings ("
        " owner_key TEXT PRIMARY KEY,"
        " player_tag TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS snapshots ("
        " player_tag TEXT NOT NULL,"
        " day TEXT NOT NULL,"
        " data TEXT NOT NULL,"
        " PRIMARY KEY (player_tag, day))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS member_snapshots ("
        " clan_tag TEXT NOT NULL,"
        " day TEXT NOT NULL,"
        " data TEXT NOT NULL,"       # JSON: {player_tag: {name, th, trophies, donations, ...}}
        " PRIMARY KEY (clan_tag, day))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS shared_links ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " kind TEXT NOT NULL,"       # base=阵型 / strategy=流派
        " url TEXT NOT NULL UNIQUE,"
        " note TEXT NOT NULL DEFAULT '',"
        " th INTEGER,"               # 备注里带"17本"则记下，用于按大本过滤
        " submitter TEXT NOT NULL DEFAULT '匿名',"
        " day TEXT NOT NULL)"
    )
    return conn


def bind(group_openid: str, clan_tag: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO bindings (group_openid, clan_tag) VALUES (?, ?)"
            " ON CONFLICT(group_openid) DO UPDATE SET clan_tag = excluded.clan_tag",
            (group_openid, clan_tag),
        )


def get_clan_tag(group_openid: str) -> str | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT clan_tag FROM bindings WHERE group_openid = ?", (group_openid,)
        ).fetchone()
    return row[0] if row else None


def unbind(group_openid: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM bindings WHERE group_openid = ?", (group_openid,))
    return cur.rowcount > 0


def unbind_player(owner_key: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM player_bindings WHERE owner_key = ?", (owner_key,))
    return cur.rowcount > 0


def bind_player(owner_key: str, player_tag: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO player_bindings (owner_key, player_tag) VALUES (?, ?)"
            " ON CONFLICT(owner_key) DO UPDATE SET player_tag = excluded.player_tag",
            (owner_key, player_tag),
        )


def get_player_tag(owner_key: str) -> str | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT player_tag FROM player_bindings WHERE owner_key = ?", (owner_key,)
        ).fetchone()
    return row[0] if row else None


def all_bound_player_tags() -> list[str]:
    with _conn() as conn:
        rows = conn.execute("SELECT DISTINCT player_tag FROM player_bindings").fetchall()
    return [r[0] for r in rows]


def all_bound_clan_tags() -> list[str]:
    with _conn() as conn:
        rows = conn.execute("SELECT DISTINCT clan_tag FROM bindings").fetchall()
    return [r[0] for r in rows]


def save_snapshot(player_tag: str, data: dict) -> None:
    """每天每玩家一条，同日覆盖。"""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _conn() as conn:
        conn.execute(
            "INSERT INTO snapshots (player_tag, day, data) VALUES (?, ?, ?)"
            " ON CONFLICT(player_tag, day) DO UPDATE SET data = excluded.data",
            (player_tag, day, json.dumps(data)),
        )


def save_member_snapshot(clan_tag: str, data: dict) -> None:
    """每天每部落一条（全体成员打包成一个 JSON），同日覆盖。"""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _conn() as conn:
        conn.execute(
            "INSERT INTO member_snapshots (clan_tag, day, data) VALUES (?, ?, ?)"
            " ON CONFLICT(clan_tag, day) DO UPDATE SET data = excluded.data",
            (clan_tag, day, json.dumps(data)),
        )


def get_member_snapshots(clan_tag: str, limit_days: int = 10) -> list[tuple[str, dict]]:
    """按日期升序返回最近 N 天的部落成员快照。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT day, data FROM member_snapshots WHERE clan_tag = ?"
            " ORDER BY day DESC LIMIT ?", (clan_tag, limit_days),
        ).fetchall()
    return [(d, json.loads(j)) for d, j in reversed(rows)]


def add_shared_link(kind: str, url: str, note: str, th: int | None, submitter: str) -> bool:
    """收录一条群友分享的链接；重复 URL 返回 False。"""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        with _conn() as conn:
            conn.execute(
                "INSERT INTO shared_links (kind, url, note, th, submitter, day)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (kind, url, note, th, submitter, day),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def list_shared_links(kind: str, th: int | None = None) -> list[tuple]:
    """按种类（可选按大本）取分享，新的在前。th 为 None 的收录对所有大本可见。"""
    q = "SELECT id, url, note, th, submitter, day FROM shared_links WHERE kind = ?"
    params: list = [kind]
    if th is not None:
        q += " AND (th IS NULL OR th = ?)"
        params.append(th)
    q += " ORDER BY id DESC LIMIT 10"
    with _conn() as conn:
        return conn.execute(q, params).fetchall()


def all_shared_links() -> list[tuple]:
    with _conn() as conn:
        return conn.execute(
            "SELECT id, kind, url, note, th, submitter, day FROM shared_links"
            " ORDER BY id DESC LIMIT 30").fetchall()


def delete_shared_link(link_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM shared_links WHERE id = ?", (link_id,))
    return cur.rowcount > 0


def get_snapshots(player_tag: str, limit_days: int = 30) -> list[tuple[str, dict]]:
    """按日期升序返回最近 N 天的快照。"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT day, data FROM snapshots WHERE player_tag = ?"
            " ORDER BY day DESC LIMIT ?", (player_tag, limit_days),
        ).fetchall()
    return [(d, json.loads(j)) for d, j in reversed(rows)]
