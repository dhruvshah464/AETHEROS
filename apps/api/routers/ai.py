from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.events import AetherEvent, EventChannel, EventType, event_engine
from services.agents import agent_orchestrator
from services.llm_router import llm_router
from services.memory import memory_engine

router = APIRouter(prefix="/ai", tags=["AI"])


class CommandRequest(BaseModel):
    prompt: str
    context: str | None = None
    agent_id: str | None = None
    stream: bool = True
    use_agents: bool = True


class MemoryStoreRequest(BaseModel):
    content: str
    type: str = "episodic"
    metadata: dict | None = None


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 10


@router.post("/command")
async def execute_command(req: CommandRequest):
    await event_engine.publish(
        AetherEvent(
            type=EventType.AI_COMMAND_QUEUED,
            channel=EventChannel.AI,
            payload={"prompt": req.prompt},
        )
    )

    async def generate():
        await event_engine.publish(
            AetherEvent(
                type=EventType.AI_STREAM_START,
                channel=EventChannel.AI,
                payload={"prompt": req.prompt},
            )
        )

        idx = 0
        stream_fn = (
            agent_orchestrator.execute_task(req.prompt)
            if req.use_agents
            else llm_router.stream(req.prompt, req.context)
        )

        async for token in stream_fn:
            await event_engine.publish(
                AetherEvent(
                    type=EventType.AI_STREAM_TOKEN,
                    channel=EventChannel.AI,
                    payload={"token": token, "index": idx},
                )
            )
            yield f"data: {token}\n\n"
            idx += 1

        await event_engine.publish(
            AetherEvent(
                type=EventType.AI_STREAM_END,
                channel=EventChannel.AI,
                payload={"tokens": idx},
            )
        )
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/memory/store")
async def store_memory(req: MemoryStoreRequest):
    entry = await memory_engine.store(req.content, req.type, req.metadata)
    return entry


@router.post("/memory/search")
async def search_memory(req: MemorySearchRequest):
    results = await memory_engine.search(req.query, req.limit)
    return {"results": results}


@router.get("/memory/timeline")
async def memory_timeline(limit: int = 50):
    return {"entries": await memory_engine.get_timeline(limit)}


@router.get("/agents")
async def get_agents():
    return {"agents": await agent_orchestrator.get_network_state()}
