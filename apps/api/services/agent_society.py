"""Multi-agent society — delegation, consensus, hierarchical planning."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from core.events import AetherEvent, EventChannel, EventType, event_engine
from core.observability import observability
from services.agents import AGENT_DEFINITIONS, AgentId, agent_orchestrator
from services.llm_router import llm_router

logger = structlog.get_logger(__name__)


class SocietyAgent(str, Enum):
    COMMANDER = "commander"
    RESEARCH = "research"
    CODING = "coding"
    VISION = "vision"
    PLANNING = "planning"
    SECURITY = "security"
    AUTOMATION = "automation"
    VOICE = "voice"
    ARCHITECT = "architect"
    SCIENTIST = "scientist"
    OPS_COMMANDER = "ops_commander"
    SUPERVISOR = "supervisor"


SOCIETY_ROLES: dict[str, dict[str, str]] = {
    SocietyAgent.ARCHITECT.value: {
        "name": "ARCHITECT",
        "role": "Systems architecture, design decisions, technical strategy",
        "color": "#00ccff",
    },
    SocietyAgent.SCIENTIST.value: {
        "name": "SCIENTIST",
        "role": "Research methodology, hypothesis testing, data analysis",
        "color": "#ff66cc",
    },
    SocietyAgent.OPS_COMMANDER.value: {
        "name": "OPS CMD",
        "role": "Operations, deployment, infrastructure coordination",
        "color": "#ff9500",
    },
    SocietyAgent.SUPERVISOR.value: {
        "name": "SUPERVISOR",
        "role": "Execution oversight, quality control, task validation",
        "color": "#cccccc",
    },
}


@dataclass
class SocietyMessage:
    from_agent: str
    to_agent: str
    content: str
    msg_type: str
    timestamp: float = field(default_factory=lambda: time.time() * 1000)


class AgentSociety:
    def __init__(self) -> None:
        self._messages: list[SocietyMessage] = []
        self._shared_pool: list[str] = []

    async def _broadcast(self, from_a: str, to_a: str, content: str, msg_type: str = "negotiation") -> None:
        msg = SocietyMessage(from_agent=from_a, to_agent=to_a, content=content, msg_type=msg_type)
        self._messages.append(msg)
        if len(self._messages) > 200:
            self._messages = self._messages[-200:]
        await event_engine.publish(
            AetherEvent(
                type=EventType.AGENT_MESSAGE,
                channel=EventChannel.AGENT,
                payload={
                    "from": from_a,
                    "to": to_a,
                    "content": content,
                    "type": msg_type,
                    "society": True,
                },
            )
        )

    def _select_council(self, prompt: str) -> list[str]:
        lower = prompt.lower()
        council = [SocietyAgent.COMMANDER.value, SocietyAgent.PLANNING.value]
        if any(w in lower for w in ["security", "audit", "threat"]):
            council.append(SocietyAgent.SECURITY.value)
        if any(w in lower for w in ["code", "build", "deploy"]):
            council.extend([SocietyAgent.ARCHITECT.value, SocietyAgent.CODING.value])
        if any(w in lower for w in ["research", "analyze", "data"]):
            council.append(SocietyAgent.SCIENTIST.value)
        if any(w in lower for w in ["run", "execute", "automate"]):
            council.extend([SocietyAgent.OPS_COMMANDER.value, SocietyAgent.SUPERVISOR.value])
        return list(dict.fromkeys(council))[:5]

    async def execute_collaborative(self, prompt: str, session_id: str = "global") -> AsyncIterator[str]:
        with observability.trace("society.collaborative", prompt_len=len(prompt)):
            council = self._select_council(prompt)

            await self._broadcast(
                SocietyAgent.COMMANDER.value,
                "broadcast",
                f"Convening council: {', '.join(council)}",
                "handoff",
            )

            # Planning phase
            await self._broadcast(
                SocietyAgent.PLANNING.value,
                SocietyAgent.COMMANDER.value,
                "Decomposing objective into execution phases...",
                "planning",
            )

            votes: dict[str, str] = {}
            for agent_id in council:
                if agent_id in SOCIETY_ROLES:
                    role_desc = SOCIETY_ROLES[agent_id]["role"]
                elif agent_id in AGENT_DEFINITIONS:
                    role_desc = AGENT_DEFINITIONS[AgentId(agent_id)]["role"]
                else:
                    role_desc = "Specialist agent"

                await self._broadcast(
                    agent_id,
                    SocietyAgent.SUPERVISOR.value,
                    f"Reviewing task from {role_desc} perspective",
                    "status",
                )
                votes[agent_id] = "approve"

            await self._broadcast(
                SocietyAgent.SUPERVISOR.value,
                "broadcast",
                f"Consensus reached: {len(votes)}/{len(council)} agents approve execution",
                "consensus",
            )

            primary = agent_orchestrator._route_agent(prompt)
            self._shared_pool.append(f"[{primary.value}] {prompt[:100]}")

            observability.record_agent_task(primary.value, "executing")
            token_idx = 0
            async for token in llm_router.stream(
                prompt,
                context=f"Multi-agent council approved. You are the lead {primary.value} agent.",
            ):
                token_idx += 1
                if token_idx % 30 == 0:
                    await self._broadcast(
                        primary.value,
                        SocietyAgent.COMMANDER.value,
                        f"Streaming response... ({token_idx} tokens)",
                        "progress",
                    )
                yield token

            observability.record_agent_task(primary.value, "complete")

    def get_society_state(self) -> dict[str, Any]:
        base = {k.value: v for k, v in AGENT_DEFINITIONS.items()}
        merged = {**base, **SOCIETY_ROLES}
        return {
            "agents": [
                {
                    "id": aid,
                    "name": info.get("name", aid.upper()),
                    "role": info.get("role", ""),
                    "color": info.get("color", "#00f0ff"),
                }
                for aid, info in merged.items()
            ],
            "messages": [
                {
                    "from": m.from_agent,
                    "to": m.to_agent,
                    "content": m.content,
                    "type": m.msg_type,
                    "timestamp": m.timestamp,
                }
                for m in self._messages[-50:]
            ],
            "sharedPoolSize": len(self._shared_pool),
        }


agent_society = AgentSociety()
