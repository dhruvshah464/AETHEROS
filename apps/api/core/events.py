"""Realtime event engine — pub/sub backbone for AetherOS."""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine

import orjson
import structlog

logger = structlog.get_logger(__name__)


class EventChannel(str, Enum):
    SYSTEM = "system"
    TELEMETRY = "telemetry"
    AI = "ai"
    AGENT = "agent"
    VISION = "vision"
    VOICE = "voice"
    MEMORY = "memory"
    AUTOMATION = "automation"
    BROWSER = "browser"


class EventType(str, Enum):
    SYSTEM_CONNECTED = "system.connected"
    SYSTEM_HEARTBEAT = "system.heartbeat"
    SYSTEM_ERROR = "system.error"
    TELEMETRY_SNAPSHOT = "telemetry.snapshot"
    TELEMETRY_GPU = "telemetry.gpu"
    AI_STREAM_START = "ai.stream.start"
    AI_STREAM_TOKEN = "ai.stream.token"
    AI_STREAM_THOUGHT = "ai.stream.thought"
    AI_STREAM_END = "ai.stream.end"
    AI_COMMAND_QUEUED = "ai.command.queued"
    AI_COMMAND_COMPLETE = "ai.command.complete"
    AGENT_STATUS = "agent.status"
    AGENT_MESSAGE = "agent.message"
    AGENT_HANDOFF = "agent.handoff"
    AGENT_TASK_START = "agent.task.start"
    AGENT_TASK_PROGRESS = "agent.task.progress"
    AGENT_TASK_COMPLETE = "agent.task.complete"
    VISION_FRAME = "vision.frame"
    VISION_DETECTION = "vision.detection"
    VOICE_WAKE = "voice.wake"
    VOICE_TRANSCRIPT = "voice.transcript"
    VOICE_RESPONSE = "voice.response"
    MEMORY_STORE = "memory.store"
    MEMORY_RECALL = "memory.recall"
    AUTOMATION_ACTION = "automation.action"
    AUTOMATION_APPROVAL_REQUEST = "automation.approval.request"
    AUTOMATION_APPROVAL_GRANTED = "automation.approval.granted"
    BROWSER_NAVIGATION = "browser.navigation"
    BROWSER_SCREENSHOT = "browser.screenshot"
    BROWSER_ACTION = "browser.action"
    BROWSER_CURSOR = "browser.cursor"
    TERMINAL_OUTPUT = "terminal.output"
    TERMINAL_COMMAND = "terminal.command"
    WORKFLOW_START = "workflow.start"
    WORKFLOW_NODE_START = "workflow.node.start"
    WORKFLOW_NODE_COMPLETE = "workflow.node.complete"
    WORKFLOW_COMPLETE = "workflow.complete"
    VOICE_SPEAKING = "voice.speaking"
    VOICE_AUDIO = "voice.audio"
    VISION_SCENE = "vision.scene"
    VISION_OCR = "vision.ocr"
    SCREEN_CAPTURE = "screen.capture"
    DEMO_START = "demo.start"
    DEMO_STEP = "demo.step"
    DEMO_COMPLETE = "demo.complete"
    MODEL_STATUS = "model.status"


@dataclass
class AetherEvent:
    type: EventType
    channel: EventChannel
    payload: dict[str, Any]
    session_id: str = "global"
    metadata: dict[str, Any] | None = None
    id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(
        default_factory=lambda: datetime.now(timezone.utc).timestamp() * 1000
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "channel": self.channel.value,
            "timestamp": self.timestamp,
            "sessionId": self.session_id,
            "payload": self.payload,
            "metadata": self.metadata,
        }

    def to_json(self) -> bytes:
        return orjson.dumps(self.to_dict())


EventHandler = Callable[[AetherEvent], Coroutine[Any, Any, None]]


class EventEngine:
    """Central event bus with WebSocket fan-out and optional Redis pub/sub."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._connections: set[Any] = set()
        self._redis = None
        self._history: list[AetherEvent] = []
        self._max_history = 500

    async def connect_redis(self, url: str) -> bool:
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(url, decode_responses=True)
            await self._redis.ping()
            logger.info("redis_connected", url=url)
            return True
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e))
            self._redis = None
            return False

    def register_handler(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_channel(self, channel: EventChannel) -> asyncio.Queue:
        key = channel.value
        if key not in self._subscribers:
            self._subscribers[key] = set()
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._subscribers[key].add(queue)
        return queue

    def unsubscribe(self, channel: EventChannel, queue: asyncio.Queue) -> None:
        self._subscribers.get(channel.value, set()).discard(queue)

    async def publish(self, event: AetherEvent) -> None:
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        try:
            from core.event_store import event_store

            await event_store.append(event)
        except Exception:
            pass

        try:
            from core.observability import observability

            observability.record_event(event.channel.value, event.type.value)
        except Exception:
            pass

        # Channel subscribers
        for queue in self._subscribers.get(event.channel.value, set()):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

        # Type handlers
        for handler in self._handlers.get(event.type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error("handler_error", type=event.type.value, error=str(e))

        # WebSocket fan-out
        dead = set()
        for ws in self._connections:
            try:
                await ws.send_bytes(event.to_json())
            except Exception:
                dead.add(ws)
        self._connections -= dead

        # Redis pub/sub
        if self._redis:
            try:
                await self._redis.publish(
                    f"aetheros:{event.channel.value}",
                    event.to_json().decode(),
                )
            except Exception as e:
                logger.warning("redis_publish_failed", error=str(e))

    async def broadcast_to_ws(self, event: AetherEvent) -> None:
        """Publish only to WebSocket clients."""
        dead = set()
        for ws in self._connections:
            try:
                await ws.send_bytes(event.to_json())
            except Exception:
                dead.add(ws)
        self._connections -= dead

    def add_connection(self, ws: Any) -> None:
        self._connections.add(ws)

    def remove_connection(self, ws: Any) -> None:
        self._connections.discard(ws)

    def get_history(self, channel: EventChannel | None = None, limit: int = 50) -> list[dict]:
        events = self._history
        if channel:
            events = [e for e in events if e.channel == channel]
        return [e.to_dict() for e in events[-limit:]]


# Singleton
event_engine = EventEngine()
