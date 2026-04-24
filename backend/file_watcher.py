"""File watcher for Claude Code session log changes using watchdog."""

import asyncio
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from watchdog.observers import Observer


class ClaudeProjectHandler(FileSystemEventHandler):
    """Handles filesystem events for .jsonl files under ~/.claude/projects/."""

    def __init__(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue):
        self._loop = loop
        self._queue = queue

    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith('.jsonl'):
            return
        self._loop.call_soon_threadsafe(
            self._queue.put_nowait, ("log_changed", Path(event.src_path))
        )

    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith('.jsonl'):
            return
        self._loop.call_soon_threadsafe(
            self._queue.put_nowait, ("log_created", Path(event.src_path))
        )


class FileWatcherService:
    """Manages the watchdog Observer for Claude session files."""

    def __init__(self):
        self._observer: Optional[Observer] = None
        self._queue: asyncio.Queue = asyncio.Queue()

    def start(self, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
        """Start watching ~/.claude/projects/ recursively. Returns the event queue."""
        claude_dir = Path.home() / ".claude" / "projects"

        if not claude_dir.exists():
            print(f"[FileWatcher] Warning: {claude_dir} does not exist. File watcher disabled.")
            return self._queue

        handler = ClaudeProjectHandler(loop, self._queue)
        self._observer = Observer()
        self._observer.schedule(handler, str(claude_dir), recursive=True)
        self._observer.daemon = True
        self._observer.start()
        print(f"[FileWatcher] Started watching {claude_dir}")
        return self._queue

    def stop(self):
        """Stop the file watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            print("[FileWatcher] Stopped")
