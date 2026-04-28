"""Claude Monitor - Desktop floating mini window via pywebview.

Usage:
    python mini_window.py
    python mini_window.py 9000
"""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class Api:
    """Bridge between pywebview JS and Python."""

    def close_window(self):
        import webview
        webview.destroy()

    def open_detail(self, pid):
        webbrowser.open(f"http://localhost:{PORT}/")


def _start_server():
    os.chdir(str(BACKEND))
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="warning")


def _wait_for_server(port, timeout=15):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/api/processes", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    print("=" * 40)
    print("  Claude Monitor - Mini Window")
    print("=" * 40)
    print("")

    sys.path.insert(0, str(BACKEND))

    server = threading.Thread(target=_start_server, daemon=True)
    server.start()

    print(f"Waiting for backend on port {PORT}...")
    if not _wait_for_server(PORT):
        print("[ERROR] Backend failed to start.")
        sys.exit(1)
    print("Backend ready.")

    import webview

    api = Api()
    webview.create_window(
        "Claude Monitor",
        f"http://localhost:{PORT}/mini",
        width=320,
        height=420,
        x=100,
        y=50,
        on_top=True,
        frameless=False,
        easy_drag=True,
        js_api=api,
        min_size=(280, 200),
    )
    webview.start()


if __name__ == "__main__":
    main()
