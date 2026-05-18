"""Voice pipeline — Whisper STT + Edge TTS synthesis."""

from __future__ import annotations

import asyncio
import base64
import io
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import structlog

from core.config import get_settings
from core.events import AetherEvent, EventChannel, EventType, event_engine
from services.llm_router import llm_router

logger = structlog.get_logger(__name__)


class VoicePipeline:
    def __init__(self) -> None:
        self._whisper_model = None
        self._conversation: list[dict[str, str]] = []

    def _load_whisper(self):
        if self._whisper_model is None:
            try:
                import whisper
                settings = get_settings()
                self._whisper_model = whisper.load_model(settings.whisper_model)
                logger.info("whisper_loaded", model=settings.whisper_model)
            except Exception as e:
                logger.warning("whisper_unavailable", error=str(e))
        return self._whisper_model

    async def transcribe(self, audio_b64: str, format: str = "webm") -> dict[str, Any]:
        """Transcribe base64 audio using Whisper."""
        start = time.perf_counter()
        audio_bytes = base64.b64decode(audio_b64)

        await event_engine.publish(
            AetherEvent(
                type=EventType.VOICE_WAKE,
                channel=EventChannel.VOICE,
                payload={"status": "processing"},
            )
        )

        model = self._load_whisper()
        text = ""

        if model:
            suffix = f".{format}" if format else ".webm"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name
            try:
                result = await asyncio.to_thread(model.transcribe, tmp_path)
                text = result.get("text", "").strip()
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        else:
            text = "[Whisper unavailable — install openai-whisper]"

        latency = (time.perf_counter() - start) * 1000

        await event_engine.publish(
            AetherEvent(
                type=EventType.VOICE_TRANSCRIPT,
                channel=EventChannel.VOICE,
                payload={"text": text, "latencyMs": latency},
            )
        )

        return {"text": text, "latencyMs": latency}

    async def converse(self, audio_b64: str, format: str = "webm") -> dict[str, Any]:
        """Full voice turn: STT → LLM → TTS."""
        stt = await self.transcribe(audio_b64, format)
        user_text = stt["text"]
        if not user_text:
            return {"transcript": "", "response": "", "audio": None}

        self._conversation.append({"role": "user", "content": user_text})
        context = "\n".join(
            f"{m['role']}: {m['content']}" for m in self._conversation[-6:]
        )

        response_chunks: list[str] = []
        async for token in llm_router.stream(user_text, context=context):
            response_chunks.append(token)
            await event_engine.publish(
                AetherEvent(
                    type=EventType.AI_STREAM_TOKEN,
                    channel=EventChannel.AI,
                    payload={"token": token, "source": "voice"},
                )
            )

        response_text = "".join(response_chunks)
        self._conversation.append({"role": "assistant", "content": response_text})

        await event_engine.publish(
            AetherEvent(
                type=EventType.VOICE_RESPONSE,
                channel=EventChannel.VOICE,
                payload={"text": response_text},
            )
        )

        audio_b64_out = await self.synthesize(response_text)

        return {
            "transcript": user_text,
            "response": response_text,
            "audio": audio_b64_out,
            "latencyMs": stt.get("latencyMs", 0),
        }

    async def synthesize(self, text: str) -> str | None:
        """Synthesize speech via Edge TTS, return base64 MP3."""
        settings = get_settings()
        try:
            import edge_tts

            await event_engine.publish(
                AetherEvent(
                    type=EventType.VOICE_SPEAKING,
                    channel=EventChannel.VOICE,
                    payload={"status": "start", "text": text[:100]},
                )
            )

            communicate = edge_tts.Communicate(text, settings.tts_voice)
            audio_data = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])

            b64 = base64.b64encode(audio_data.getvalue()).decode()
            await event_engine.publish(
                AetherEvent(
                    type=EventType.VOICE_AUDIO,
                    channel=EventChannel.VOICE,
                    payload={"audio": b64, "format": "mp3"},
                )
            )
            await event_engine.publish(
                AetherEvent(
                    type=EventType.VOICE_SPEAKING,
                    channel=EventChannel.VOICE,
                    payload={"status": "end"},
                )
            )
            return b64
        except Exception as e:
            logger.error("tts_failed", error=str(e))
            return None

    def clear_conversation(self) -> None:
        self._conversation.clear()


voice_pipeline = VoicePipeline()
