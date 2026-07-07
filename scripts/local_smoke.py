"""本地冒烟测试：不碰 QQ 群，直接测指令逻辑 + Webhook 验签/回调校验。

用法: .venv/bin/python scripts/local_smoke.py [#部落TAG]
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from nacl.signing import SigningKey

from app import commands
from app.main import app, _signing_key, _verify_key

FAKE_GROUP = "smoke-test-group"


async def test_commands(clan_tag: str):
    print("=== 指令逻辑（真实 CoC 数据）===")
    for cmd in [f"绑定 {clan_tag}", "部落", "成员", "战况", "战绩",
                "联赛", "突袭", "搜索 tribe", "帮助",
                "部落战-侦查", "联赛-侦查", "联赛-阵容 15",
                "突袭-历史", "都城", "周报",
                "排行-部落 国服", "排行-玩家 全球", "排行-传奇"]:
        reply = await commands.handle(FAKE_GROUP, cmd)
        print(f"\n>>> @bot {cmd}\n{reply}")


def test_webhook():
    print("\n=== Webhook 验签 ===")
    client = TestClient(app)

    # 1) op=13 回调地址校验（模拟平台的挑战请求）
    body = json.dumps({"op": 13, "d": {"plain_token": "Arq0AZTr", "event_ts": "1725442341"}}).encode()
    ts = "1725442341"
    sig = _signing_key.sign(ts.encode() + body).signature.hex()
    r = client.post("/qq/webhook", content=body,
                    headers={"X-Signature-Ed25519": sig, "X-Signature-Timestamp": ts,
                             "Content-Type": "application/json"})
    assert r.status_code == 200, r.text
    resp = r.json()
    _verify_key.verify(("1725442341" + "Arq0AZTr").encode(), bytes.fromhex(resp["signature"]))
    print("op=13 回调校验: 通过（应答签名可被平台公钥验证）")

    # 2) 错误签名必须被拒
    r = client.post("/qq/webhook", content=body,
                    headers={"X-Signature-Ed25519": "00" * 64, "X-Signature-Timestamp": ts,
                             "Content-Type": "application/json"})
    assert r.status_code == 401
    print("伪造签名: 已拒绝 (401)")

    # 3) 群 @ 消息事件走通指令分发（拦截真实发送，只看回复内容）
    from app import main as main_mod
    captured = {}

    async def fake_send(group_openid, content, msg_id):
        captured.update(group=group_openid, content=content, msg_id=msg_id)

    main_mod.qq_api.send_group_message = fake_send
    event = json.dumps({"op": 0, "t": "GROUP_AT_MESSAGE_CREATE",
                        "d": {"id": "fake-msg-id", "group_openid": FAKE_GROUP,
                              "author": {"member_openid": "u1"}, "content": " 部落"}}).encode()
    sig = _signing_key.sign(ts.encode() + event).signature.hex()
    r = client.post("/qq/webhook", content=event,
                    headers={"X-Signature-Ed25519": sig, "X-Signature-Timestamp": ts,
                             "Content-Type": "application/json"})
    assert r.status_code == 200 and captured.get("content"), (r.text, captured)
    print(f"群消息事件: 通过，机器人将回复:\n{captured['content']}")


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "#2GP9CGR8Q"
    asyncio.run(test_commands(tag))
    test_webhook()
    print("\n✅ 冒烟测试全部通过")
