from fastapi import APIRouter
from pydantic import BaseModel

from services.memory_graph import memory_graph

router = APIRouter(prefix="/memory/v3", tags=["Memory V3"])


class GraphStoreRequest(BaseModel):
    content: str
    type: str = "episodic"
    agent_id: str | None = None
    link_to: str | None = None
    relation: str = "related"


@router.post("/store")
async def store(req: GraphStoreRequest):
    return await memory_graph.store(req.content, req.type, req.agent_id, req.link_to, req.relation)


@router.get("/graph")
async def full_graph():
    return memory_graph.get_full_graph()


@router.get("/search")
async def search(q: str, limit: int = 20):
    return await memory_graph.search_graph(q, limit)


@router.get("/timeline")
async def timeline(limit: int = 50):
    return {"entries": memory_graph.timeline(limit)}


@router.post("/compress")
async def compress():
    removed = memory_graph.compress_old_memories()
    return {"removed": removed}
