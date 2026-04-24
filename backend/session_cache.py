"""Session cache to avoid redundant JSONL parsing."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from log_reader import SessionInfo, _parse_session_jsonl, find_active_sessions


@dataclass
class CachedSession:
    """Cached parse result for a single JSONL file."""
    session_info: SessionInfo
    file_size: int
    last_modified: float  # st_mtime
    parsed_at: datetime = field(default_factory=datetime.now)


class SessionCache:
    """Cache for parsed session JSONL files, keyed by filepath string."""

    def __init__(self):
        self._cache: dict[str, CachedSession] = {}

    def get_or_parse(self, filepath: Path) -> SessionInfo:
        """Get session info, re-parsing only if the file has changed."""
        key = str(filepath)

        if not filepath.exists():
            self._cache.pop(key, None)
            # Return a minimal placeholder
            return SessionInfo(
                session_id=filepath.stem,
                project_dir=filepath.parent.name,
                project_name=filepath.parent.name,
                cwd=None,
                version=None,
                start_time=None,
                last_activity=None,
            )

        try:
            stat = filepath.stat()
        except OSError:
            self._cache.pop(key, None)
            return SessionInfo(
                session_id=filepath.stem,
                project_dir=filepath.parent.name,
                project_name=filepath.parent.name,
                cwd=None,
                version=None,
                start_time=None,
                last_activity=None,
            )

        current_size = stat.st_size
        current_mtime = stat.st_mtime

        cached = self._cache.get(key)

        # Return cached if file unchanged
        if cached and cached.file_size == current_size and cached.last_modified == current_mtime:
            return cached.session_info

        # File changed or new — full re-parse
        try:
            session_info = _parse_session_jsonl(filepath)
        except Exception:
            self._cache.pop(key, None)
            raise

        self._cache[key] = CachedSession(
            session_info=session_info,
            file_size=current_size,
            last_modified=current_mtime,
            parsed_at=datetime.now(),
        )
        return session_info

    def get_by_cwd(self, cwd: str) -> Optional[SessionInfo]:
        """Find cached session matching a cwd."""
        if not cwd:
            return None
        cwd_lower = cwd.lower()
        best: Optional[SessionInfo] = None
        best_activity = ""
        for cached in self._cache.values():
            si = cached.session_info
            if si.cwd and cwd_lower in si.cwd.lower():
                if si.last_activity and si.last_activity > best_activity:
                    best = si
                    best_activity = si.last_activity
        return best

    def get_all_sessions(self) -> list[SessionInfo]:
        """Return all cached sessions sorted by last activity."""
        sessions = [c.session_info for c in self._cache.values() if c.session_info.message_count > 0]
        sessions.sort(key=lambda s: s.last_activity or "", reverse=True)
        return sessions

    def invalidate(self, filepath: Path):
        """Remove a file from cache."""
        self._cache.pop(str(filepath), None)

    def invalidate_stale(self, max_age_hours: int = 24):
        """Remove cache entries for files not modified recently."""
        now = time.time()
        stale_keys = [
            k for k, v in self._cache.items()
            if now - v.last_modified > max_age_hours * 3600
        ]
        for k in stale_keys:
            del self._cache[k]

    def populate_from_disk(self):
        """Initial population: scan all active sessions into the cache."""
        sessions = find_active_sessions()
        # find_active_sessions returns parsed SessionInfo but not keyed by filepath.
        # We need to re-discover the files. We'll do a lightweight scan.
        claude_dir = Path.home() / ".claude" / "projects"
        if not claude_dir.exists():
            return
        for project_path in claude_dir.iterdir():
            if not project_path.is_dir():
                continue
            for jsonl_file in project_path.glob("*.jsonl"):
                try:
                    stat = jsonl_file.stat()
                    if time.time() - stat.st_mtime > 86400:
                        continue
                    # Parse and cache
                    key = str(jsonl_file)
                    if key not in self._cache:
                        session_info = _parse_session_jsonl(jsonl_file)
                        self._cache[key] = CachedSession(
                            session_info=session_info,
                            file_size=stat.st_size,
                            last_modified=stat.st_mtime,
                        )
                except (OSError, PermissionError):
                    continue
        print(f"[SessionCache] Populated with {len(self._cache)} sessions")
