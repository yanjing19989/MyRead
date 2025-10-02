from __future__ import annotations
import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import json

from ..utils.events import events

router = APIRouter(tags=["events"])


@router.get("/events/stream")
async def stream_events():
    q = events.subscribe()

    async def gen():
        try:
            while True:
                payload = await q.get()
                data = payload.get("data") if isinstance(payload, dict) else None
                if data is None:
                    data = payload
                yield {
                    "event": "message",
                    "data": json.dumps(data),
                }
        finally:
            events.unsubscribe(q)

    return EventSourceResponse(gen())
