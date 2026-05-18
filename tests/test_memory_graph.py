import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))


def test_memory_graph_store_and_search():
    from services.memory_graph import memory_graph

    async def run():
        n1 = await memory_graph.store("First memory node", "episodic")
        n2 = await memory_graph.store("Linked second node", "semantic", link_to=n1["id"])
        graph = memory_graph.get_full_graph()
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 1
        result = await memory_graph.search_graph("second")
        assert len(result["nodes"]) >= 1

    asyncio.run(run())
