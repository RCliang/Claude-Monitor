"""Scan system for running Claude Code CLI processes."""

import asyncio
import platform
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import psutil


@dataclass
class ClaudeProcess:
    pid: int
    name: str
    cmdline: list[str]
    cwd: Optional[str]
    create_time: datetime
    cpu_percent: float
    memory_mb: float
    status: str  # "running", "idle", "exited"
    session_id: Optional[str] = None
    project_name: Optional[str] = None
    last_seen: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "name": self.name,
            "cmdline": self.cmdline,
            "cwd": self.cwd,
            "create_time": self.create_time.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_mb": round(self.memory_mb, 1),
            "status": self.status,
            "session_id": self.session_id,
            "project_name": self.project_name,
            "last_seen": self.last_seen.isoformat(),
        }


# Precise patterns that identify Claude Code CLI (not just any process with "claude" in path)
CLAUDE_CLI_PATTERNS = [
    "@anthropic-ai/claude-code",
    "claude-code\\cli",
    "claude-code/cli",
    "\\claude.exe",
    "/claude",
]

# These are child processes spawned BY Claude Code, not Claude Code itself
EXCLUDED_PROCESS_NAMES = {"bash", "bash.exe", "sh", "sh.exe", "cmd", "cmd.exe", "powershell", "powershell.exe"}

# CWD patterns to exclude (not real Claude Code CLI sessions)
EXCLUDED_CWD_PATTERNS = ["trae", "Trae"]


def _is_claude_process(proc: psutil.Process) -> bool:
    """Check if a process is a Claude Code CLI instance (not a child shell)."""
    try:
        name = proc.name().lower()
        # Skip known shell/child processes
        if name in EXCLUDED_PROCESS_NAMES:
            return False

        cmdline = " ".join(proc.cmdline()).lower()
        for pattern in CLAUDE_CLI_PATTERNS:
            if pattern.lower() in cmdline:
                # Exclude processes from specific directories (e.g. Trae CN)
                try:
                    cwd = (proc.cwd() or "").lower()
                    for exc in EXCLUDED_CWD_PATTERNS:
                        if exc.lower() in cwd:
                            return False
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                return True
        # Direct claude executable (not node wrapper)
        if name in ("claude", "claude.exe"):
            return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


def _extract_session_id(cmdline: list[str]) -> Optional[str]:
    """Try to extract session ID from command line args."""
    for arg in cmdline:
        # Session IDs are UUIDs
        if len(arg) == 36 and arg.count("-") == 4:
            return arg
    return None


def _extract_project_from_cwd(cwd: Optional[str]) -> Optional[str]:
    """Extract a readable project name from the working directory."""
    if not cwd:
        return None
    # Use the last directory component as project name
    parts = cwd.replace("\\", "/").rstrip("/").split("/")
    return parts[-1] if parts else None


class ProcessScanner:
    """Scans system for Claude Code processes."""

    def __init__(self):
        self._previous_pids: set[int] = set()
        self._process_cache: dict[int, ClaudeProcess] = {}

    def scan(self) -> tuple[list[ClaudeProcess], list[int], list[int]]:
        """Scan for Claude processes.

        Returns:
            (current_processes, new_pids, gone_pids)
        """
        current_pids: set[int] = set()
        processes: list[ClaudeProcess] = []

        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
            if _is_claude_process(proc):
                try:
                    pid = proc.pid
                    current_pids.add(pid)

                    try:
                        cwd = proc.cwd()
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        cwd = None

                    try:
                        cpu = proc.cpu_percent(interval=None)
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        cpu = 0.0

                    try:
                        mem = proc.memory_info().rss / (1024 * 1024)
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        mem = 0.0

                    try:
                        cmdline = proc.cmdline()
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        cmdline = []

                    status = "running" if cpu > 0.5 else "idle"

                    cp = ClaudeProcess(
                        pid=pid,
                        name=proc.name(),
                        cmdline=cmdline,
                        cwd=cwd,
                        create_time=datetime.fromtimestamp(proc.create_time()),
                        cpu_percent=cpu,
                        memory_mb=mem,
                        status=status,
                        session_id=_extract_session_id(cmdline),
                        project_name=_extract_project_from_cwd(cwd),
                        last_seen=datetime.now(),
                    )
                    processes.append(cp)
                    self._process_cache[pid] = cp
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        # Detect new and gone PIDs
        new_pids = current_pids - self._previous_pids
        gone_pids = self._previous_pids - current_pids

        # Clean up cache for gone processes
        for pid in gone_pids:
            self._process_cache.pop(pid, None)

        self._previous_pids = current_pids
        return processes, list(new_pids), list(gone_pids)

    def get_cached(self, pid: int) -> Optional[ClaudeProcess]:
        return self._process_cache.get(pid)
