@echo off
REM CoC QQ Bot launcher (auto-restart on crash). Keep this window open.
cd /d %~dp0..
if not exist .env (
    echo [ERROR] .env not found! Copy .env and bindings.db from the old machine into this folder, then run again.
    pause
    exit /b 1
)
echo Bot starting... logs in bot.log ^(closing this window stops the bot^)
:loop
.venv\Scripts\python.exe -m app.ws_main >> bot.log 2>&1
echo [%date% %time%] bot exited, restarting in 10s... >> bot.log
timeout /t 10 /nobreak > nul
goto loop
