"""Plugin registry — dynamic loading of AetherOS extensions."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import structlog

from core.config import get_settings

logger = structlog.get_logger(__name__)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, dict[str, Any]] = {}

    def discover(self) -> list[dict[str, Any]]:
        settings = get_settings()
        plugins_dir = Path(settings.plugins_dir)
        if not plugins_dir.is_absolute():
            plugins_dir = Path(__file__).resolve().parents[2] / plugins_dir

        plugins_dir.mkdir(parents=True, exist_ok=True)
        discovered: list[dict[str, Any]] = []

        for manifest_path in plugins_dir.glob("*/plugin.json"):
            try:
                manifest = json.loads(manifest_path.read_text())
                plugin_id = manifest.get("id", manifest_path.parent.name)
                manifest["path"] = str(manifest_path.parent)
                manifest["status"] = "registered"
                self._plugins[plugin_id] = manifest
                discovered.append(manifest)
            except Exception as e:
                logger.warning("plugin_load_failed", path=str(manifest_path), error=str(e))

        return discovered

    def get(self, plugin_id: str) -> dict[str, Any] | None:
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[dict[str, Any]]:
        if not self._plugins:
            return self.discover()
        return list(self._plugins.values())

    def marketplace(self) -> list[dict[str, Any]]:
        """Curated + discovered plugins for marketplace UI."""
        discovered = self.list_plugins()
        curated = [
            {
                "id": "github-operator",
                "name": "GitHub Operator",
                "description": "Autonomous repo management and PR workflows",
                "version": "1.0.0",
                "author": "AetherOS",
                "type": "agent",
                "rating": 4.9,
                "installs": 1240,
                "status": "available",
            },
            {
                "id": "slack-ops",
                "name": "Slack Ops Bot",
                "description": "Deploy agents to Slack channels",
                "version": "0.9.0",
                "author": "Community",
                "type": "tool",
                "rating": 4.7,
                "installs": 890,
                "status": "available",
            },
            {
                "id": "k8s-operator",
                "name": "Kubernetes Operator",
                "description": "Cluster orchestration from AetherOS",
                "version": "1.2.0",
                "author": "AetherOS",
                "type": "workflow",
                "rating": 4.8,
                "installs": 2100,
                "status": "available",
            },
        ]
        for p in discovered:
            p.setdefault("rating", 5.0)
            p.setdefault("installs", 1)
            p.setdefault("status", "installed")
        return curated + discovered

    def load_tool(self, plugin_id: str) -> Any | None:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return None
        tool_path = Path(plugin["path"]) / "tool.py"
        if not tool_path.exists():
            return None
        spec = importlib.util.spec_from_file_location(f"aetheros_plugin_{plugin_id}", tool_path)
        if not spec or not spec.loader:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "run", None)


plugin_registry = PluginRegistry()
