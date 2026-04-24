"""FastAPI main entry point for Claude Monitor."""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from file_watcher import FileWatcherService
from log_reader import find_active_sessions, get_session_by_cwd
from scanner import ProcessScanner
from session_cache import SessionCache
from updater import DashboardUpdater
from ws_manager import manager

# Global components
scanner = ProcessScanner()
cache = SessionCache()
file_watcher = FileWatcherService()
updater = DashboardUpdater(scanner, cache, file_watcher)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await updater.start()
    yield
    await updater.stop()


app = FastAPI(title="Claude Monitor", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from starlette.responses import FileResponse

    @app.get("/")
    async def serve_index():
        return FileResponse(str(frontend_dist / "index.html"))


# --- REST API ---

@app.get("/mini", response_class=HTMLResponse)
async def mini_page():
    """Self-contained mini dashboard for desktop floating window."""
    from mini_page import get_mini_html
    return get_mini_html()


@app.get("/api/processes")
async def get_processes():
    """Get current list of Claude processes."""
    # Use updater's current state (enriched with cached sessions)
    process_list = updater.get_current_state()
    return {"processes": process_list}


@app.get("/api/sessions")
async def get_sessions():
    """Get all active Claude sessions."""
    # Try cache first, fall back to full scan
    cached = cache.get_all_sessions()
    if cached:
        return {"sessions": [s.to_dict() for s in cached]}
    sessions = find_active_sessions()
    return {"sessions": [s.to_dict() for s in sessions]}


@app.get("/api/sessions/{project_dir}")
async def get_project_sessions(project_dir: str):
    """Get sessions for a specific project directory."""
    sessions = find_active_sessions(cwd_filter=project_dir)
    return {"sessions": [s.to_dict() for s in sessions]}


# --- WebSocket ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state using updater's current state
        process_list = updater.get_current_state()

        await manager.send_to(websocket, "initial", {
            "processes": process_list,
        })

        # Keep connection alive, receive client messages
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "get_session_logs":
                cwd = msg.get("cwd")
                if cwd:
                    session = cache.get_by_cwd(cwd) or get_session_by_cwd(cwd)
                    await manager.send_to(websocket, "session_logs", session.to_dict() if session else {})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)


# --- Static file catch-all (must be after API/WebSocket routes) ---
if frontend_dist.exists():
    @app.get("/{filename:path}")
    async def serve_static(filename: str):
        file = frontend_dist / filename
        if file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(frontend_dist / "index.html"))

    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
