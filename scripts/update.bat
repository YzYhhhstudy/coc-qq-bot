@echo off
REM One-click updater: pull latest code, install deps, restart the bot.
REM Safe to run while the bot is running.
cd /d %~dp0..

echo [1/3] Pulling latest code...
git pull
if errorlevel 1 (
    echo [ERROR] git pull failed. Check network or local changes.
    pause
    exit /b 1
)

echo [2/3] Installing dependencies (only if changed)...
.venv\Scripts\pip install -q -r requirements.txt

echo [3/3] Restarting bot...
REM Kill only the bot's python.exe (matched by command line). "$_.ProcessId -ne $PID" excludes
REM this PowerShell itself -- its own command line also contains "app.ws_main", and matching
REM itself used to make the "is the bot running?" check below always say yes.
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -like 'python*' -and $_.CommandLine -like '*app.ws_main*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

REM If run_windows.bat's guard loop is running, it restarts the bot within ~10s: wait up to 20s for it.
set /a tries=0
:waitloop
timeout /t 2 /nobreak > nul
set /a tries+=1
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -like 'python*' -and $_.CommandLine -like '*app.ws_main*' }) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo OK: bot restarted with new code.
    goto done
)
if %tries% lss 10 goto waitloop

REM Guard loop is not running (e.g. after a reboot): start it in its own window and keep that window open.
echo Guard loop not running, starting bot in a new window...
start "CoC QQ Bot" "%~dp0run_windows.bat"

:done
echo Done. Check bot.log or message the bot to verify.
pause
