from typing import Any, Optional
import time

class TTLCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self.cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            item = self.cache[key]
            if time.time() < item['expires_at']:
                return item['value']
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + self.ttl
        }

    def clear(self):
        self.cache = {}

result_cache = TTLCache(ttl_seconds=600)
