"""Claude Monitor - One-click launcher.

Usage:
    python run.py          # Start on port 8765
    python run.py 9000     # Start on port 9000
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


def _run(cmd, **kw):
    return subprocess.run(cmd, shell=True, **kw)


def check_python():
    print("[1/4] Checking Python dependencies...")
    _run(f'"{sys.executable}" -m pip install -q -r "{BACKEND / "requirements.txt"}"', check=True)
    print("      OK")


def check_node():
    print("[2/4] Checking Node.js dependencies...")
    if not (FRONTEND / "node_modules").exists():
        print("      Installing npm packages...")
        _run(f'cd /d "{FRONTEND}" && npm install' if os.name == "nt" else f'cd "{FRONTEND}" && npm install', check=True)
    else:
        print("      OK")


def build_frontend():
    print("[3/4] Building frontend...")
    _run(f'cd /d "{FRONTEND}" && npm run build' if os.name == "nt" else f'cd "{FRONTEND}" && npm run build', check=True)
    print("      OK")


def start_server():
    print(f"[4/4] Starting server on http://localhost:{PORT}")
    print("")
    print("=" * 40)
    print(f"  Claude Monitor")
    print(f"  http://localhost:{PORT}")
    print("=" * 40)
    print("")

    # Open browser
    import webbrowser
    webbrowser.open(f"http://localhost:{PORT}")

    os.chdir(str(BACKEND))
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", str(PORT),
    ])


def main():
    print("=" * 40)
    print("  Claude Monitor - Launcher")
    print("=" * 40)
    print("")

    try:
        check_python()
        check_node()
        build_frontend()
        start_server()
    except KeyboardInterrupt:
        print("\nStopped.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
