@echo off
echo ====================================
echo   Claude Monitor - Build EXE
echo ====================================
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

:: 1. Install Python dependencies
echo [1/4] Installing Python dependencies...
cd /d %~dp0backend
pip install -q -r requirements.txt
pip install -q pyinstaller
echo       Done.

:: 2. Build frontend
echo [2/4] Building frontend...
cd /d %~dp0frontend
call npm install
call npm run build
if not exist dist\index.html (
    echo [ERROR] Frontend build failed.
    pause
    exit /b 1
)
echo       Done.

:: 3. Run PyInstaller
echo [3/4] Packaging into EXE...
cd /d %~dp0
python -m PyInstaller claude-monitor.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed.
    pause
    exit /b 1
)
echo       Done.

:: 4. Done
echo.
echo ====================================
echo   Build complete!
echo.
echo   Output: dist\Claude Monitor\
echo   Run:    dist\Claude Monitor\Claude Monitor.exe
echo ====================================
echo.

:: Open output folder
explorer "dist\Claude Monitor"

pause
