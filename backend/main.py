"""FastAPI main entry point for Claude Monitor."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from log_reader import find_active_sessions, get_session_by_cwd
from scanner import ProcessScanner
from ws_manager import manager

# Global scanner
scanner = ProcessScanner()

# Background scan task
_scan_task: asyncio.Task | None = None


async def _scan_loop():
    """Background task that periodically scans for processes."""
    while True:
        try:
            processes, new_pids, gone_pids = scanner.scan()

            # Broadcast current state
            process_list = [p.to_dict() for p in processes]

            # Enrich with session info
            for proc_dict in process_list:
                if proc_dict.get("cwd"):
                    session = get_session_by_cwd(proc_dict["cwd"])
                    if session:
                        proc_dict["session_info"] = session.to_dict()

            await manager.broadcast("processes", {
                "processes": process_list,
                "new_pids": new_pids,
                "gone_pids": gone_pids,
            })

            # Send notifications for new/gone processes
            for pid in new_pids:
                cp = scanner.get_cached(pid)
                if cp:
                    await manager.broadcast("notification", {
                        "type": "process_started",
                        "pid": pid,
                        "project": cp.project_name,
                        "cwd": cp.cwd,
                    })

            for pid in gone_pids:
                await manager.broadcast("notification", {
                    "type": "process_exited",
                    "pid": pid,
                })

        except Exception as e:
            print(f"Scan error: {e}")

        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scan_task
    _scan_task = asyncio.create_task(_scan_loop())
    yield
    if _scan_task:
        _scan_task.cancel()


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
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


# --- REST API ---

@app.get("/api/processes")
async def get_processes():
    """Get current list of Claude processes."""
    processes, _, _ = scanner.scan()
    result = []
    for p in processes:
        d = p.to_dict()
        if p.cwd:
            session = get_session_by_cwd(p.cwd)
            if session:
                d["session_info"] = session.to_dict()
        result.append(d)
    return {"processes": result}


@app.get("/api/sessions")
async def get_sessions():
    """Get all active Claude sessions."""
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
        # Send initial state
        processes, _, _ = scanner.scan()
        process_list = [p.to_dict() for p in processes]
        for proc_dict in process_list:
            if proc_dict.get("cwd"):
                session = get_session_by_cwd(proc_dict["cwd"])
                if session:
                    proc_dict["session_info"] = session.to_dict()

        await manager.send_to(websocket, "initial", {
            "processes": process_list,
        })

        # Keep connection alive, receive client messages
        while True:
            data = await websocket.receive_text()
            # Handle client requests if needed
            msg = __import__("json").loads(data)
            if msg.get("type") == "get_session_logs":
                cwd = msg.get("cwd")
                if cwd:
                    session = get_session_by_cwd(cwd)
                    await manager.send_to(websocket, "session_logs", session.to_dict() if session else {})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)
