#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Try conda if available
if [ -f "$HOME/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/opt/anaconda3/etc/profile.d/conda.sh"
    if conda env list | grep -q "^dev "; then
        conda activate dev
    fi
fi

# Fallback to python3
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python not found. Please install Python 3.10+."
    exit 1
fi

# Install dependencies
echo "[1/2] Checking dependencies..."
cd "$SCRIPT_DIR/backend"
"$PYTHON_CMD" -m pip install -q -r requirements.txt 2>/dev/null
echo "      OK"

echo "[2/2] Starting mini window..."
cd "$SCRIPT_DIR"
"$PYTHON_CMD" mini_window.py "$@"
