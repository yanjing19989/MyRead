from __future__ import annotations
import asyncio
import json
from typing import Any, Dict, List, Set


class EventBus:
    def __init__(self) -> None:
        self._subs: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    def publish(self, event: str, data: Dict[str, Any]) -> None:
        payload = {"event": event, "data": data}
        for q in list(self._subs):
            try:
                q.put_nowait(payload)
            except Exception:
                pass


events = EventBus()
