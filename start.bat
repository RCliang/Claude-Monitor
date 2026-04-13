@echo off
echo ================================
echo   Claude Monitor - Launcher
echo ================================
echo.

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

:: Check Node.js
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm not found. Please install Node.js 18+ and add to PATH.
    pause
    exit /b 1
)

:: Install Python dependencies
echo [1/4] Checking Python dependencies...
cd /d %~dp0backend
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo       Done.
echo.

:: Install Node.js dependencies
echo [2/4] Checking Node.js dependencies...
cd /d %~dp0frontend
if not exist node_modules (
    echo       Installing npm packages...
    call npm install
) else (
    echo       node_modules found, skipping.
)
echo.

:: Start backend
echo [3/4] Starting backend server...
start "Claude Monitor Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload"

timeout /t 2 /nobreak >nul

:: Start frontend
echo [4/4] Starting frontend dev server...
start "Claude Monitor Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ================================
echo   Claude Monitor is starting!
echo   Backend:  http://localhost:8765
echo   Frontend: http://localhost:3000
echo ================================
echo.
echo Close both terminal windows to stop.
