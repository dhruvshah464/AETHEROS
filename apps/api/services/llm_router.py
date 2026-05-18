"""Multimodal LLM routing — OpenAI, Anthropic, Ollama with fallback."""

from __future__ import annotations

import time
from typing import AsyncIterator

import httpx
import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.config import get_settings
from services.telemetry import telemetry_service

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are AETHER, the central intelligence of AetherOS — a cinematic AI operating system.
You speak with precision, confidence, and tactical clarity like an advanced military AI assistant.
You can orchestrate agents, analyze systems, control automation, and provide strategic guidance.
Keep responses concise unless depth is requested. Use technical language when appropriate.
When reasoning through complex tasks, structure your thinking clearly."""


class LLMRouter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._clients: dict = {}

    def _get_openai(self) -> ChatOpenAI | None:
        if not self.settings.openai_api_key:
            return None
        return ChatOpenAI(
            model=self.settings.default_llm_model,
            api_key=self.settings.openai_api_key,
            streaming=True,
            temperature=0.7,
        )

    def _get_anthropic(self) -> ChatAnthropic | None:
        if not self.settings.anthropic_api_key:
            return None
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=self.settings.anthropic_api_key,
            streaming=True,
            temperature=0.7,
        )

    async def _stream_ollama(self, prompt: str, model: str) -> AsyncIterator[str]:
        url = f"{self.settings.ollama_base_url}/api/generate"
        payload = {"model": model, "prompt": f"{SYSTEM_PROMPT}\n\nUser: {prompt}\n\nAssistant:", "stream": True}
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                import json

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break

    async def stream(
        self, prompt: str, context: str | None = None, provider: str | None = None
    ) -> AsyncIterator[str]:
        provider = provider or self.settings.default_llm_provider
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nQuery: {prompt}"

        start = time.perf_counter()
        token_count = 0

        # Try primary provider
        try:
            if provider == "openai":
                client = self._get_openai()
                if client:
                    messages = [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=full_prompt),
                    ]
                    async for chunk in client.astream(messages):
                        if chunk.content:
                            token_count += 1
                            yield str(chunk.content)
                    latency = (time.perf_counter() - start) * 1000
                    telemetry_service.update_ai_usage(
                        tokens_out=token_count,
                        model=self.settings.default_llm_model,
                        latency_ms=latency,
                    )
                    return

            elif provider == "anthropic":
                client = self._get_anthropic()
                if client:
                    messages = [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=full_prompt),
                    ]
                    async for chunk in client.astream(messages):
                        if chunk.content:
                            token_count += 1
                            yield str(chunk.content)
                    latency = (time.perf_counter() - start) * 1000
                    telemetry_service.update_ai_usage(
                        tokens_out=token_count, model="claude-3-5-sonnet", latency_ms=latency
                    )
                    return

            elif provider == "ollama":
                async for token in self._stream_ollama(
                    full_prompt, self.settings.fallback_llm_model
                ):
                    token_count += 1
                    yield token
                latency = (time.perf_counter() - start) * 1000
                telemetry_service.update_ai_usage(
                    tokens_out=token_count,
                    model=self.settings.fallback_llm_model,
                    latency_ms=latency,
                )
                return

        except Exception as e:
            logger.warning("llm_primary_failed", provider=provider, error=str(e))

        # Fallback chain
        fallbacks = []
        if provider != "ollama":
            fallbacks.append("ollama")
        if provider != "openai" and self.settings.openai_api_key:
            fallbacks.append("openai")
        if provider != "anthropic" and self.settings.anthropic_api_key:
            fallbacks.append("anthropic")

        for fb in fallbacks:
            try:
                logger.info("llm_fallback", provider=fb)
                async for token in self.stream(full_prompt, provider=fb):
                    yield token
                return
            except Exception as e:
                logger.warning("llm_fallback_failed", provider=fb, error=str(e))

        # Offline intelligent response
        yield self._offline_response(full_prompt)

    def _offline_response(self, prompt: str) -> str:
        return (
            f"[AETHER OFFLINE MODE] Received command: \"{prompt[:200]}\"\n\n"
            "No LLM provider is configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, "
            "or start Ollama locally to enable full intelligence.\n\n"
            "System subsystems remain operational: telemetry, agents, vision, and event engine."
        )


llm_router = LLMRouter()
