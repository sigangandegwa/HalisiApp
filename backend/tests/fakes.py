"""In-memory stand-in for the supabase-py query builder (the subset SupabaseRepository uses).

Lets the SupabaseRepository run the same contract tests as the MemoryRepository without a network.
Rows are stored as JSON-like dicts, exactly as PostgREST would return them.
"""

import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

UNIQUE_KEYS: dict[str, tuple[str, ...]] = {"merchant_handles": ("platform", "handle")}


def _comparable(value: Any) -> Any:
    """Compare ISO timestamps as datetimes (like Postgres), everything else as-is."""
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value


@dataclass
class _Response:
    data: list[dict[str, Any]]


class _Query:
    def __init__(self, db: "FakeSupabase", table: str) -> None:
        self.db, self.table = db, table
        self.op = "select"
        self.payload: Any = None
        self.on_conflict: str | None = None
        self.filters: list[tuple[str, str, Any]] = []
        self.order_by: tuple[str, bool] | None = None
        self.limit_n: int | None = None
        self.columns = "*"

    # builders
    def select(self, columns: str = "*") -> "_Query":
        self.op, self.columns = "select", columns
        return self

    def insert(self, rows: Any) -> "_Query":
        self.op, self.payload = "insert", rows
        return self

    def upsert(self, rows: Any, on_conflict: str | None = None) -> "_Query":
        self.op, self.payload, self.on_conflict = "upsert", rows, on_conflict
        return self

    def update(self, values: dict[str, Any]) -> "_Query":
        self.op, self.payload = "update", values
        return self

    def delete(self) -> "_Query":
        self.op = "delete"
        return self

    def eq(self, col: str, val: Any) -> "_Query":
        self.filters.append(("eq", col, val))
        return self

    def gt(self, col: str, val: Any) -> "_Query":
        self.filters.append(("gt", col, val))
        return self

    def in_(self, col: str, vals: list[Any]) -> "_Query":
        self.filters.append(("in", col, list(vals)))
        return self

    def contains(self, col: str, vals: list[Any]) -> "_Query":
        self.filters.append(("contains", col, list(vals)))
        return self

    def is_(self, col: str, val: str) -> "_Query":
        self.filters.append(("is", col, val))
        return self

    def order(self, col: str, desc: bool = False) -> "_Query":
        self.order_by = (col, desc)
        return self

    def limit(self, n: int) -> "_Query":
        self.limit_n = n
        return self

    # execution
    def _match(self, row: dict[str, Any]) -> bool:
        for op, col, val in self.filters:
            cell = row.get(col)
            if op == "eq" and cell != val:
                return False
            if op == "gt" and not (cell is not None and _comparable(cell) > _comparable(val)):
                return False
            if op == "in" and cell not in val:
                return False
            if op == "contains" and not all(v in (cell or []) for v in val):
                return False
            if op == "is" and val == "null" and cell is not None:
                return False
        return True

    def execute(self) -> _Response:
        self.db.calls += 1
        rows = self.db.tables.setdefault(self.table, [])
        if self.op in ("insert", "upsert"):
            items = self.payload if isinstance(self.payload, list) else [self.payload]
            keys = tuple((self.on_conflict or "id").split(",")) if self.op == "upsert" else ("id",)
            out = []
            for item in items:
                item = copy.deepcopy(item)
                existing = next((r for r in rows if all(r.get(k) == item.get(k) for k in keys)), None)
                unique = UNIQUE_KEYS.get(self.table)
                if existing is None and unique:
                    existing = next((r for r in rows if all(r.get(k) == item.get(k) for k in unique)), None)
                if existing is not None and self.op == "upsert":
                    existing.update(item)
                    out.append(copy.deepcopy(existing))
                elif existing is not None:
                    raise RuntimeError(f"duplicate key in {self.table}")
                else:
                    rows.append(item)
                    out.append(copy.deepcopy(item))
            return _Response(out)
        matched = [r for r in rows if self._match(r)]
        if self.op == "update":
            for r in matched:
                r.update(copy.deepcopy(self.payload))
            return _Response(copy.deepcopy(matched))
        if self.op == "delete":
            self.db.tables[self.table] = [r for r in rows if r not in matched]
            return _Response(copy.deepcopy(matched))
        if self.order_by:
            col, desc = self.order_by
            matched = sorted(matched, key=lambda r: (r.get(col) is None, r.get(col)), reverse=desc)
        if self.limit_n is not None:
            matched = matched[: self.limit_n]
        return _Response(copy.deepcopy(matched))


class FakeSupabase:
    """``client.table(name)`` -> query builder over dict tables."""

    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self.calls = 0

    def table(self, name: str) -> _Query:
        return _Query(self, name)
