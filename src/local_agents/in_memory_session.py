from __future__ import annotations

from typing import Any

from agents.items import TResponseInputItem
from agents.memory import Session


class InMemorySession(Session):
    """In-memory implementation of the Agents Session protocol.

    This session keeps only the last ``max_items`` conversation items in memory.
    It is intended for simple, non-persistent runtimes (e.g. CLI tools) where
    you want a small sliding window of history without any external storage.
    """

    def __init__(self, session_id: str, max_items: int = 4) -> None:
        self.session_id = session_id
        self._max_items = max_items
        self._items: list[TResponseInputItem] = []

    @property
    def max_items(self) -> int:
        """Maximum number of items kept in memory for this session."""

        return self._max_items

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        """Return up to ``limit`` of the most recent items, capped by ``max_items``.

        Items are always returned in chronological order (oldest first), as
        required by the Session protocol.
        """

        if not self._items:
            return []

        # Effective limit cannot exceed the configured max_items
        effective_limit: int | None
        if limit is None:
            effective_limit = self._max_items
        else:
            effective_limit = min(limit, self._max_items)

        if effective_limit >= len(self._items):
            return list(self._items)

        return self._items[-effective_limit:]

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        """Append new items and trim history to keep only the last ``max_items``."""

        if not items:
            return

        self._items.extend(items)
        if len(self._items) > self._max_items:
            self._items = self._items[-self._max_items :]

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item in the session, if any."""

        if not self._items:
            return None

        return self._items.pop()

    async def clear_session(self) -> None:
        """Clear all stored items for this session."""

        self._items.clear()
