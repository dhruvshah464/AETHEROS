from fastapi import APIRouter
from pydantic import BaseModel

from services.demo_engine import demo_engine

router = APIRouter(prefix="/demo", tags=["Demo"])


class StartDemoRequest(BaseModel):
    sequence: str = "full_mission"


@router.get("/sequences")
async def sequences():
    return {"sequences": demo_engine.list_sequences()}


@router.post("/start")
async def start(req: StartDemoRequest):
    return await demo_engine.start(req.sequence)


@router.post("/stop")
async def stop():
    await demo_engine.stop()
    return {"ok": True}


@router.get("/status")
async def status():
    return {"running": demo_engine.is_running}
