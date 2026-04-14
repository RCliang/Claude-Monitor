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
class SubagentInfo:
    agent_id: str
    slug: Optional[str] = None
    subagent_type: Optional[str] = None
    description: Optional[str] = None
    status: str = "running"  # "completed", "running", "error"
    message_count: int = 0
    total_tokens: Optional[int] = None
    total_duration_ms: Optional[int] = None
    total_tool_use_count: Optional[int] = None
    model: Optional[str] = None
    last_activity: Optional[str] = None
    current_activity: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "slug": self.slug,
            "subagent_type": self.subagent_type,
            "description": self.description,
            "status": self.status,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "total_duration_ms": self.total_duration_ms,
            "total_tool_use_count": self.total_tool_use_count,
            "model": self.model,
            "last_activity": self.last_activity,
            "current_activity": self.current_activity,
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
    subagents: list['SubagentInfo'] = field(default_factory=list)

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
            "subagents": [sa.to_dict() for sa in self.subagents],
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


def _parse_subagent_file(filepath: Path) -> Optional[SubagentInfo]:
    """Parse a subagent JSONL file and return summary info."""
    import time as _time

    mtime = filepath.stat().st_mtime
    # Skip old files
    if _time.time() - mtime > 86400:
        return None

    agent_name = filepath.stem  # e.g. "agent-ae959a1"
    agent_id = agent_name.replace("agent-", "")

    info = SubagentInfo(agent_id=agent_id)
    last_assistant_summary = None
    message_count = 0
    has_tool_result = False
    last_entry_type = None

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
                ts = entry.get("timestamp", "")
                message = entry.get("message", {})
                last_entry_type = entry_type

                # Extract slug
                if entry.get("slug") and not info.slug:
                    info.slug = entry["slug"]

                # Extract model
                if isinstance(message, dict) and message.get("model") and not info.model:
                    info.model = message["model"]

                # Extract description from first user message
                if entry_type == "user" and not info.description:
                    content = message.get("content", "") if isinstance(message, dict) else ""
                    if isinstance(content, str) and content and content != "Warmup":
                        info.description = _truncate(content, 120)

                # Count messages and track last activity
                if entry_type in ("user", "assistant"):
                    # Tool results (toolUseResult at top level)
                    if entry_type == "user" and entry.get("toolUseResult") is not None:
                        result = entry.get("toolUseResult", {})
                        has_tool_result = True
                        if isinstance(result, dict):
                            # Completion info from main session's Task result
                            if result.get("status") == "completed":
                                info.status = "completed"
                            if result.get("totalDurationMs"):
                                info.total_duration_ms = result["totalDurationMs"]
                            if result.get("totalTokens"):
                                info.total_tokens = result["totalTokens"]
                            if result.get("totalToolUseCount") is not None:
                                info.total_tool_use_count = result["totalToolUseCount"]
                        continue
                    if entry_type == "user" and entry.get("isMeta"):
                        continue

                    message_count += 1
                    if ts:
                        info.last_activity = ts

                    # Track last assistant activity for current_activity
                    if entry_type == "assistant" and isinstance(message, dict):
                        content = message.get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict):
                                    if c.get("type") == "tool_use":
                                        tool_name = c.get("name", "")
                                        if tool_name == "Task":
                                            continue
                                        tool_input = c.get("input", {})
                                        if isinstance(tool_input, dict):
                                            if "file_path" in tool_input:
                                                last_assistant_summary = f"{tool_name}: {tool_input['file_path']}"
                                            elif "command" in tool_input:
                                                last_assistant_summary = f"{tool_name}: {tool_input['command']}"
                                            else:
                                                last_assistant_summary = tool_name
                                        else:
                                            last_assistant_summary = tool_name
                                    elif c.get("type") == "text":
                                        text = c.get("text", "")
                                        if text:
                                            last_assistant_summary = _truncate(text, 80)
                                    elif c.get("type") == "thinking":
                                        thinking = c.get("thinking", "")
                                        if thinking:
                                            last_assistant_summary = f"Thinking: {_truncate(thinking, 60)}"

        info.message_count = message_count
        if last_assistant_summary:
            info.current_activity = last_assistant_summary

        # Determine status: if not explicitly completed, check last entry
        if info.status == "running":
            # If last entry is an assistant text response (not a tool call),
            # the subagent likely finished its work
            if last_entry_type == "assistant" and has_tool_result:
                info.status = "completed"

    except (OSError, UnicodeDecodeError):
        pass

    return info


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
    task_descriptions: dict[str, dict] = {}  # agent_id -> {description, subagent_type}
    task_results: dict[str, dict] = {}  # agent_id -> {status, totalDurationMs, totalTokens, totalToolUseCount}

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
                        # Extract Task completion info from main session
                        result = entry.get("toolUseResult", {})
                        if isinstance(result, dict) and result.get("agentId"):
                            aid = result["agentId"]
                            task_results[aid] = {
                                "status": result.get("status", "completed"),
                                "totalDurationMs": result.get("totalDurationMs"),
                                "totalTokens": result.get("totalTokens"),
                                "totalToolUseCount": result.get("totalToolUseCount"),
                            }
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

                    # Track Task tool calls to enrich subagent descriptions
                    if ctype == "tool_use" and tool_name == "Task":
                        message_raw = entry.get("message", {})
                        content_raw = message_raw.get("content", []) if isinstance(message_raw, dict) else []
                        if isinstance(content_raw, list):
                            for c in content_raw:
                                if isinstance(c, dict) and c.get("name") == "Task":
                                    inp = c.get("input", {})
                                    if isinstance(inp, dict):
                                        desc = inp.get("description", "")
                                        sa_type = inp.get("subagent_type", "")
                                        if desc:
                                            task_descriptions[desc] = {
                                                "description": desc,
                                                "subagent_type": sa_type,
                                            }
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

            # Load subagents from session subdirectory
            session_dir = filepath.parent / filepath.stem
            subagents_dir = session_dir / "subagents"
            if subagents_dir.exists():
                for sa_file in subagents_dir.glob("agent-*.jsonl"):
                    sa = _parse_subagent_file(sa_file)
                    if sa and sa.message_count > 0:
                        # Enrich with completion info from parent session's Task results
                        tr = task_results.get(sa.agent_id)
                        if tr:
                            if tr.get("status"):
                                sa.status = tr["status"]
                            if tr.get("totalDurationMs"):
                                sa.total_duration_ms = tr["totalDurationMs"]
                            if tr.get("totalTokens"):
                                sa.total_tokens = tr["totalTokens"]
                            if tr.get("totalToolUseCount") is not None:
                                sa.total_tool_use_count = tr["totalToolUseCount"]
                        # Enrich with description from parent session's Task calls
                        if not sa.description:
                            for td in task_descriptions.values():
                                sa.description = td["description"]
                                if td.get("subagent_type"):
                                    sa.subagent_type = td["subagent_type"]
                                break
                        session_info.subagents.append(sa)
                # Sort: running first, then by last_activity
                session_info.subagents.sort(
                    key=lambda s: (0 if s.status == "running" else 1, s.last_activity or ""),
                    reverse=True,
                )

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
