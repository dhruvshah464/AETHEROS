"""Live computer vision — YOLOv8 detection with OpenCV."""

from __future__ import annotations

import asyncio
import base64
import io
from typing import Any

import structlog

from core.events import AetherEvent, EventChannel, EventType, event_engine

logger = structlog.get_logger(__name__)


class VisionService:
    def __init__(self) -> None:
        self._model = None
        self._running = False
        self._task: asyncio.Task | None = None

    def _load_model(self):
        if self._model is None:
            try:
                from ultralytics import YOLO

                self._model = YOLO("yolov8n.pt")
                logger.info("yolo_model_loaded")
            except Exception as e:
                logger.warning("yolo_load_failed", error=str(e))
        return self._model

    async def process_frame(self, frame_b64: str) -> list[dict[str, Any]]:
        """Process a base64-encoded image frame."""
        detections = []
        try:
            import cv2
            import numpy as np
            from PIL import Image

            img_data = base64.b64decode(frame_b64)
            img = Image.open(io.BytesIO(img_data))
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            h, w = frame.shape[:2]

            model = self._load_model()
            if model:
                results = model(frame, verbose=False)
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].tolist()
                        detections.append(
                            {
                                "label": result.names[cls_id],
                                "confidence": round(conf, 3),
                                "bbox": [
                                    round(xyxy[0] / w, 4),
                                    round(xyxy[1] / h, 4),
                                    round((xyxy[2] - xyxy[0]) / w, 4),
                                    round((xyxy[3] - xyxy[1]) / h, 4),
                                ],
                            }
                        )
            else:
                # OpenCV Haar cascade fallback for faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, fw, fh) in faces:
                    detections.append(
                        {
                            "label": "face",
                            "confidence": 0.85,
                            "bbox": [
                                round(x / w, 4),
                                round(y / h, 4),
                                round(fw / w, 4),
                                round(fh / h, 4),
                            ],
                        }
                    )

            await event_engine.publish(
                AetherEvent(
                    type=EventType.VISION_DETECTION,
                    channel=EventChannel.VISION,
                    payload={"detections": detections, "frameSize": [w, h]},
                )
            )
        except Exception as e:
            logger.error("vision_process_error", error=str(e))

        return detections


vision_service = VisionService()
