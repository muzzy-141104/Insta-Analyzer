import os
import json
import time
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional
from cryptography.fernet import Fernet

logger = logging.getLogger("session_manager")

# Optional encryption config via env vars
KEY_FILE = os.getenv("SESSION_KEY_FILE", "session_key.key")
USE_ENCRYPTION = os.getenv("ENCRYPT_SESSIONS", "0") == "1"


def _get_fernet() -> Optional[Fernet]:
    """Return a Fernet instance if encryption enabled, else None.
    NOTE: If key file does not exist, this will create it locally.
    Operator must secure KEY_FILE manually and avoid committing it to git."""
    if not USE_ENCRYPTION:
        return None
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as kf:
            kf.write(key)
        os.chmod(KEY_FILE, 0o600)
        logger.info(f"Created new session encryption key at {KEY_FILE}. Keep it safe!")
    else:
        with open(KEY_FILE, "rb") as kf:
            key = kf.read()
    return Fernet(key)


@dataclass
class SessionData:
    sessionid: str
    username: Optional[str] = None
    created_at: float = time.time()
    last_used: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    is_active: bool = True

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return SessionData(
            sessionid=d.get("sessionid"),
            username=d.get("username"),
            created_at=d.get("created_at", 0.0),
            last_used=d.get("last_used", 0.0),
            success_count=d.get("success_count", 0),
            failure_count=d.get("failure_count", 0),
            is_active=d.get("is_active", True),
        )


class SessionManager:
    def __init__(self, sessions_file: str = "sessions.json"):
        self.sessions_file = sessions_file
        self.sessions: List[SessionData] = []
        self._load_sessions()

    def _load_sessions(self):
        """Load stored sessions. If encryption enabled, decrypt the file."""
        if not os.path.exists(self.sessions_file):
            logger.debug("No sessions file found; starting with empty pool.")
            self.sessions = []
            return

        try:
            fernet = _get_fernet()
            with open(self.sessions_file, "rb") as f:
                raw = f.read()
            if fernet:
                raw = fernet.decrypt(raw)
            data = json.loads(raw.decode("utf-8"))
            self.sessions = [SessionData.from_dict(s) for s in data]
            logger.debug(f"Loaded {len(self.sessions)} sessions from {self.sessions_file}")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            self.sessions = []

    def _save_sessions_atomic(self):
        """Save sessions atomically. If encryption enabled, encrypt payload."""
        try:
            data = [s.to_dict() for s in self.sessions]
            payload = json.dumps(data, indent=2).encode("utf-8")
            fernet = _get_fernet()
            if fernet:
                payload = fernet.encrypt(payload)
            tmp_path = self.sessions_file + ".tmp"
            with open(tmp_path, "wb") as f:
                f.write(payload)
            os.replace(tmp_path, self.sessions_file)
            logger.debug(f"Saved {len(self.sessions)} sessions to {self.sessions_file}")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def add_session(self, sessionid: str, username: Optional[str] = None):
        """Add a new session to the pool (no duplicates)."""
        for s in self.sessions:
            if s.sessionid == sessionid:
                logger.warning("Session already present; skipping add.")
                return
        new_session = SessionData(sessionid=sessionid, username=username, created_at=time.time())
        self.sessions.append(new_session)
        self._save_sessions_atomic()
        logger.info(f"Added new session for {username or 'unknown'}")

    def get_next_session(self) -> Optional[SessionData]:
        """Rotate and return the next best session (persist last_used immediately)."""
        active_sessions = [s for s in self.sessions if s.is_active]
        if not active_sessions:
            logger.error("No active sessions available")
            return None
        # Sort by (failure_count asc, last_used asc) to prefer low-failure and least-recently-used
        active_sessions.sort(key=lambda s: (s.failure_count, s.last_used))
        session = active_sessions[0]
        session.last_used = time.time()
        logger.debug(f"Selected session for {session.username or 'unknown'} (failures: {session.failure_count})")
        self._save_sessions_atomic()
        return session

    def mark_session_success(self, sessionid: str):
        """Mark a session as successful and persist."""
        for s in self.sessions:
            if s.sessionid == sessionid:
                s.success_count += 1
                s.failure_count = max(0, s.failure_count - 1)
                s.is_active = True
                logger.debug(f"Marked session success for {s.username or 'unknown'}")
                break
        self._save_sessions_atomic()

    def mark_session_failure(self, sessionid: str):
        """Mark a session failure; deactivate after threshold and persist."""
        for s in self.sessions:
            if s.sessionid == sessionid:
                s.failure_count += 1
                if s.failure_count >= 5:
                    s.is_active = False
                    logger.warning(f"Deactivated session for {s.username or 'unknown'} due to repeated failures")
                else:
                    logger.warning(f"Marked session failure ({s.failure_count}/5) for {s.username or 'unknown'}")
                break
        self._save_sessions_atomic()

    def reactivate_session(self, sessionid: str):
        """Operator can reactivate a session (resets failure count)."""
        for s in self.sessions:
            if s.sessionid == sessionid:
                s.failure_count = 0
                s.is_active = True
                logger.info(f"Reactivated session for {s.username or 'unknown'}")
                break
        self._save_sessions_atomic()

    def get_session_stats(self) -> dict:
        """Return basic session stats for reporting."""
        active = sum(1 for s in self.sessions if s.is_active)
        total_success = sum(s.success_count for s in self.sessions)
        total_failures = sum(s.failure_count for s in self.sessions)
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active,
            "total_successes": total_success,
            "total_failures": total_failures,
            "sessions": [s.to_dict() for s in self.sessions],
        }
