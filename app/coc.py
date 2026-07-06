"""Clash of Clans 官方 API 封装，带 60 秒内存缓存（同一群反复查询不打爆限流）。

文档: https://developer.clashofclans.com/#/documentation
"""
import os
import time
import urllib.parse

import httpx

CACHE_TTL = 60
_cache: dict[str, tuple[float, dict]] = {}


def _base_url() -> str:
    return os.environ.get("COC_BASE_URL", "https://api.clashofclans.com/v1")


async def _get(path: str, ttl: int = CACHE_TTL) -> dict:
    now = time.time()
    if path in _cache and now - _cache[path][0] < ttl:
        return _cache[path][1]
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base_url()}{path}",
            headers={"Authorization": f"Bearer {os.environ['COC_TOKEN']}"},
        )
        resp.raise_for_status()
        data = resp.json()
    _cache[path] = (now, data)
    return data


def _enc(tag: str) -> str:
    tag = tag.upper().replace("O", "0")
    if not tag.startswith("#"):
        tag = "#" + tag
    return urllib.parse.quote(tag, safe="")


async def get_clan(tag: str) -> dict:
    return await _get(f"/clans/{_enc(tag)}")


async def get_members(tag: str) -> dict:
    return await _get(f"/clans/{_enc(tag)}/members")


async def get_current_war(tag: str) -> dict:
    return await _get(f"/clans/{_enc(tag)}/currentwar")


async def get_war_log(tag: str) -> dict:
    return await _get(f"/clans/{_enc(tag)}/warlog?limit=5")


async def get_player(tag: str) -> dict:
    return await _get(f"/players/{_enc(tag)}")


async def get_league_group(tag: str) -> dict:
    """联赛(CWL)分组，仅联赛周有数据。"""
    return await _get(f"/clans/{_enc(tag)}/currentwar/leaguegroup")


async def get_capital_raids(tag: str) -> dict:
    """都城突袭周末，最近一期。"""
    return await _get(f"/clans/{_enc(tag)}/capitalraidseasons?limit=1")


async def search_clans(name: str) -> dict:
    return await _get(f"/clans?name={urllib.parse.quote(name)}&limit=5")


async def get_cwl_war(war_tag: str) -> dict:
    """联赛单场对战详情（war_tag 来自 leaguegroup 的 rounds）。已结束的场次结果不变，缓存放宽。"""
    path = f"/clanwarleagues/wars/{_enc(war_tag)}"
    data = await _get(path)
    if data.get("state") == "warEnded":
        _cache[path] = (time.time() + 3600, data)  # 已结束：约1小时内不再重复拉取
    return data
