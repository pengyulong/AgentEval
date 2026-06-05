from abc import ABC, abstractmethod
from pathlib import Path
import time

from agenteval.trace.schema import SessionTrace


class BaseAdapter(ABC):
    @abstractmethod
    def load_session(self, session_ref: str | Path, include_raw: bool = False) -> SessionTrace:
        raise NotImplementedError

    def discover_sessions(
        self,
        scope: str,
        path: str | Path | None = None,
        since: str | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        return []

    def _filter_sessions(self, sessions: list[Path], since: str | None, limit: int | None) -> list[Path]:
        filtered = sessions
        if since:
            threshold = time.time() - self._since_seconds(since)
            filtered = [session for session in filtered if session.stat().st_mtime >= threshold]
        return filtered[:limit] if limit else filtered

    def _since_seconds(self, since: str) -> int:
        unit = since[-1]
        amount = int(since[:-1]) if unit.isalpha() else int(since)
        multipliers = {"m": 60, "h": 3600, "d": 86400}
        return amount * multipliers.get(unit, 1)
