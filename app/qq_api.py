"""QQ 机器人 v2 API：access_token 管理 + 发送群消息（被动回复）。"""
import os
import time

import httpx

TOKEN_URL = "https://bots.qq.com/app/getAppAccessToken"
# 机器人"发布上线"前只能调沙箱环境；上线后切正式环境（.env 里改 QQ_API_BASE）
API_BASE = os.environ.get("QQ_API_BASE", "https://sandbox.api.sgroup.qq.com")

_token_cache = {"token": None, "expires_at": 0.0}


async def _get_access_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]
    async with httpx.AsyncClient() as client:
        resp = await client.post(TOKEN_URL, json={
            "appId": os.environ["QQ_APP_ID"],
            "clientSecret": os.environ["QQ_APP_SECRET"],
        })
        resp.raise_for_status()
        data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + int(data["expires_in"])
    return _token_cache["token"]


async def send_group_message(group_openid: str, content: str, reply_to_msg_id: str):
    """带 msg_id 即为被动回复，不消耗主动消息配额。"""
    token = await _get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/v2/groups/{group_openid}/messages",
            headers={"Authorization": f"QQBot {token}"},
            json={
                "content": content,
                "msg_type": 0,  # 0 = 纯文本
                "msg_id": reply_to_msg_id,
                "msg_seq": 1,
            },
        )
        resp.raise_for_status()
