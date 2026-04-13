@echo off
echo Starting Claude Monitor...
echo.

echo [1/2] Starting backend server...
start "Claude Monitor Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting frontend dev server...
start "Claude Monitor Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Claude Monitor is starting!
echo Backend:  http://localhost:8765
echo Frontend: http://localhost:3000
echo.
echo Close both terminal windows to stop.
