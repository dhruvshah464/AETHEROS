from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from services.voice_pipeline import voice_pipeline

router = APIRouter(prefix="/voice", tags=["Voice"])


class TranscriptRequest(BaseModel):
    audio: str
    format: str = "webm"


class SpeakRequest(BaseModel):
    text: str


@router.post("/transcribe")
async def transcribe(req: TranscriptRequest):
    return await voice_pipeline.transcribe(req.audio, req.format)


@router.post("/converse")
async def converse(req: TranscriptRequest):
    return await voice_pipeline.converse(req.audio, req.format)


@router.post("/speak")
async def speak(req: SpeakRequest):
    audio = await voice_pipeline.synthesize(req.text)
    return {"audio": audio, "format": "mp3"}


@router.post("/clear")
async def clear():
    voice_pipeline.clear_conversation()
    return {"ok": True}
