"""Claude Monitor — Desktop floating mini window launcher.

Usage:
    python mini_window.py

Starts the backend server and opens a frameless, always-on-top
floating window showing the mini dashboard.
"""

import os
import sys
import time
import threading

# Ensure backend/ is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import uvicorn


def start_backend():
    """Run the FastAPI backend in a daemon thread."""
    os.chdir(os.path.join(os.path.dirname(__file__), "backend"))
    uvicorn.run("main:app", host="0.0.0.0", port=8765, log_level="warning")


def main():
    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait for backend to be ready
    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen("http://localhost:8765/api/processes", timeout=1)
            break
        except Exception:
            time.sleep(0.5)

    # Open floating window
    import webview

    screen = webview.screens[0] if webview.screens else None
    x = (screen.width - 310) if screen else 1620
    y = 16

    window = webview.create_window(
        title="Claude Monitor",
        url="http://localhost:8765/mini",
        width=300,
        height=240,
        frameless=True,
        on_top=True,
        x=x,
        y=y,
        easy_drag=True,
    )

    # Expose functions to JS
    def close_window():
        window.destroy()

    def open_detail(pid):
        import webbrowser
        webbrowser.open(f"http://localhost:8765/")

    window.expose(close_window, open_detail)

    print("[Claude Monitor] Mini window started")
    webview.start()
    print("[Claude Monitor] Window closed, exiting")


if __name__ == "__main__":
    main()
