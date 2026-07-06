@echo off
REM Windows 启动脚本：双击运行，或配合任务计划程序开机自启
REM 断线/崩溃后 10 秒自动重启
cd /d %~dp0..
:loop
.venv\Scripts\python.exe -m app.ws_main >> bot.log 2>&1
echo [%date% %time%] bot exited, restarting in 10s... >> bot.log
timeout /t 10 /nobreak > nul
goto loop
