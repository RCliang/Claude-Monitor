# Claude Monitor

A retro NES/CRT pixel-art style real-time monitoring dashboard for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI processes.

## Features

- **Real-time process monitoring** — Detects running Claude Code instances via `psutil`, updates every 3 seconds via WebSocket
- **Session log integration** — Reads `~/.claude/projects/` session logs to show recent activity, todos, and current task
- **Status indicators** — Green blinking indicator when Claude is working, blue blinking when waiting for user input
- **Toolkit viewer** — Browse available Skills and MCP tools in a two-column dropdown
- **Dark/Light theme** — Toggle between CRT dark mode and light mode, with scanline overlay effect
- **Cross-platform** — Works on Windows and Linux

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Vue 3 + TypeScript + Vite)           │
│  Port 3000 (dev)                                │
├─────────────────────────────────────────────────┤
│  WebSocket / REST API                           │
├─────────────────────────────────────────────────┤
│  Backend (Python FastAPI)                       │
│  Port 8765                                      │
│  ├── scanner.py    — Process detection (psutil) │
│  ├── log_reader.py — Session log parsing        │
│  └── ws_manager.py — WebSocket broadcast        │
└─────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Windows

```bat
start.bat
```

### Linux

```bash
chmod +x start.sh
./start.sh
```

### Manual Start

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Production Build

```bash
cd frontend && npm run build && cd ../backend
python -m uvicorn main:app --host 0.0.0.0 --port 8765
```

The backend serves the built frontend from `frontend/dist/`.

## Configuration

No configuration file required. The app auto-detects Claude Code processes and reads session logs from the default `~/.claude/projects/` directory.

## Design

The UI follows a retro NES/CRT pixel-art aesthetic with sharp edges (no border-radius), flat offset shadows, neon glow effects, and a scanline overlay. See [design-rules.md](design-rules.md) for the full design specification.

## License

MIT
