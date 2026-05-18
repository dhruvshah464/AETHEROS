"""Multi-agent orchestration — LangGraph-inspired agent network."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from core.events import AetherEvent, EventChannel, EventType, event_engine
from services.llm_router import llm_router

logger = structlog.get_logger(__name__)


class AgentId(str, Enum):
    COMMANDER = "commander"
    RESEARCH = "research"
    CODING = "coding"
    VISION = "vision"
    PLANNING = "planning"
    SECURITY = "security"
    AUTOMATION = "automation"
    VOICE = "voice"


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETE = "complete"


AGENT_DEFINITIONS = {
    AgentId.COMMANDER: {
        "name": "COMMANDER",
        "role": "Central orchestrator — routes tasks and synthesizes results",
        "color": "#00f0ff",
    },
    AgentId.RESEARCH: {
        "name": "RESEARCH",
        "role": "Information gathering, analysis, and knowledge synthesis",
        "color": "#7b61ff",
    },
    AgentId.CODING: {
        "name": "CODING",
        "role": "Code generation, debugging, and software engineering",
        "color": "#00ff88",
    },
    AgentId.VISION: {
        "name": "VISION",
        "role": "Visual perception, object detection, scene analysis",
        "color": "#ff6b35",
    },
    AgentId.PLANNING: {
        "name": "PLANNING",
        "role": "Strategic planning, task decomposition, workflow design",
        "color": "#ffd700",
    },
    AgentId.SECURITY: {
        "name": "SECURITY",
        "role": "Threat analysis, security auditing, access control",
        "color": "#ff3366",
    },
    AgentId.AUTOMATION: {
        "name": "AUTOMATION",
        "role": "Browser control, terminal execution, workflow automation",
        "color": "#00ccff",
    },
    AgentId.VOICE: {
        "name": "VOICE",
        "role": "Speech recognition, synthesis, conversational interface",
        "color": "#cc66ff",
    },
}


@dataclass
class AgentState:
    id: AgentId
    status: AgentStatus = AgentStatus.IDLE
    current_task: str | None = None
    progress: float = 0.0
    last_activity: float = field(default_factory=time.time)


class AgentOrchestrator:
    def __init__(self) -> None:
        self.agents: dict[AgentId, AgentState] = {
            aid: AgentState(id=aid) for aid in AgentId
        }
        self._task_queue: asyncio.Queue = asyncio.Queue()

    async def get_network_state(self) -> list[dict[str, Any]]:
        return [
            {
                "id": agent.id.value,
                "name": AGENT_DEFINITIONS[agent.id]["name"],
                "role": AGENT_DEFINITIONS[agent.id]["role"],
                "color": AGENT_DEFINITIONS[agent.id]["color"],
                "status": agent.status.value,
                "currentTask": agent.current_task,
                "progress": agent.progress,
                "lastActivity": agent.last_activity,
            }
            for agent in self.agents.values()
        ]

    async def _set_status(
        self, agent_id: AgentId, status: AgentStatus, task: str | None = None, progress: float = 0
    ) -> None:
        agent = self.agents[agent_id]
        agent.status = status
        agent.current_task = task
        agent.progress = progress
        agent.last_activity = time.time()

        await event_engine.publish(
            AetherEvent(
                type=EventType.AGENT_STATUS,
                channel=EventChannel.AGENT,
                payload={
                    "id": agent_id.value,
                    "status": status.value,
                    "currentTask": task,
                    "progress": progress,
                },
            )
        )

    async def _send_message(self, from_id: AgentId, to_id: AgentId, content: str) -> None:
        await event_engine.publish(
            AetherEvent(
                type=EventType.AGENT_MESSAGE,
                channel=EventChannel.AGENT,
                payload={
                    "from": from_id.value,
                    "to": to_id.value,
                    "content": content,
                    "type": "request",
                },
            )
        )

    def _route_agent(self, prompt: str) -> AgentId:
        """Heuristic routing — can be replaced with LLM classifier."""
        lower = prompt.lower()
        if any(w in lower for w in ["code", "debug", "implement", "function", "api"]):
            return AgentId.CODING
        if any(w in lower for w in ["search", "research", "find", "analyze", "report"]):
            return AgentId.RESEARCH
        if any(w in lower for w in ["see", "camera", "vision", "detect", "image", "webcam"]):
            return AgentId.VISION
        if any(w in lower for w in ["plan", "strategy", "roadmap", "steps", "workflow"]):
            return AgentId.PLANNING
        if any(w in lower for w in ["security", "threat", "vulnerability", "audit"]):
            return AgentId.SECURITY
        if any(w in lower for w in ["browser", "automate", "click", "navigate", "terminal"]):
            return AgentId.AUTOMATION
        if any(w in lower for w in ["speak", "voice", "listen", "say"]):
            return AgentId.VOICE
        return AgentId.COMMANDER

    async def execute_task(self, prompt: str, session_id: str = "global") -> AsyncIterator[str]:
        """Route task through agent network with visible inter-agent communication."""
        primary = self._route_agent(prompt)

        await self._set_status(AgentId.COMMANDER, AgentStatus.THINKING, "Analyzing command")
        await self._send_message(
            AgentId.COMMANDER,
            primary,
            f"Routing task to {AGENT_DEFINITIONS[primary]['name']}: {prompt[:100]}",
        )
        await asyncio.sleep(0.3)

        await self._set_status(primary, AgentStatus.EXECUTING, prompt[:80], 0.1)
        await event_engine.publish(
            AetherEvent(
                type=EventType.AGENT_TASK_START,
                channel=EventChannel.AGENT,
                payload={"agentId": primary.value, "task": prompt},
                session_id=session_id,
            )
        )

        # Planning agent collaborates on complex tasks
        if primary not in (AgentId.PLANNING, AgentId.COMMANDER) and len(prompt) > 100:
            await self._set_status(AgentId.PLANNING, AgentStatus.THINKING, "Decomposing task")
            await self._send_message(
                AgentId.PLANNING, primary, "Task decomposition complete. Proceeding."
            )

        agent_context = (
            f"You are the {AGENT_DEFINITIONS[primary]['name']} agent of AetherOS.\n"
            f"Role: {AGENT_DEFINITIONS[primary]['role']}\n"
            f"Execute this task with expertise in your domain."
        )

        token_idx = 0
        async for token in llm_router.stream(prompt, context=agent_context):
            token_idx += 1
            progress = min(0.95, token_idx / 200)
            if token_idx % 20 == 0:
                await self._set_status(primary, AgentStatus.EXECUTING, prompt[:80], progress)
            yield token

        await self._set_status(primary, AgentStatus.COMPLETE, None, 1.0)
        await self._set_status(AgentId.COMMANDER, AgentStatus.IDLE)
        await event_engine.publish(
            AetherEvent(
                type=EventType.AGENT_TASK_COMPLETE,
                channel=EventChannel.AGENT,
                payload={"agentId": primary.value, "task": prompt},
                session_id=session_id,
            )
        )

        # Reset after delay
        await asyncio.sleep(2)
        await self._set_status(primary, AgentStatus.IDLE)


agent_orchestrator = AgentOrchestrator()
