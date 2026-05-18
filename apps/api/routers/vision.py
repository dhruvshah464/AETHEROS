from fastapi import APIRouter
from pydantic import BaseModel

from services.vision import vision_service

router = APIRouter(prefix="/vision", tags=["Vision"])


class FrameRequest(BaseModel):
    frame: str  # base64 encoded image


@router.post("/detect")
async def detect_objects(req: FrameRequest):
    detections = await vision_service.process_frame(req.frame)
    return {"detections": detections}
