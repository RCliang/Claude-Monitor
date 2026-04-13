"""Read Claude Code session logs from ~/.claude/projects/."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class TodoItem:
    content: str
    status: str  # "in_progress", "pending", "completed"
    activeForm: str = ""

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "status": self.status,
            "activeForm": self.activeForm,
        }


@dataclass
class LogEntry:
    timestamp: str
    role: str  # "user", "assistant", "tool"
    content_type: str  # "text", "tool_use", "tool_result"
    summary: str
    tool_name: Optional[str] = None
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "role": self.role,
            "content_type": self.content_type,
            "summary": self.summary,
            "tool_name": self.tool_name,
            "detail": self.detail,
        }


@dataclass
class SessionInfo:
    session_id: str
    project_dir: str
    project_name: str
    cwd: Optional[str]
    version: Optional[str]
    start_time: Optional[str]
    last_activity: Optional[str]
    message_count: int = 0
    recent_logs: list[LogEntry] = field(default_factory=list)
    current_todos: list[TodoItem] = field(default_factory=list)
    current_activity: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "project_dir": self.project_dir,
            "project_name": self.project_name,
            "cwd": self.cwd,
            "version": self.version,
            "start_time": self.start_time,
            "last_activity": self.last_activity,
            "message_count": self.message_count,
            "recent_logs": [log.to_dict() for log in self.recent_logs],
            "current_todos": [t.to_dict() for t in self.current_todos],
            "current_activity": self.current_activity,
        }


def _get_claude_dir() -> Path:
    """Get the Claude config directory."""
    home = Path.home()
    return home / ".claude"


def _truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _extract_summary(msg: dict) -> tuple[str, str, Optional[str], Optional[str], Optional[str]]:
    """Extract (role, content_type, summary, tool_name, detail) from a message."""
    role = msg.get("type", "unknown")
    message = msg.get("message", {})
    msg_role = message.get("role", role)

    content = message.get("content", [])
    if isinstance(content, str):
        return msg_role, "text", _truncate(content), None, content

    if isinstance(content, list) and len(content) > 0:
        first = content[0]
        ctype = first.get("type", "text")

        if ctype == "thinking":
            thinking_text = first.get("thinking", "")
            return msg_role, "thinking", _truncate(thinking_text, 100), None, thinking_text
        elif ctype == "text":
            text = first.get("text", "")
            return msg_role, "text", _truncate(text), None, text if len(text) > 200 else None
        elif ctype == "tool_use":
            tool = first.get("name", "unknown")
            inp = first.get("input", {})
            detail = None
            if isinstance(inp, dict):
                if tool in ("Edit", "edit") and "file_path" in inp:
                    summary = f"{tool}: {inp['file_path']}"
                    parts = []
                    if inp.get("old_string"):
                        parts.append(f"--- old ---\n{inp['old_string']}")
                    if inp.get("new_string"):
                        parts.append(f"+++ new +++\n{inp['new_string']}")
                    if parts:
                        detail = "\n".join(parts)
                elif tool in ("Write", "write") and "file_path" in inp:
                    summary = f"{tool}: {inp['file_path']}"
                    if inp.get("content"):
                        detail = inp["content"]
                elif "command" in inp:
                    summary = f"{tool}: {inp['command']}"
                elif "pattern" in inp:
                    summary = f"{tool}: {inp['pattern']}"
                elif "file_path" in inp:
                    summary = f"{tool}: {inp['file_path']}"
                else:
                    summary = f"{tool}"
            else:
                summary = tool
            return msg_role, "tool_use", _truncate(summary), tool, detail
        elif ctype == "tool_result":
            content_text = first.get("content", "")
            if isinstance(content_text, str):
                return msg_role, "tool_result", _truncate(content_text[:100]), None, content_text if len(content_text) > 200 else None
            return msg_role, "tool_result", "tool result", None

    return msg_role, "text", _truncate(str(content)[:100]), None, None


def _parse_session_jsonl(filepath: Path, max_logs: int = 50) -> SessionInfo:
    """Parse a session JSONL file."""
    session_id = filepath.stem
    # Extract actual session_id from filename pattern: UUID-agent-UUID.jsonl
    parts = session_id.split("-agent-")
    if len(parts) >= 1:
        # The main session ID is the first UUID
        main_id = parts[0]

    project_dir = filepath.parent.name

    # Try to decode the project dir name back to a path
    project_name = project_dir

    session_info = SessionInfo(
        session_id=main_id if len(parts) > 1 else session_id,
        project_dir=project_dir,
        project_name=project_name,
        cwd=None,
        version=None,
        start_time=None,
        last_activity=None,
    )

    logs: list[LogEntry] = []
    message_count = 0
    current_todos: list[TodoItem] = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type", "")

                # Extract session metadata
                if entry.get("cwd") and not session_info.cwd:
                    session_info.cwd = entry.get("cwd")
                if entry.get("version") and not session_info.version:
                    session_info.version = entry.get("version")
                if entry.get("sessionId") and session_info.session_id == session_id:
                    session_info.session_id = entry["sessionId"]

                ts = entry.get("timestamp", "")

                if entry_type in ("user", "assistant"):
                    if entry_type == "user" and entry.get("isMeta"):
                        continue
                    if entry_type == "user" and entry.get("toolUseResult") is not None:
                        continue

                    message_count += 1
                    msg_role, ctype, summary, tool_name, detail = _extract_summary(entry)

                    # Track TodoWrite: overwrite with latest todo list
                    if ctype == "tool_use" and tool_name == "TodoWrite":
                        message = entry.get("message", {})
                        content = message.get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("name") == "TodoWrite":
                                    todos_input = c.get("input", {}).get("todos", [])
                                    current_todos = [
                                        TodoItem(
                                            content=t.get("content", ""),
                                            status=t.get("status", "pending"),
                                            activeForm=t.get("activeForm", ""),
                                        )
                                        for t in todos_input
                                        if isinstance(t, dict)
                                    ]
                                    break

                    # Update time tracking
                    if not session_info.start_time:
                        session_info.start_time = ts
                    session_info.last_activity = ts

                    logs.append(LogEntry(
                        timestamp=ts,
                        role=msg_role,
                        content_type=ctype,
                        summary=summary,
                        tool_name=tool_name,
                        detail=detail,
                    ))

            session_info.message_count = message_count
            session_info.recent_logs = logs[-max_logs:]
            session_info.current_todos = current_todos

            # Derive current activity from last non-result log
            for log in reversed(logs):
                if log.role == "assistant" and log.content_type != "tool_result":
                    if log.content_type == "tool_use":
                        session_info.current_activity = log.summary
                    elif log.content_type == "thinking":
                        session_info.current_activity = f"Thinking: {_truncate(log.summary, 60)}"
                    else:
                        session_info.current_activity = _truncate(log.summary, 80)
                    break

    except (OSError, UnicodeDecodeError):
        pass

    return session_info


def find_active_sessions(cwd_filter: Optional[str] = None) -> list[SessionInfo]:
    """Find all Claude sessions, optionally filtered by working directory.

    Scans ~/.claude/projects/ for JSONL files, sorted by modification time.
    """
    claude_dir = _get_claude_dir()
    projects_dir = claude_dir / "projects"

    if not projects_dir.exists():
        return []

    sessions: list[SessionInfo] = []

    for project_path in projects_dir.iterdir():
        if not project_path.is_dir():
            continue

        for jsonl_file in project_path.glob("*.jsonl"):
            try:
                # Only read recently modified files (last 24h) for performance
                mtime = jsonl_file.stat().st_mtime
                import time
                if time.time() - mtime > 86400:  # 24 hours
                    continue

                session = _parse_session_jsonl(jsonl_file, max_logs=30)

                # Filter by cwd if specified
                if cwd_filter and session.cwd:
                    if cwd_filter.lower() not in session.cwd.lower():
                        continue

                if session.message_count > 0:
                    sessions.append(session)
            except (OSError, PermissionError):
                continue

    # Sort by last activity
    sessions.sort(key=lambda s: s.last_activity or "", reverse=True)
    return sessions


def get_session_by_cwd(cwd: str) -> Optional[SessionInfo]:
    """Find the most recent session for a given working directory."""
    sessions = find_active_sessions(cwd_filter=cwd)
    return sessions[0] if sessions else None
