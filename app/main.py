"""QQ 开放平台 Webhook 入口。

流程：验签 → 回调地址校验(op=13) → 群 @ 消息(GROUP_AT_MESSAGE_CREATE) → 分发指令 → 被动回复。
文档: https://bot.q.qq.com/wiki/develop/api-v2/dev-prepare/interface-framework/event-emit.html
"""
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, Response
from nacl.signing import SigningKey

from . import commands, qq_api

app = FastAPI()

# QQ 的验签方式：用 AppSecret 重复填充到 32 字节作为 ed25519 种子，
# 平台用该密钥对签名，我们用同一种子派生的密钥对验证/应答。
_secret = os.environ["QQ_APP_SECRET"]
_seed = (_secret * (32 // len(_secret) + 1))[:32].encode()
_signing_key = SigningKey(_seed)
_verify_key = _signing_key.verify_key

OP_DISPATCH = 0          # 事件推送
OP_CALLBACK_VALIDATE = 13  # 回调地址校验


@app.post("/qq/webhook")
async def qq_webhook(request: Request):
    body = await request.body()

    # 1) 验签：平台在 header 里带 Ed25519 签名，签名内容为 timestamp + body
    sig = request.headers.get("X-Signature-Ed25519", "")
    ts = request.headers.get("X-Signature-Timestamp", "")
    try:
        _verify_key.verify(ts.encode() + body, bytes.fromhex(sig))
    except Exception:
        return Response(status_code=401)

    payload = await request.json()
    op = payload.get("op")

    # 2) 配置回调地址时的一次性校验
    if op == OP_CALLBACK_VALIDATE:
        d = payload["d"]
        msg = (d["event_ts"] + d["plain_token"]).encode()
        signature = _signing_key.sign(msg).signature.hex()
        return {"plain_token": d["plain_token"], "signature": signature}

    # 3) 事件推送
    if op == OP_DISPATCH and payload.get("t") == "GROUP_AT_MESSAGE_CREATE":
        d = payload["d"]
        group_openid = d["group_openid"]
        msg_id = d["id"]
        content = (d.get("content") or "").strip()

        reply = await commands.handle(group_openid, content)
        if reply:
            await qq_api.send_group_message(group_openid, reply, msg_id)

    return {"ok": True}
