from fastapi import APIRouter

from core.event_store import event_store
from core.events import event_engine, EventChannel
from services.telemetry import collect_snapshot, telemetry_service

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health():
    return {
        "status": "operational",
        "system": "AetherOS",
        "version": "0.1.0",
        "subsystems": {
            "event_engine": True,
            "telemetry": telemetry_service._running,
            "websocket_connections": len(event_engine._connections),
        },
    }


@router.get("/telemetry")
async def get_telemetry():
    return collect_snapshot()


@router.get("/events/history")
async def event_history(channel: str | None = None, limit: int = 50):
    ch = EventChannel(channel) if channel else None
    return {"events": event_engine.get_history(ch, limit)}


@router.get("/events/timeline")
async def event_timeline(limit: int = 100):
    return {"events": await event_store.timeline(limit)}


@router.get("/events/replay")
async def event_replay(session_id: str | None = None, limit: int = 200, offset: int = 0):
    return {"events": await event_store.replay(session_id, limit, offset)}
