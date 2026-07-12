#!/bin/bash
# macOS / Linux 一键更新：拉代码 → 装依赖 → 重启机器人
# 机器人运行中可直接执行；只精准杀 bot 进程，不影响其他 Python 程序
cd "$(dirname "$0")/.." || exit 1

echo "[1/3] Pulling latest code..."
git pull --ff-only || { echo "[ERROR] git pull failed"; exit 1; }

echo "[2/3] Installing dependencies (only if changed)..."
.venv/bin/pip install -q -r requirements.txt

echo "[3/3] Restarting bot..."
pkill -f "app.ws_main" 2>/dev/null

sleep 13
if pgrep -f "app.ws_main" > /dev/null; then
    echo "OK: bot restarted with new code (via guard loop)."
else
    echo "Guard loop not running, starting bot in background (nohup)..."
    nohup ./scripts/run_unix.sh > /dev/null 2>&1 &
    echo "Started. Logs: bot.log"
fi
