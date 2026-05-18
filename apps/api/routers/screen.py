from fastapi import APIRouter
from pydantic import BaseModel

from services.screen_intel import screen_intel

router = APIRouter(prefix="/screen", tags=["Screen"])


class AnalyzeRequest(BaseModel):
    question: str | None = None


@router.post("/capture")
async def capture():
    return await screen_intel.capture_screen()


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    return await screen_intel.analyze_screen(req.question)
