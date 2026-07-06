@echo off
REM Windows 启动脚本：双击运行，或配合任务计划程序开机自启
REM 断线/崩溃后 10 秒自动重启
cd /d %~dp0..
if not exist .env (
    echo [错误] 找不到 .env 文件！把 Mac 上的 .env 和 bindings.db 拷到本目录再运行
    pause
    exit /b 1
)
echo 机器人启动中... 日志见 bot.log（此窗口保持开着，关掉=机器人下线）
:loop
.venv\Scripts\python.exe -m app.ws_main >> bot.log 2>&1
echo [%date% %time%] bot exited, restarting in 10s... >> bot.log
timeout /t 10 /nobreak > nul
goto loop
