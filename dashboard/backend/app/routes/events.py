"""Server-sent events for console state changes."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


class EventHub:
    """Small in-process broadcast hub; every subscriber gets its own queue."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, object]]] = set()
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[dict[str, object]]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(queue)
        try:
            yield queue
        finally:
            async with self._lock:
                self._subscribers.discard(queue)

    async def publish(self, event_type: str, **payload: object) -> None:
        event = {
            "type": event_type,
            "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat(),
            **payload,
        }
        async with self._lock:
            subscribers = tuple(self._subscribers)
        for queue in subscribers:
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(event)


hub = EventHub()


async def _stream(request: Request) -> AsyncIterator[str]:
    async with hub.subscribe() as queue:
        yield "event: connected\ndata: {\"schemaVersion\":2}\n\n"
        while not await request.is_disconnected():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue
            event_type = str(event.get("type", "message"))
            yield f"event: {event_type}\ndata: {json.dumps(event, separators=(',', ':'))}\n\n"


@router.get("/api/events", include_in_schema=True)
async def events(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
