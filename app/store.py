"""Read-only access to Delta tables via delta-rs (no Spark in the request path)."""
import threading
import time

from deltalake import DeltaTable

from app.config import settings


class DeltaStore:
    def __init__(self, base: str | None = None, refresh_seconds: float | None = None):
        self.base = (base or settings.delta_base_path).rstrip("/")
        self.refresh = settings.delta_refresh_seconds if refresh_seconds is None else refresh_seconds
        self._tables: dict[str, DeltaTable] = {}
        self._checked: dict[str, float] = {}
        self._lock = threading.Lock()

    def _table(self, name: str) -> DeltaTable:
        with self._lock:
            now = time.monotonic()
            dt = self._tables.get(name)
            if dt is None:
                dt = DeltaTable(f"{self.base}/{name}")
                self._tables[name] = dt
                self._checked[name] = now
            elif now - self._checked[name] > self.refresh:
                dt.update_incremental()  # picks up new commits from Spark jobs
                self._checked[name] = now
            return dt

    def read(self, name: str, filters: list[tuple] | None = None) -> list[dict]:
        dt = self._table(name)
        return dt.to_pyarrow_table(filters=filters).to_pylist()


_store: DeltaStore | None = None


def get_store() -> DeltaStore:
    global _store
    if _store is None:
        _store = DeltaStore()
    return _store
