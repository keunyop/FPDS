"""Bounded process-local reuse of already validated Public snapshot rows."""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from concurrent.futures import Future
from threading import RLock
from time import monotonic
from typing import Any, Callable


class PublicProjectionCache:
    def __init__(self, *, ttl_seconds: float = 60, max_entries: int = 64,
                 clock: Callable[[], float] = monotonic) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.clock = clock
        self._entries: OrderedDict[tuple, tuple[float, list[dict[str, Any]]]] = OrderedDict()
        self._lock = RLock()
        self._inflight: dict[tuple, Future] = {}

    def _get(self, key: tuple) -> list[dict[str, Any]] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        deadline, rows = entry
        if self.clock() >= deadline:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return deepcopy(rows)

    def get(self, key: tuple) -> list[dict[str, Any]] | None:
        with self._lock:
            return self._get(key)

    def load(self, key: tuple, loader: Callable[[], list[dict[str, Any]]]) -> list[dict[str, Any]]:
        # Coalesce misses for one key without blocking other countries or hits.
        with self._lock:
            cached = self._get(key)
            if cached is not None:
                return cached
            pending = self._inflight.get(key)
            owner = pending is None
            if owner:
                pending = self._inflight[key] = Future()
        if not owner:
            return deepcopy(pending.result())
        try:
            rows = loader()
            stored = deepcopy(rows)
            with self._lock:
                self._entries[key] = (self.clock() + self.ttl_seconds, stored)
                self._entries.move_to_end(key)
                while len(self._entries) > self.max_entries:
                    self._entries.popitem(last=False)
            pending.set_result(stored)
            return rows
        except BaseException as error:
            # Share the error with waiters; never serve expired rows or retain
            # a failed load. A later request may retry normally.
            pending.set_exception(error)
            raise
        finally:
            with self._lock:
                del self._inflight[key]


def connection_scope(connection: Any) -> tuple | None:
    """Separate databases and roles; never key by a credential or DB URL.

    Non-psycopg adapters without explicit connection identity bypass reuse.
    Only explicit read-only connections participate, so a writer cannot cache
    uncommitted results for another request. Connection options isolate schemas.
    """
    if getattr(connection, "read_only", False) is not True:
        return None
    info = getattr(connection, "info", None)
    if info is None:
        return None
    values = tuple(getattr(info, field, None) for field in ("host", "port", "dbname", "user", "options"))
    if not all(isinstance(value, (str, int)) for value in values):
        return None
    return values


projection_cache = PublicProjectionCache()
