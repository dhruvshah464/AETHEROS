"""DAG workflow orchestration engine with approval checkpoints."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

import structlog

from core.events import AetherEvent, EventChannel, EventType, event_engine

logger = structlog.get_logger(__name__)


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    id: str
    type: str
    label: str
    params: dict[str, Any]
    depends_on: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None
    error: str | None = None


@dataclass
class Workflow:
    id: str
    name: str
    nodes: list[WorkflowNode]
    status: str = "pending"
    created_at: float = field(default_factory=lambda: time.time() * 1000)


class WorkflowEngine:
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._running: set[str] = set()

    def create(self, name: str, nodes: list[dict[str, Any]]) -> Workflow:
        wf_id = f"wf_{uuid.uuid4().hex[:10]}"
        wf_nodes = [
            WorkflowNode(
                id=n.get("id", f"node_{i}"),
                type=n["type"],
                label=n.get("label", n["type"]),
                params=n.get("params", {}),
                depends_on=n.get("dependsOn", n.get("depends_on", [])),
            )
            for i, n in enumerate(nodes)
        ]
        wf = Workflow(id=wf_id, name=name, nodes=wf_nodes)
        self._workflows[wf_id] = wf
        return wf

    def get(self, wf_id: str) -> Workflow | None:
        return self._workflows.get(wf_id)

    def list_all(self) -> list[dict[str, Any]]:
        return [self._to_dict(wf) for wf in self._workflows.values()]

    def _to_dict(self, wf: Workflow) -> dict[str, Any]:
        return {
            "id": wf.id,
            "name": wf.name,
            "status": wf.status,
            "createdAt": wf.created_at,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "status": n.status.value,
                    "dependsOn": n.depends_on,
                    "result": n.result,
                    "error": n.error,
                }
                for n in wf.nodes
            ],
        }

    async def execute(self, wf_id: str) -> dict[str, Any]:
        wf = self._workflows.get(wf_id)
        if not wf:
            return {"ok": False, "error": "Workflow not found"}
        if wf_id in self._running:
            return {"ok": False, "error": "Workflow already running"}

        self._running.add(wf_id)
        wf.status = "running"
        asyncio.create_task(self._run_workflow(wf))
        return {"ok": True, "workflowId": wf_id}

    async def _run_workflow(self, wf: Workflow) -> None:
        await event_engine.publish(
            AetherEvent(
                type=EventType.WORKFLOW_START,
                channel=EventChannel.AUTOMATION,
                payload={"workflowId": wf.id, "name": wf.name},
            )
        )

        completed: set[str] = set()
        try:
            while len(completed) < len(wf.nodes):
                progress = False
                for node in wf.nodes:
                    if node.id in completed:
                        continue
                    if not all(dep in completed for dep in node.depends_on):
                        continue

                    progress = True
                    await self._run_node(wf, node)
                    if node.status == NodeStatus.FAILED:
                        wf.status = "failed"
                        break
                    completed.add(node.id)

                if not progress:
                    break

            if wf.status != "failed":
                wf.status = "complete"
        finally:
            self._running.discard(wf.id)
            await event_engine.publish(
                AetherEvent(
                    type=EventType.WORKFLOW_COMPLETE,
                    channel=EventChannel.AUTOMATION,
                    payload={"workflowId": wf.id, "status": wf.status},
                )
            )

    async def _run_node(self, wf: Workflow, node: WorkflowNode) -> None:
        node.status = NodeStatus.RUNNING
        await event_engine.publish(
            AetherEvent(
                type=EventType.WORKFLOW_NODE_START,
                channel=EventChannel.AUTOMATION,
                payload={"workflowId": wf.id, "nodeId": node.id, "label": node.label},
            )
        )

        try:
            if node.type == "wait":
                await asyncio.sleep(node.params.get("seconds", 1))
                node.result = "waited"
            elif node.type == "ai":
                from services.agents import agent_orchestrator
                prompt = node.params.get("prompt", "")
                chunks = []
                async for token in agent_orchestrator.execute_task(prompt):
                    chunks.append(token)
                node.result = "".join(chunks)
            elif node.type == "browser":
                from services.browser_runtime import browser_runtime
                result = await browser_runtime.execute(
                    node.params.get("action", "navigate"),
                    node.params.get("params", {}),
                    force=node.params.get("force", False),
                )
                node.result = result
                if not result.get("ok"):
                    raise RuntimeError(result.get("error", "Browser action failed"))
            elif node.type == "terminal":
                from services.terminal_runtime import terminal_runtime
                result = await terminal_runtime.execute(node.params.get("command", "echo hello"))
                node.result = result
                if not result.get("ok"):
                    raise RuntimeError(result.get("error", "Terminal failed"))
            elif node.type == "approval":
                node.status = NodeStatus.WAITING
                await asyncio.sleep(node.params.get("timeout", 30))
                node.result = "auto-approved"
            else:
                node.result = f"Unknown node type: {node.type}"

            node.status = NodeStatus.COMPLETE
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            logger.error("workflow_node_failed", node=node.id, error=str(e))

        await event_engine.publish(
            AetherEvent(
                type=EventType.WORKFLOW_NODE_COMPLETE,
                channel=EventChannel.AUTOMATION,
                payload={
                    "workflowId": wf.id,
                    "nodeId": node.id,
                    "status": node.status.value,
                    "result": str(node.result)[:500] if node.result else None,
                },
            )
        )


workflow_engine = WorkflowEngine()
