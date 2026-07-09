"""自动更新：比对本地 git commit 与 GitHub main 最新 commit。

发现新版本时（AUTO_UPDATE=1，默认开）自动 git pull + 装依赖，然后退出进程——
run_windows.bat / systemd 的守护会用新代码重新拉起。关闭自动更新则只在
「版本」查询里提示手动跑 update.bat。
"""
import asyncio
import os
import sys

import httpx

REPO = os.environ.get("GITHUB_REPO", "YzYhhhstudy/coc-qq-bot")
AUTO = os.environ.get("AUTO_UPDATE", "1") == "1"

update_available: str | None = None  # 远端新版本短 sha（无更新时为 None）


async def _run(*cmd: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return proc.returncode or 0, out.decode(errors="replace").strip()


async def local_sha() -> str | None:
    code, out = await _run("git", "rev-parse", "HEAD")
    return out[:40] if code == 0 else None


async def remote_sha() -> str | None:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://api.github.com/repos/{REPO}/commits/main",
            headers={"Accept": "application/vnd.github+json"})
        r.raise_for_status()
        return r.json()["sha"]


async def check() -> str | None:
    """刷新 update_available；网络/git 失败时保持原状不打扰主流程。"""
    global update_available
    try:
        lo, rm = await asyncio.gather(local_sha(), remote_sha())
        update_available = rm[:7] if (lo and rm and lo != rm) else None
    except Exception:
        pass
    return update_available


async def apply_update() -> str | None:
    """拉代码+装依赖，成功则退出进程交给守护循环重启。返回错误信息或不返回。"""
    code, out = await _run("git", "pull", "--ff-only")
    if code != 0:
        return f"git pull 失败：{out[-200:]}"
    await _run(sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt")
    print("✅ 更新完成，重启进程加载新代码…")
    os._exit(0)
