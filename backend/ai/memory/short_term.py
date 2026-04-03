"""
short_term.py — In-session conversation memory.

Each session is a SessionState object keyed by session_id.
Thread-safe: all reads and writes use a per-session lock.
Sessions persist until explicitly cleared or the server restarts.
"""

import threading
import time
from typing import List, Dict


class SessionState:
    """Holds conversation history and control flags for one session."""

    def __init__(self):
        self._lock = threading.Lock()
        self._messages: List[Dict] = []
        self.cancel_requested: bool = False

    # --- Message operations ---

    def add_message(self, role: str, content: str) -> None:
        """Append a message. role must be 'user' or 'assistant'."""
        with self._lock:
            self._messages.append({
                "role": role,
                "content": content,
                "timestamp": int(time.time()),
            })

    def get_messages(self, max_count: int = None) -> List[Dict]:
        """Return a copy of messages. Optionally trim to last max_count."""
        with self._lock:
            msgs = list(self._messages)
        if max_count is not None and max_count > 0:
            msgs = msgs[-max_count:]
        return msgs

    def message_count(self) -> int:
        with self._lock:
            return len(self._messages)

    def clear_messages(self) -> None:
        with self._lock:
            self._messages = []

    # --- Cancel flag ---

    def request_cancel(self) -> None:
        with self._lock:
            self.cancel_requested = True

    def clear_cancel(self) -> None:
        with self._lock:
            self.cancel_requested = False

    def is_cancelled(self) -> bool:
        with self._lock:
            return self.cancel_requested

    # --- Full reset ---

    def reset(self) -> None:
        with self._lock:
            self._messages = []
            self.cancel_requested = False


# --- Module-level session store ---

_sessions: Dict[str, SessionState] = {}
_sessions_lock = threading.Lock()


def get_session(session_id: str) -> SessionState:
    """Return existing session or create a new one."""
    with _sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = SessionState()
        return _sessions[session_id]


def delete_session(session_id: str) -> None:
    """Remove a session entirely."""
    with _sessions_lock:
        _sessions.pop(session_id, None)


def get_all_sessions() -> Dict[str, SessionState]:
    """Return a snapshot of all active sessions."""
    with _sessions_lock:
        return dict(_sessions)
