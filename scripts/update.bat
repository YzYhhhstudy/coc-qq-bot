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
REM Kill only the bot's python (matched by command line), NOT other python processes
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*app.ws_main*'} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}"

REM The run_windows.bat guard loop auto-restarts the bot with NEW code within ~10s.
REM If the guard loop itself is not running, start it.
timeout /t 13 /nobreak > nul
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*app.ws_main*'}) { Write-Host 'OK: bot restarted with new code.' } else { Write-Host 'Guard loop not running, starting bot...'; Start-Process -FilePath 'scripts\run_windows.bat' }"

echo Done. Check bot.log or message the bot to verify.
pause
