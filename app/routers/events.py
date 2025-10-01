from __future__ import annotations
import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ..utils.events import events

router = APIRouter(tags=["events"])


@router.get("/events/stream")
async def stream_events():
    q = events.subscribe()

    async def gen():
        try:
            while True:
                payload = await q.get()
                yield {
                    "event": payload.get("event", "message"),
                    "data": payload.get("data"),
                }
        finally:
            events.unsubscribe(q)

    return EventSourceResponse(gen())
