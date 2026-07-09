"""WebSocket 模式入口（官方 botpy SDK）。

出站长连接，不需要公网 IP / 域名 / 备案 / 隧道，笔记本换网络也能跑。
用法: .venv/bin/python -m app.ws_main
"""
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import asyncio

import botpy
from botpy.message import C2CMessage, GroupMessage

from app import coc, commands, store, updater

_snap_task = None
_upd_task = None


async def _update_loop():
    """每小时检查 GitHub main 是否有新版本；开了自动更新就地升级并重启进程。"""
    await asyncio.sleep(120)  # 启动后先稳定运行一会
    while True:
        new = await updater.check()
        if new and updater.AUTO:
            print(f"📦 发现新版本 {new}，自动更新中…")
            err = await updater.apply_update()  # 成功则进程退出，守护循环重启
            if err:
                print(f"自动更新失败（保持当前版本运行）：{err}")
        await asyncio.sleep(3600)


async def _snapshot_loop():
    """每 12 小时快照：已绑定玩家的成长数据 + 已绑定部落的全员数据（周报用）。

    同日覆盖，等效每日一条。
    """
    while True:
        for tag in store.all_bound_player_tags():
            try:
                store.save_snapshot(tag, commands.snapshot_of(await coc.get_player(tag)))
            except Exception:
                pass  # 单个失败不影响其他玩家
        for ctag in store.all_bound_clan_tags():
            try:
                members = (await coc.get_clan(ctag)).get("memberList", [])
                profiles = await coc.get_players([m["tag"] for m in members],
                                                 concurrency=5)
                store.save_member_snapshot(
                    ctag, commands.member_snapshot_of(members, profiles))
            except Exception:
                pass  # 单个部落失败不影响其他部落
        await asyncio.sleep(12 * 3600)


class CocBot(botpy.Client):
    async def on_ready(self):
        global _snap_task, _upd_task
        loop = asyncio.get_event_loop()
        if _snap_task is None or _snap_task.done():
            _snap_task = loop.create_task(_snapshot_loop())
        if _upd_task is None or _upd_task.done():
            _upd_task = loop.create_task(_update_loop())
        print(f"✅ 机器人「{self.robot.name}」已连接网关，等待消息…")

    # 群聊 @ 消息（平台开放群场景后自动生效，绑定关系按群存）
    async def on_group_at_message_create(self, message: GroupMessage):
        reply = await commands.handle(message.group_openid, (message.content or "").strip())
        if reply:
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0,
                msg_id=message.id,
                content=reply,
            )

    # 私聊消息（沙箱期主用通道，绑定关系按用户存）
    async def on_c2c_message_create(self, message: C2CMessage):
        user_key = f"user:{message.author.user_openid}"
        reply = await commands.handle(user_key, (message.content or "").strip())
        if reply:
            await message._api.post_c2c_message(
                openid=message.author.user_openid,
                msg_type=0,
                msg_id=message.id,
                content=reply,
            )


if __name__ == "__main__":
    import asyncio
    # botpy 依赖隐式事件循环，Python 3.12+ 需手动创建
    asyncio.set_event_loop(asyncio.new_event_loop())

    intents = botpy.Intents(public_messages=True)  # 群/单聊公域消息事件
    client = CocBot(intents=intents, is_sandbox=True)  # 上线过审后改 False
    client.run(appid=os.environ["QQ_APP_ID"], secret=os.environ["QQ_APP_SECRET"])
