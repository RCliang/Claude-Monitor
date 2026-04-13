# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Monitor is a real-time process monitoring dashboard for Claude Code CLI processes. It detects running Claude Code instances via `psutil`, enriches them with session log data from `~/.claude/projects/`, and displays everything through a retro NES/CRT pixel-art themed web UI. The UI is Chinese-language localized.

## Development Commands

### Start the full application (Windows)
```bat
start.bat
```
Launches both backend (port 8765) and frontend dev server (port 3000) in separate terminals.

### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload
```
No tests, no linter configured. Backend is pure Python with no build step.

### Frontend (Vue 3 + TypeScript)
```bash
cd frontend
npm install
npm run dev       # Dev server on :3000 with API proxy to backend :8765
npm run build     # Production build to frontend/dist/
```
No tests, no linter configured. Type-check with `npx vue-tsc --noEmit`.

## Architecture

Two-process architecture: Python FastAPI backend + Vue 3 SPA frontend. Communication via WebSocket (real-time) and REST API (initial fetch).

### Backend (`backend/`)

- **`main.py`** — FastAPI app with REST endpoints (`/api/processes`, `/api/sessions`) and WebSocket (`/ws`). Runs a background `_scan_loop` every 3 seconds that broadcasts process updates to all connected clients.
- **`scanner.py`** — `ProcessScanner` class. Uses `psutil` to find Claude Code processes by matching command-line patterns (`@anthropic-ai/claude-code`, `claude-code\cli`, `claude`). Filters out child processes (bash, cmd). Tracks process state changes (new/gone PIDs).
- **`log_reader.py`** — Parses `~/.claude/projects/*/UUID.jsonl` session log files. Extracts `SessionInfo` including recent logs, current activity, todos, message counts. Only reads files modified within 24 hours.
- **`ws_manager.py`** — WebSocket connection manager with `broadcast` and `send_to` methods.
- **`console_writer.py`** — Windows-specific console input writer (not used in web UI flow).

Data flow per scan cycle: `scanner.scan()` → enrich each process with `get_session_by_cwd()` → broadcast via WebSocket as `{type: "processes", data: {processes, new_pids, gone_pids}}`.

### Frontend (`frontend/src/`)

- **`App.vue`** — Root layout: header + Dashboard + (ProcessList | ProcessDetail) flex row. Defines CSS custom properties for dark/light themes.
- **`composables/useWebSocket.ts`** — Single shared WebSocket connection (`ref` outside composable = singleton). Manages `processes` and `notifications` reactive state. Auto-reconnects on disconnect.
- **`composables/useTheme.ts`** — Dark/light theme toggle.
- **`components/ProcessList.vue`** — Left sidebar (300px fixed). Shows process items with PixelAvatar, PID, status badge, project name, CPU/mem. Has blinking indicators: green for running, blue for waiting-for-input.
- **`components/ProcessDetail.vue`** — Right panel. Shows header (avatar, PID, status, TOOLKIT dropdown), status/activity section, session info bar, recent logs with expandable detail.
- **`components/PixelAvatar.vue`** — 8x8 pixel identicon canvas based on PID seed.
- **`components/Dashboard.vue`** — Top stats bar (running/idle/total counts).
- **`components/NotificationPanel.vue`** — Dropdown for process start/exit notifications.

### Vite Proxy

In dev mode, Vite proxies `/api` and `/ws` to `localhost:8765` (see `vite.config.ts`). In production, the backend serves `frontend/dist/assets/` directly via FastAPI `StaticFiles`.

## Design System

The full design specification is in `design-rules.md`. Key constraints when modifying UI:

- **No border-radius anywhere** — all elements are sharp rectangles
- **No SVG icons** — use Unicode/ASCII symbols only (`▶`, `■`, `◆`, `◇`, `▼`, `│`)
- **Pixel fonts**: `--font-pixel` (Press Start 2P) for labels/badges, `--font-body` (Silkscreen) for body text
- **Transitions**: always `step-end` timing, never smooth easing
- **Shadows**: flat offset only (`Npx Npx 0px`), no blur
- **CRT scanline overlay** on dark theme via fixed `repeating-linear-gradient`
- **Anti-aliasing off**: `-webkit-font-smoothing: none`
- **Status indicators**: 8x8 squares, not circles. Green (`--success`) = running, blue (`--info`) = waiting input, yellow (`--warning`) = idle
