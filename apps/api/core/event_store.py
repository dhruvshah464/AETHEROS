"""Append-only event store for session replay and debugging."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import orjson
import structlog

from core.config import get_settings
from core.events import AetherEvent

logger = structlog.get_logger(__name__)


class EventStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._path: Path | None = None

    def _ensure_path(self) -> Path:
        if self._path is None:
            settings = get_settings()
            self._path = Path(settings.event_store_path)
            self._path.parent.mkdir(parents=True, exist_ok=True)
        return self._path

    async def append(self, event: AetherEvent) -> None:
        path = self._ensure_path()
        line = orjson.dumps(event.to_dict()) + b"\n"
        async with self._lock:
            with open(path, "ab") as f:
                f.write(line)

    async def replay(
        self,
        session_id: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        path = self._ensure_path()
        if not path.exists():
            return []

        events: list[dict[str, Any]] = []
        with open(path, "rb") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    evt = orjson.loads(line)
                    if session_id and evt.get("sessionId") != session_id:
                        continue
                    events.append(evt)
                except Exception:
                    continue

        return events[offset : offset + limit]

    async def timeline(self, limit: int = 100) -> list[dict[str, Any]]:
        path = self._ensure_path()
        if not path.exists():
            return []
        lines: list[bytes] = []
        with open(path, "rb") as f:
            lines = f.readlines()
        result = []
        for line in lines[-limit:]:
            try:
                result.append(orjson.loads(line))
            except Exception:
                pass
        return result


event_store = EventStore()
