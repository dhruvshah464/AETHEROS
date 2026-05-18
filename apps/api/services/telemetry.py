"""Live system telemetry — real psutil + optional GPU stats."""

from __future__ import annotations

import asyncio
import platform
from typing import Any

import psutil
import structlog

from core.config import get_settings
from core.events import AetherEvent, EventChannel, EventType, event_engine

logger = structlog.get_logger(__name__)

_net_prev: dict[str, int] = {}


def _get_gpu_stats() -> list[dict[str, Any]]:
    gpus = []
    try:
        import subprocess

        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    gpus.append(
                        {
                            "name": parts[0],
                            "utilization": float(parts[1]) if parts[1] != "[N/A]" else 0,
                            "memoryUsedMb": float(parts[2]) if parts[2] != "[N/A]" else 0,
                            "memoryTotalMb": float(parts[3]) if parts[3] != "[N/A]" else 0,
                            "temperature": float(parts[4]) if parts[4] != "[N/A]" else None,
                        }
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return gpus


def collect_snapshot(ai_usage: dict | None = None) -> dict[str, Any]:
    global _net_prev

    cpu_freq = psutil.cpu_freq()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    processes = []
    for proc in sorted(
        psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]),
        key=lambda p: p.info.get("cpu_percent") or 0,
        reverse=True,
    )[:12]:
        try:
            info = proc.info
            mem_info = info.get("memory_info")
            processes.append(
                {
                    "pid": info["pid"],
                    "name": info["name"] or "unknown",
                    "cpuPercent": round(info.get("cpu_percent") or 0, 1),
                    "memoryMb": round((mem_info.rss / 1024 / 1024) if mem_info else 0, 1),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return {
        "hostname": platform.node(),
        "platform": f"{platform.system()} {platform.release()}",
        "cpu": {
            "percent": round(psutil.cpu_percent(interval=None), 1),
            "cores": psutil.cpu_count(logical=True) or 1,
            "freqMhz": round(cpu_freq.current if cpu_freq else 0, 0),
        },
        "memory": {
            "totalGb": round(mem.total / 1024**3, 2),
            "usedGb": round(mem.used / 1024**3, 2),
            "percent": round(mem.percent, 1),
        },
        "disk": {
            "totalGb": round(disk.total / 1024**3, 2),
            "usedGb": round(disk.used / 1024**3, 2),
            "percent": round(disk.percent, 1),
        },
        "network": {
            "bytesSent": net.bytes_sent,
            "bytesRecv": net.bytes_recv,
            "packetsSent": net.packets_sent,
            "packetsRecv": net.packets_recv,
        },
        "gpu": _get_gpu_stats(),
        "processes": processes,
        "aiUsage": ai_usage
        or {
            "tokensIn": 0,
            "tokensOut": 0,
            "activeModels": [],
            "inferenceLatencyMs": 0,
        },
    }


class TelemetryService:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._ai_usage: dict = {
            "tokensIn": 0,
            "tokensOut": 0,
            "activeModels": [],
            "inferenceLatencyMs": 0,
        }

    def update_ai_usage(
        self,
        tokens_in: int = 0,
        tokens_out: int = 0,
        model: str | None = None,
        latency_ms: float = 0,
    ) -> None:
        self._ai_usage["tokensIn"] += tokens_in
        self._ai_usage["tokensOut"] += tokens_out
        if model and model not in self._ai_usage["activeModels"]:
            self._ai_usage["activeModels"].append(model)
            if len(self._ai_usage["activeModels"]) > 5:
                self._ai_usage["activeModels"] = self._ai_usage["activeModels"][-5:]
        if latency_ms:
            self._ai_usage["inferenceLatencyMs"] = latency_ms

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        settings = get_settings()
        interval = settings.telemetry_interval_ms / 1000
        self._task = asyncio.create_task(self._loop(interval))
        logger.info("telemetry_started", interval_ms=settings.telemetry_interval_ms)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self, interval: float) -> None:
        while self._running:
            try:
                snapshot = collect_snapshot(self._ai_usage)
                await event_engine.publish(
                    AetherEvent(
                        type=EventType.TELEMETRY_SNAPSHOT,
                        channel=EventChannel.TELEMETRY,
                        payload=snapshot,
                    )
                )
            except Exception as e:
                logger.error("telemetry_error", error=str(e))
            await asyncio.sleep(interval)


telemetry_service = TelemetryService()
