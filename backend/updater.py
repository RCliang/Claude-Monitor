"""Hybrid update coordinator: file watcher + process scanner."""

import asyncio
from pathlib import Path
from typing import Optional

from file_watcher import FileWatcherService
from log_reader import get_session_by_cwd
from scanner import ProcessScanner, ClaudeProcess
from session_cache import SessionCache
from ws_manager import manager


class DashboardUpdater:
    """Coordinates file watching and process scanning to push real-time updates."""

    PROCESS_SCAN_INTERVAL = 10       # seconds between psutil scans
    DEBOUNCE_SECONDS = 0.5           # debounce window for file changes
    STALE_CACHE_CLEANUP_INTERVAL = 300  # 5 minutes

    def __init__(self, scanner: ProcessScanner, cache: SessionCache, file_watcher: FileWatcherService):
        self._scanner = scanner
        self._cache = cache
        self._file_watcher = file_watcher
        self._current_processes: list[ClaudeProcess] = []
        self._event_queue: Optional[asyncio.Queue] = None
        self._debounce_timers: dict[str, asyncio.TimerHandle] = {}
        self._tasks: list[asyncio.Task] = []
        # State tracking for notifications
        self._prev_activity_state: dict[int, str] = {}       # pid -> activity_state
        self._prev_subagent_status: dict[str, str] = {}      # "pid:agent_id" -> status

    async def start(self):
        """Start all update loops."""
        loop = asyncio.get_running_loop()
        self._event_queue = self._file_watcher.start(loop)

        # Pre-populate cache from existing session files
        loop.run_in_executor(None, self._cache.populate_from_disk)

        self._tasks = [
            asyncio.create_task(self._process_scan_loop()),
            asyncio.create_task(self._file_event_consumer()),
            asyncio.create_task(self._stale_cache_cleanup_loop()),
        ]
        print("[DashboardUpdater] Started")

    async def stop(self):
        """Stop all update loops and the file watcher."""
        for task in self._tasks:
            task.cancel()
        # Wait for cancellation
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        # Cancel debounce timers
        for timer in self._debounce_timers.values():
            timer.cancel()
        self._debounce_timers.clear()
        self._file_watcher.stop()
        print("[DashboardUpdater] Stopped")

    async def _process_scan_loop(self):
        """Poll for process changes every PROCESS_SCAN_INTERVAL seconds."""
        while True:
            try:
                processes, new_pids, gone_pids = self._scanner.scan()
                self._current_processes = processes

                if new_pids or gone_pids:
                    await self._broadcast_full_update(new_pids, gone_pids)
                else:
                    # Periodic stats update (CPU/mem) using cached sessions
                    await self._broadcast_stats_update()

                # Check for state-change notifications
                await self._check_state_change_notifications()

            except Exception as e:
                print(f"[DashboardUpdater] Process scan error: {e}")

            await asyncio.sleep(self.PROCESS_SCAN_INTERVAL)

    async def _check_state_change_notifications(self):
        """Detect activity_state and subagent status transitions, send notifications."""
        for proc in self._current_processes:
            session = self._cache.get_by_cwd(proc.cwd) if proc.cwd else None
            if not session:
                continue

            # --- user_input_required notification ---
            current_state = session.activity_state
            prev_state = self._prev_activity_state.get(proc.pid, "")
            self._prev_activity_state[proc.pid] = current_state or ""

            # Detect transition TO waiting state
            if current_state == "waiting" and prev_state != "waiting" and prev_state != "":
                await manager.broadcast("notification", {
                    "type": "user_input_required",
                    "pid": proc.pid,
                    "project": proc.project_name,
                    "cwd": proc.cwd,
                })

            # --- subagent_completed notification ---
            for sa in session.subagents:
                sa_key = f"{proc.pid}:{sa.agent_id}"
                current_sa_status = sa.status
                prev_sa_status = self._prev_subagent_status.get(sa_key, "")
                self._prev_subagent_status[sa_key] = current_sa_status

                if current_sa_status == "completed" and prev_sa_status == "running":
                    await manager.broadcast("notification", {
                        "type": "subagent_completed",
                        "pid": proc.pid,
                        "project": proc.project_name,
                        "cwd": proc.cwd,
                        "agent_id": sa.agent_id,
                        "description": sa.description or sa.slug or sa.agent_id,
                    })

    async def _file_event_consumer(self):
        """Consume file change events from the watchdog queue."""
        while True:
            try:
                event_type, filepath = await self._event_queue.get()
                self._debounce_file_update(event_type, filepath)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[DashboardUpdater] File event error: {e}")

    def _debounce_file_update(self, event_type: str, filepath: Path):
        """Set/reset a debounce timer for a file change."""
        key = str(filepath)
        # Cancel existing timer for this file
        if key in self._debounce_timers:
            self._debounce_timers[key].cancel()

        loop = asyncio.get_running_loop()
        timer = loop.call_later(
            self.DEBOUNCE_SECONDS,
            lambda: asyncio.ensure_future(
                self._handle_file_change(event_type, filepath)
            )
        )
        self._debounce_timers[key] = timer

    async def _handle_file_change(self, event_type: str, filepath: Path):
        """Handle a debounced file change: re-parse and broadcast."""
        key = str(filepath)
        self._debounce_timers.pop(key, None)

        try:
            # Resolve subagent files to their parent session
            session_filepath = self._resolve_session_file(filepath)

            # Re-parse the session file via cache
            session_info = self._cache.get_or_parse(session_filepath)

            # For new files, trigger an immediate process scan
            if event_type == "log_created":
                await self._trigger_immediate_scan()

            # Broadcast an update with enriched session data
            await self._broadcast_session_update(session_filepath)

            # Check for state-change notifications after file change
            await self._check_state_change_notifications()

        except Exception as e:
            print(f"[DashboardUpdater] File change handler error ({filepath}): {e}")
            self._cache.invalidate(filepath)

    def _resolve_session_file(self, filepath: Path) -> Path:
        """If filepath is a subagent file, return the parent session JSONL."""
        # Subagent files are at: .../project-dir/session-uuid/subagents/agent-*.jsonl
        # Parent session is:      .../project-dir/session-uuid.jsonl
        parts = filepath.parts
        if "subagents" in parts:
            # Find the index of "subagents" and go up two levels
            idx = parts.index("subagents")
            if idx >= 2:
                parent_dir = Path(*parts[:idx - 1])
                session_id = parts[idx - 1]
                parent_file = parent_dir / f"{session_id}.jsonl"
                if parent_file.exists():
                    return parent_file
        return filepath

    async def _trigger_immediate_scan(self):
        """Trigger an immediate process scan (for new sessions)."""
        try:
            processes, new_pids, gone_pids = self._scanner.scan()
            self._current_processes = processes
            if new_pids or gone_pids:
                await self._broadcast_full_update(new_pids, gone_pids)
        except Exception as e:
            print(f"[DashboardUpdater] Immediate scan error: {e}")

    async def _broadcast_full_update(self, new_pids: list[int], gone_pids: list[int]):
        """Broadcast full process list with session enrichment."""
        process_list = self._build_enriched_process_list()

        await manager.broadcast("processes", {
            "processes": process_list,
            "new_pids": new_pids,
            "gone_pids": gone_pids,
        })

        # Notifications for new processes
        for pid in new_pids:
            cp = self._scanner.get_cached(pid)
            if cp:
                await manager.broadcast("notification", {
                    "type": "process_started",
                    "pid": pid,
                    "project": cp.project_name,
                    "cwd": cp.cwd,
                })

        # Notifications for gone processes
        for pid in gone_pids:
            await manager.broadcast("notification", {
                "type": "process_exited",
                "pid": pid,
            })

        # Clean up state tracking for gone processes
        for pid in gone_pids:
            self._prev_activity_state.pop(pid, None)
            keys_to_remove = [k for k in self._prev_subagent_status if k.startswith(f"{pid}:")]
            for k in keys_to_remove:
                del self._prev_subagent_status[k]

    async def _broadcast_stats_update(self):
        """Lightweight update: refresh process stats using cached sessions."""
        if not self._current_processes:
            return

        process_list = self._build_enriched_process_list()
        await manager.broadcast("processes", {
            "processes": process_list,
            "new_pids": [],
            "gone_pids": [],
        })

    async def _broadcast_session_update(self, session_filepath: Path):
        """Broadcast after a specific session file changed."""
        process_list = self._build_enriched_process_list()
        await manager.broadcast("processes", {
            "processes": process_list,
            "new_pids": [],
            "gone_pids": [],
        })

    def _build_enriched_process_list(self) -> list[dict]:
        """Build the enriched process list for broadcast."""
        process_list = [p.to_dict() for p in self._current_processes]
        for proc_dict in process_list:
            cwd = proc_dict.get("cwd")
            if cwd:
                session = self._cache.get_by_cwd(cwd)
                if session:
                    proc_dict["session_info"] = session.to_dict()
                else:
                    # Cache miss — try direct read as fallback
                    session = get_session_by_cwd(cwd)
                    if session:
                        proc_dict["session_info"] = session.to_dict()
        return process_list

    def get_current_state(self) -> list[dict]:
        """Get current enriched process list (for REST API and WebSocket initial state)."""
        return self._build_enriched_process_list()

    async def _stale_cache_cleanup_loop(self):
        """Periodically clean stale cache entries."""
        while True:
            await asyncio.sleep(self.STALE_CACHE_CLEANUP_INTERVAL)
            try:
                self._cache.invalidate_stale()
            except Exception as e:
                print(f"[DashboardUpdater] Cache cleanup error: {e}")
