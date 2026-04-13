#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "================================"
echo "  Claude Monitor - Launcher"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "[ERROR] Python not found. Please install Python 3.10+."
    exit 1
fi
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)

# Check Node.js
if ! command -v npm &>/dev/null; then
    echo "[ERROR] npm not found. Please install Node.js 18+."
    exit 1
fi

# Install Python dependencies
echo "[1/4] Checking Python dependencies..."
cd "$SCRIPT_DIR/backend"
"$PYTHON_CMD" -m pip install -q -r requirements.txt
echo "      Done."
echo ""

# Install Node.js dependencies
echo "[2/4] Checking Node.js dependencies..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "      Installing npm packages..."
    npm install
else
    echo "      node_modules found, skipping."
fi
echo ""

cleanup() {
    echo ""
    echo "Stopping Claude Monitor..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
    wait 2>/dev/null
    echo "Stopped."
    exit 0
}
trap cleanup INT TERM

echo "[3/4] Starting backend server..."
cd "$SCRIPT_DIR/backend"
"$PYTHON_CMD" -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload &
BACKEND_PID=$!

sleep 2

echo "[4/4] Starting frontend dev server..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "================================"
echo "  Claude Monitor is starting!"
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:3000"
echo "================================"
echo ""
echo "Press Ctrl+C to stop."

wait
