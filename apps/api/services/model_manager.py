"""Local/cloud model management — Ollama integration + metrics."""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

from core.config import get_settings
from core.events import AetherEvent, EventChannel, EventType, event_engine
from services.telemetry import telemetry_service

logger = structlog.get_logger(__name__)


class ModelManager:
    async def list_models(self) -> dict[str, Any]:
        settings = get_settings()
        models: list[dict[str, Any]] = []
        providers = []

        # Ollama
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{settings.ollama_base_url}/api/tags")
                if r.status_code == 200:
                    data = r.json()
                    for m in data.get("models", []):
                        models.append({
                            "id": m.get("name"),
                            "provider": "ollama",
                            "size": m.get("size"),
                            "modified": m.get("modified_at"),
                        })
                    providers.append({"name": "ollama", "status": "online", "url": settings.ollama_base_url})
        except Exception as e:
            providers.append({"name": "ollama", "status": "offline", "error": str(e)})

        if settings.openai_api_key:
            providers.append({"name": "openai", "status": "configured", "model": settings.default_llm_model})
        if settings.anthropic_api_key:
            providers.append({"name": "anthropic", "status": "configured", "model": "claude-3-5-sonnet"})

        return {
            "models": models,
            "providers": providers,
            "active": {
                "primary": settings.default_llm_provider,
                "model": settings.default_llm_model,
                "fallback": settings.fallback_llm_provider,
            },
        }

    async def benchmark(self, provider: str = "ollama", model: str | None = None) -> dict[str, Any]:
        settings = get_settings()
        model = model or settings.fallback_llm_model
        start = time.perf_counter()

        try:
            if provider == "ollama":
                async with httpx.AsyncClient(timeout=60.0) as client:
                    r = await client.post(
                        f"{settings.ollama_base_url}/api/generate",
                        json={"model": model, "prompt": "Say OK", "stream": False},
                    )
                    r.raise_for_status()
                    latency = (time.perf_counter() - start) * 1000
                    telemetry_service.update_ai_usage(model=model, latency_ms=latency)
                    result = {"provider": provider, "model": model, "latencyMs": latency, "status": "ok"}
            else:
                from services.llm_router import llm_router
                tokens = 0
                async for _ in llm_router.stream("Respond with OK", provider=provider):
                    tokens += 1
                latency = (time.perf_counter() - start) * 1000
                result = {"provider": provider, "latencyMs": latency, "tokens": tokens, "status": "ok"}

            await event_engine.publish(
                AetherEvent(
                    type=EventType.MODEL_STATUS,
                    channel=EventChannel.AI,
                    payload=result,
                )
            )
            return result
        except Exception as e:
            return {"provider": provider, "status": "error", "error": str(e)}

    async def pull_model(self, name: str) -> dict[str, Any]:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.ollama_base_url}/api/pull",
                    json={"name": name},
                ) as response:
                    async for line in response.aiter_lines():
                        pass
            return {"ok": True, "model": name}
        except Exception as e:
            return {"ok": False, "error": str(e)}


model_manager = ModelManager()
