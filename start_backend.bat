@echo off
title SueLotto Backend
cd /d "%~dp0"
echo ====================================
    SueLotto Backend
echo ====================================

:: Kill existing process on port 8000 (using PowerShell)
powershell -NoProfile -Command ^
    "$p = netstat -ano | Select-String ':8000' | Select-String LISTENING; ^
     if ($p) { $pid = $p.Line.Trim().Split()[-1]; Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue; ^
               Write-Host 'Killed PID' $pid; Start-Sleep -Seconds 1 }"

:: Start uvicorn (foreground - keeps window open)
echo Starting uvicorn on http://0.0.0.0:8000 ...
echo NOTE: Auto-update runs at startup - first health check may take ~2 min
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

echo.
echo [ERROR] Backend stopped unexpectedly (code %ERRORLEVEL%).
pause
