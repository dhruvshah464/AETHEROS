from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.agent_society import agent_society

router = APIRouter(prefix="/society", tags=["Agent Society"])


class SocietyRequest(BaseModel):
    prompt: str


@router.get("/state")
async def state():
    return agent_society.get_society_state()


@router.post("/execute")
async def execute(req: SocietyRequest):
    async def generate():
        async for token in agent_society.execute_collaborative(req.prompt):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
