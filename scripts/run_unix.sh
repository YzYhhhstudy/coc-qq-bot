#!/bin/bash
# macOS / Linux 启动脚本：守护循环，崩溃/断线 10 秒自动重启
# 用法: ./scripts/run_unix.sh   （保持终端开着；后台跑用 nohup 或 launchd/systemd）
cd "$(dirname "$0")/.." || exit 1

if [ ! -f .env ]; then
    echo "[ERROR] .env not found! 照 .env.example 建一个 .env 填入密钥再运行"
    exit 1
fi

echo "Bot starting... logs in bot.log (Ctrl+C 停止)"
while true; do
    .venv/bin/python -m app.ws_main >> bot.log 2>&1
    echo "[$(date '+%F %T')] bot exited, restarting in 10s..." >> bot.log
    sleep 10
done
