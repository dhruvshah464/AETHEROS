"""Screen capture + OCR + multimodal scene understanding."""

from __future__ import annotations

import asyncio
import base64
import io
import time
from typing import Any

import structlog

from core.events import AetherEvent, EventChannel, EventType, event_engine
from services.llm_router import llm_router

logger = structlog.get_logger(__name__)


class ScreenIntel:
    async def capture_screen(self) -> dict[str, Any]:
        """Capture primary monitor screenshot."""
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitor = sct.monitors[1]
                shot = sct.grab(monitor)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                b64 = base64.b64encode(buf.getvalue()).decode()

            ocr_text = await self._ocr_image(buf.getvalue())

            payload = {
                "screenshot": b64,
                "width": shot.width,
                "height": shot.height,
                "ocr": ocr_text,
            }

            await event_engine.publish(
                AetherEvent(
                    type=EventType.SCREEN_CAPTURE,
                    channel=EventChannel.VISION,
                    payload=payload,
                )
            )
            return payload
        except ImportError:
            return {"error": "Install mss: pip install mss"}
        except Exception as e:
            logger.error("screen_capture_failed", error=str(e))
            return {"error": str(e)}

    async def _ocr_image(self, image_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            text = await asyncio.to_thread(pytesseract.image_to_string, img)
            if text.strip():
                await event_engine.publish(
                    AetherEvent(
                        type=EventType.VISION_OCR,
                        channel=EventChannel.VISION,
                        payload={"text": text[:2000]},
                    )
                )
            return text.strip()[:2000]
        except Exception:
            return ""

    async def analyze_screen(self, question: str | None = None) -> dict[str, Any]:
        """Capture screen and reason about it with LLM."""
        capture = await self.capture_screen()
        if "error" in capture:
            return capture

        ocr = capture.get("ocr", "")
        prompt = question or "Describe what applications and content are visible on this screen."
        context = f"Screen OCR text extracted:\n{ocr}\n\nProvide a concise tactical analysis."

        chunks: list[str] = []
        async for token in llm_router.stream(prompt, context=context):
            chunks.append(token)

        analysis = "".join(chunks)
        await event_engine.publish(
            AetherEvent(
                type=EventType.VISION_SCENE,
                channel=EventChannel.VISION,
                payload={"analysis": analysis, "ocr": ocr[:500]},
            )
        )
        return {"analysis": analysis, "ocr": ocr, "screenshot": capture.get("screenshot")}


screen_intel = ScreenIntel()
