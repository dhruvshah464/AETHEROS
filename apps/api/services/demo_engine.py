"""Cinematic demo mode — orchestrates real subsystems for viral showcases."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from core.events import AetherEvent, EventChannel, EventType, event_engine
from services.browser_runtime import BrowserMode, browser_runtime
from services.workflow_engine import workflow_engine

logger = structlog.get_logger(__name__)

DEMO_SEQUENCES: dict[str, list[dict[str, Any]]] = {
    "full_mission": [
        {"step": "intro", "message": "AetherOS Demo — Full Mission Sequence", "delay": 2},
        {"step": "telemetry", "message": "Activating system telemetry...", "delay": 2},
        {"step": "agents", "message": "Deploying agent network...", "delay": 2},
        {"step": "browser", "action": "navigate", "params": {"url": "https://news.ycombinator.com"}, "delay": 3},
        {"step": "browser", "action": "screenshot", "delay": 2},
        {"step": "ai", "prompt": "Summarize what a hacker news front page typically contains in 2 sentences.", "delay": 5},
        {"step": "terminal", "command": "echo AetherOS Demo Complete", "delay": 2},
        {"step": "complete", "message": "Mission demo complete.", "delay": 1},
    ],
    "browser_showcase": [
        {"step": "intro", "message": "Browser Autonomy Demo", "delay": 1},
        {"step": "browser", "action": "navigate", "params": {"url": "https://www.google.com"}, "delay": 2},
        {"step": "browser", "action": "search", "params": {"query": "AetherOS AI"}, "delay": 3},
        {"step": "browser", "action": "screenshot", "delay": 2},
        {"step": "complete", "message": "Browser demo complete.", "delay": 1},
    ],
    "recruiter": [
        {"step": "intro", "message": "Recruiter Demo — Full Stack AI Systems", "delay": 2},
        {"step": "browser", "action": "navigate", "params": {"url": "https://github.com"}, "delay": 2},
        {"step": "ai", "prompt": "In 3 bullets, describe what makes a senior AI systems engineer stand out.", "delay": 4},
        {"step": "terminal", "command": "echo AetherOS — Production AI Runtime", "delay": 2},
        {"step": "complete", "message": "Recruiter demo complete.", "delay": 1},
    ],
    "investor": [
        {"step": "intro", "message": "Investor Demo — Autonomous AI Infrastructure", "delay": 2},
        {"step": "browser", "action": "navigate", "params": {"url": "https://openai.com"}, "delay": 3},
        {"step": "ai", "prompt": "Explain the market opportunity for an open-source AI operating layer in 2 sentences.", "delay": 5},
        {"step": "complete", "message": "Investor demo complete.", "delay": 1},
    ],
    "oss_showcase": [
        {"step": "intro", "message": "OSS Showcase — Community Edition", "delay": 1},
        {"step": "browser", "action": "navigate", "params": {"url": "https://news.ycombinator.com"}, "delay": 2},
        {"step": "browser", "action": "screenshot", "delay": 2},
        {"step": "ai", "prompt": "Write a compelling GitHub README tagline for an open-source AI OS.", "delay": 4},
        {"step": "complete", "message": "OSS showcase complete.", "delay": 1},
    ],
    "mission_impossible": [
        {"step": "intro", "message": "MISSION MODE — Autonomous Research Protocol", "delay": 2},
        {"step": "browser", "action": "navigate", "params": {"url": "https://www.anthropic.com"}, "delay": 3},
        {"step": "browser", "action": "extract", "params": {"selector": "body"}, "delay": 2},
        {"step": "ai", "prompt": "You are AETHER. Analyze the page content and produce an executive intelligence brief.", "delay": 6},
        {"step": "terminal", "command": "echo Mission report generated", "delay": 2},
        {"step": "workflow", "nodes": [
            {"id": "m1", "type": "ai", "label": "Final Summary", "params": {"prompt": "One paragraph mission debrief."}},
        ], "delay": 3},
        {"step": "complete", "message": "Mission complete. All systems nominal.", "delay": 1},
    ],
}


class DemoEngine:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self, sequence_id: str = "full_mission") -> dict[str, Any]:
        if self._running:
            return {"ok": False, "error": "Demo already running"}
        steps = DEMO_SEQUENCES.get(sequence_id)
        if not steps:
            return {"ok": False, "error": f"Unknown sequence: {sequence_id}"}

        self._running = True
        self._task = asyncio.create_task(self._run(sequence_id, steps))
        return {"ok": True, "sequence": sequence_id}

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def _run(self, sequence_id: str, steps: list[dict[str, Any]]) -> None:
        await event_engine.publish(
            AetherEvent(
                type=EventType.DEMO_START,
                channel=EventChannel.SYSTEM,
                payload={"sequence": sequence_id},
            )
        )

        browser_runtime.mode = BrowserMode.AUTONOMOUS
        await browser_runtime.start_stream(800)

        try:
            for i, step in enumerate(steps):
                if not self._running:
                    break

                await event_engine.publish(
                    AetherEvent(
                        type=EventType.DEMO_STEP,
                        channel=EventChannel.SYSTEM,
                        payload={"index": i, "step": step.get("step"), "message": step.get("message")},
                    )
                )

                step_type = step.get("step")

                if step_type == "browser":
                    await browser_runtime.execute(
                        step.get("action", "navigate"),
                        step.get("params", {}),
                        force=True,
                    )
                elif step_type == "ai":
                    from services.agents import agent_orchestrator
                    prompt = step.get("prompt", "")
                    async for token in agent_orchestrator.execute_task(prompt):
                        await event_engine.publish(
                            AetherEvent(
                                type=EventType.AI_STREAM_TOKEN,
                                channel=EventChannel.AI,
                                payload={"token": token, "demo": True},
                            )
                        )
                elif step_type == "terminal":
                    from services.terminal_runtime import terminal_runtime
                    await terminal_runtime.execute(step.get("command", "echo demo"))
                elif step_type == "workflow":
                    wf = workflow_engine.create(
                        "Demo Workflow",
                        step.get("nodes", []),
                    )
                    await workflow_engine.execute(wf.id)

                await asyncio.sleep(step.get("delay", 1))

        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            browser_runtime.mode = BrowserMode.SAFE
            await event_engine.publish(
                AetherEvent(
                    type=EventType.DEMO_COMPLETE,
                    channel=EventChannel.SYSTEM,
                    payload={"sequence": sequence_id},
                )
            )

    def list_sequences(self) -> list[dict[str, str]]:
        return [
            {"id": k, "name": k.replace("_", " ").title(), "steps": str(len(v))}
            for k, v in DEMO_SEQUENCES.items()
        ]


demo_engine = DemoEngine()
