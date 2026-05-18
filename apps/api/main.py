"""AetherOS API Gateway — FastAPI + WebSocket realtime event backbone."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import orjson
import structlog

from core.config import get_settings
from core.events import AetherEvent, EventChannel, EventType, event_engine
from core.logging import setup_logging
from routers import (
    ai,
    auth,
    browser,
    demo,
    diagnostics,
    memory_v3,
    models,
    plugins,
    screen,
    society,
    studio,
    system,
    terminal,
    vision,
    voice,
    workflow,
)
from core.event_store import event_store
from core.observability import observability
from plugins.registry import plugin_registry
from services.memory import memory_engine
from services.telemetry import telemetry_service

setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("aetheros_starting", version="0.1.0")

    await event_engine.connect_redis(settings.redis_url)
    await memory_engine.initialize()
    plugin_registry.discover()
    await telemetry_service.start()

    await event_engine.publish(
        AetherEvent(
            type=EventType.SYSTEM_CONNECTED,
            channel=EventChannel.SYSTEM,
            payload={"message": "AetherOS online", "version": "0.1.0"},
        )
    )

    yield

    await telemetry_service.stop()
    logger.info("aetheros_shutdown")


app = FastAPI(
    title="AetherOS API",
    description="Cinematic AI Operating System — Realtime Gateway",
    version="0.3.0",
    lifespan=lifespan,
    default_response_class=None,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai.router)
app.include_router(system.router)
app.include_router(vision.router)
app.include_router(browser.router)
app.include_router(terminal.router)
app.include_router(workflow.router)
app.include_router(voice.router)
app.include_router(models.router)
app.include_router(screen.router)
app.include_router(demo.router)
app.include_router(plugins.router)
app.include_router(auth.router)
app.include_router(diagnostics.router)
app.include_router(memory_v3.router)
app.include_router(society.router)
app.include_router(studio.router)


@app.get("/")
async def root():
    return {
        "system": "AetherOS",
        "status": "online",
        "docs": "/docs",
        "websocket": "/ws",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    event_engine.add_connection(websocket)
    observability.ws_connected()
    session_id = f"session_{id(websocket)}"

    await websocket.send_bytes(
        orjson.dumps(
            {
                "type": "system.connected",
                "channel": "system",
                "payload": {
                    "message": "WebSocket connected to AetherOS Event Engine",
                    "sessionId": session_id,
                },
            }
        )
    )

    # Send recent history
    history = event_engine.get_history(limit=20)
    await websocket.send_bytes(
        orjson.dumps({"type": "history", "events": history})
    )

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "ping":
                await websocket.send_bytes(
                    orjson.dumps({"type": "pong", "timestamp": data.get("timestamp")})
                )

            elif action == "command":
                cmd = data.get("command", {})
                prompt = cmd.get("prompt", "")
                if prompt:
                    from services.agents import agent_orchestrator

                    await event_engine.publish(
                        AetherEvent(
                            type=EventType.AI_COMMAND_QUEUED,
                            channel=EventChannel.AI,
                            payload={"prompt": prompt},
                            session_id=session_id,
                        )
                    )
                    idx = 0
                    async for token in agent_orchestrator.execute_task(prompt, session_id):
                        await websocket.send_bytes(
                            orjson.dumps(
                                {
                                    "type": "ai.stream.token",
                                    "channel": "ai",
                                    "payload": {"token": token, "index": idx},
                                }
                            )
                        )
                        idx += 1
                    await websocket.send_bytes(
                        orjson.dumps(
                            {
                                "type": "ai.stream.end",
                                "channel": "ai",
                                "payload": {"tokens": idx},
                            }
                        )
                    )

    except WebSocketDisconnect:
        event_engine.remove_connection(websocket)
        observability.ws_disconnected()
        logger.info("websocket_disconnected", session=session_id)
    except Exception as e:
        event_engine.remove_connection(websocket)
        observability.ws_disconnected()
        logger.error("websocket_error", error=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=True)
