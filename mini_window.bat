@echo off
echo ================================
echo   Claude Monitor - Mini Window
echo ================================
echo.

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
cd /d %~dp0backend
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Launch mini window
cd /d %~dp0
python mini_window.py
