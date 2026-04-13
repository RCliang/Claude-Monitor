#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

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

echo "Starting Claude Monitor..."
echo ""

echo "[1/2] Starting backend server..."
(cd "$SCRIPT_DIR/backend" && python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload) &
BACKEND_PID=$!

sleep 2

echo "[2/2] Starting frontend dev server..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "Claude Monitor is starting!"
echo "Backend:  http://localhost:8765"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop."

wait
