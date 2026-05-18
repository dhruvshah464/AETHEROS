"""Memory V3 — graph memory with importance scoring and temporal links."""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

from core.events import AetherEvent, EventChannel, EventType, event_engine
from services.memory import memory_engine

logger = structlog.get_logger(__name__)


@dataclass
class MemoryNode:
    id: str
    content: str
    memory_type: str
    importance: float
    timestamp: float
    agent_id: str | None = None
    embedding_hint: str | None = None


@dataclass
class MemoryEdge:
    source: str
    target: str
    relation: str
    weight: float = 1.0


class MemoryGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, MemoryNode] = {}
        self._edges: list[MemoryEdge] = []

    def _score_importance(self, content: str, memory_type: str) -> float:
        base = 0.3
        if memory_type == "procedural":
            base += 0.2
        if len(content) > 200:
            base += 0.15
        keywords = ["critical", "security", "error", "mission", "deploy", "key", "password"]
        for kw in keywords:
            if kw in content.lower():
                base += 0.1
        return min(1.0, base)

    async def store(
        self,
        content: str,
        memory_type: str = "episodic",
        agent_id: str | None = None,
        link_to: str | None = None,
        relation: str = "related",
    ) -> dict[str, Any]:
        node_id = f"mem_{uuid.uuid4().hex[:10]}"
        importance = self._score_importance(content, memory_type)
        node = MemoryNode(
            id=node_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            timestamp=time.time() * 1000,
            agent_id=agent_id,
        )
        self._nodes[node_id] = node

        if link_to and link_to in self._nodes:
            self._edges.append(MemoryEdge(source=link_to, target=node_id, relation=relation))

        # Also persist to vector store
        await memory_engine.store(content, memory_type, {"importance": importance, "agentId": agent_id})

        await event_engine.publish(
            AetherEvent(
                type=EventType.MEMORY_STORE,
                channel=EventChannel.MEMORY,
                payload={"id": node_id, "content": content, "importance": importance, "graph": True},
            )
        )
        return self._node_dict(node)

    def _node_dict(self, n: MemoryNode) -> dict[str, Any]:
        return {
            "id": n.id,
            "content": n.content,
            "type": n.memory_type,
            "importance": n.importance,
            "timestamp": n.timestamp,
            "agentId": n.agent_id,
        }

    async def search_graph(self, query: str, limit: int = 20) -> dict[str, Any]:
        vector_results = await memory_engine.search(query, limit)
        matched_ids = {r.get("id") for r in vector_results}

        nodes = []
        for nid, node in self._nodes.items():
            if query.lower() in node.content.lower() or nid in matched_ids:
                nodes.append(self._node_dict(node))
        nodes.sort(key=lambda x: x["importance"], reverse=True)

        edges = [
            {"source": e.source, "target": e.target, "relation": e.relation, "weight": e.weight}
            for e in self._edges
            if e.source in {n["id"] for n in nodes} or e.target in {n["id"] for n in nodes}
        ]

        return {"nodes": nodes[:limit], "edges": edges, "vectorMatches": vector_results}

    def get_full_graph(self) -> dict[str, Any]:
        return {
            "nodes": [self._node_dict(n) for n in self._nodes.values()],
            "edges": [
                {"source": e.source, "target": e.target, "relation": e.relation, "weight": e.weight}
                for e in self._edges
            ],
        }

    def timeline(self, limit: int = 50) -> list[dict[str, Any]]:
        nodes = sorted(self._nodes.values(), key=lambda n: n.timestamp, reverse=True)
        return [self._node_dict(n) for n in nodes[:limit]]

    def compress_old_memories(self, max_nodes: int = 500) -> int:
        if len(self._nodes) <= max_nodes:
            return 0
        sorted_nodes = sorted(self._nodes.values(), key=lambda n: (n.importance, n.timestamp))
        remove_count = len(self._nodes) - max_nodes
        for node in sorted_nodes[:remove_count]:
            del self._nodes[node.id]
        return remove_count


memory_graph = MemoryGraph()
