"""Vector memory engine — ChromaDB with sentence-transformers fallback."""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

from core.config import get_settings
from core.events import AetherEvent, EventChannel, EventType, event_engine

logger = structlog.get_logger(__name__)


class MemoryEngine:
    def __init__(self) -> None:
        self._collection = None
        self._local_store: list[dict[str, Any]] = []
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        settings = get_settings()

        try:
            import chromadb

            client = chromadb.HttpClient(
                host=settings.chroma_host, port=settings.chroma_port
            )
            self._collection = client.get_or_create_collection(
                name="aetheros_memory",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("chroma_connected")
        except Exception as e:
            logger.warning("chroma_unavailable_using_local", error=str(e))
            self._collection = None

        self._initialized = True

    async def store(
        self,
        content: str,
        memory_type: str = "episodic",
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        entry_id = f"mem_{uuid.uuid4().hex[:12]}"
        entry = {
            "id": entry_id,
            "content": content,
            "type": memory_type,
            "timestamp": time.time() * 1000,
            "metadata": metadata or {},
        }

        if self._collection:
            try:
                self._collection.add(
                    ids=[entry_id],
                    documents=[content],
                    metadatas=[{"type": memory_type, **(metadata or {})}],
                )
            except Exception as e:
                logger.error("chroma_store_failed", error=str(e))
                self._local_store.append(entry)
        else:
            self._local_store.append(entry)

        await event_engine.publish(
            AetherEvent(
                type=EventType.MEMORY_STORE,
                channel=EventChannel.MEMORY,
                payload=entry,
            )
        )
        return entry

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        results = []

        if self._collection:
            try:
                chroma_results = self._collection.query(
                    query_texts=[query], n_results=limit
                )
                if chroma_results and chroma_results["documents"]:
                    for i, doc in enumerate(chroma_results["documents"][0]):
                        results.append(
                            {
                                "id": chroma_results["ids"][0][i],
                                "content": doc,
                                "distance": chroma_results["distances"][0][i]
                                if chroma_results.get("distances")
                                else 0,
                            }
                        )
            except Exception as e:
                logger.error("chroma_search_failed", error=str(e))

        if not results:
            # Simple keyword fallback
            query_lower = query.lower()
            for entry in reversed(self._local_store):
                if query_lower in entry["content"].lower():
                    results.append(entry)
                    if len(results) >= limit:
                        break

        await event_engine.publish(
            AetherEvent(
                type=EventType.MEMORY_RECALL,
                channel=EventChannel.MEMORY,
                payload={"query": query, "results": results},
            )
        )
        return results

    async def get_timeline(self, limit: int = 50) -> list[dict[str, Any]]:
        if self._collection:
            try:
                data = self._collection.get(limit=limit)
                if data and data["ids"]:
                    return [
                        {
                            "id": data["ids"][i],
                            "content": data["documents"][i],
                            "metadata": data["metadatas"][i] if data.get("metadatas") else {},
                        }
                        for i in range(len(data["ids"]))
                    ]
            except Exception:
                pass
        return list(reversed(self._local_store[-limit:]))


memory_engine = MemoryEngine()
