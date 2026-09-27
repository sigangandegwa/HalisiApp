"""Tiny in-process TTL cache (fetched target profiles, 10 minutes by default)."""

import time
from collections import OrderedDict
from collections.abc import Callable


class TTLCache[V]:
    """LRU-bounded dict with per-entry expiry. Not shared between processes."""

    def __init__(
        self, ttl_seconds: float = 600, max_items: int = 1024, clock: Callable[[], float] = time.monotonic
    ):
        self.ttl = ttl_seconds
        self.max_items = max_items
        self._clock = clock
        self._items: OrderedDict[str, tuple[float, V]] = OrderedDict()

    def get(self, key: str) -> V | None:
        """Value for ``key`` if present and not expired."""
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self._clock() >= expires_at:
            del self._items[key]
            return None
        self._items.move_to_end(key)
        return value

    def set(self, key: str, value: V) -> None:
        """Store ``value`` for ``ttl`` seconds, evicting the least recently used entry when full."""
        self._items[key] = (self._clock() + self.ttl, value)
        self._items.move_to_end(key)
        while len(self._items) > self.max_items:
            self._items.popitem(last=False)

    def clear(self) -> None:
        """Drop everything."""
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)
