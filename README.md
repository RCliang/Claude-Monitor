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

### One-Click Start

```bash
python run.py
```

This will automatically install dependencies, build the frontend, start the server, and open the browser. Everything runs on a single port (default `8765`).

To use a custom port:

```bash
python run.py 9000
```

### Dev Mode (Separate Processes)

If you need hot-reload for frontend development:

```bash
# Windows
start.bat

# Linux
chmod +x start.sh
./start.sh
```

This starts backend (`:8765`) and frontend dev server (`:3000`) in separate terminals with live reload.

## Configuration

No configuration file required. The app auto-detects Claude Code processes and reads session logs from the default `~/.claude/projects/` directory.

## Design

The UI follows a retro NES/CRT pixel-art aesthetic with sharp edges (no border-radius), flat offset shadows, neon glow effects, and a scanline overlay. See [design-rules.md](design-rules.md) for the full design specification.

## License

MIT
