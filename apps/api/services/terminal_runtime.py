"""Sandboxed terminal execution with streaming output and audit logs."""

from __future__ import annotations

import asyncio
import os
import shlex
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from core.config import get_settings
from core.events import AetherEvent, EventChannel, EventType, event_engine

logger = structlog.get_logger(__name__)


@dataclass
class TerminalEntry:
    id: str
    command: str
    cwd: str
    status: str = "running"
    output: str = ""
    exit_code: int | None = None
    timestamp: float = field(default_factory=lambda: time.time() * 1000)


class TerminalRuntime:
    def __init__(self) -> None:
        self._audit_log: list[TerminalEntry] = []
        self._sandbox: Path | None = None

    def _get_sandbox(self) -> Path:
        if self._sandbox is None:
            settings = get_settings()
            self._sandbox = Path(settings.terminal_sandbox_dir)
            self._sandbox.mkdir(parents=True, exist_ok=True)
        return self._sandbox

    def _validate_command(self, command: str) -> tuple[bool, str]:
        settings = get_settings()
        parts = shlex.split(command.strip())
        if not parts:
            return False, "Empty command"
        base = parts[0].split("/")[-1]
        if base not in settings.terminal_allowed_list:
            return False, f"Command '{base}' not in allowlist"
        dangerous = ["sudo", "rm -rf", "mkfs", "dd if=", "> /dev/", "chmod 777 /"]
        lower = command.lower()
        for d in dangerous:
            if d in lower:
                return False, f"Blocked dangerous pattern: {d}"
        return True, ""

    async def execute(self, command: str, cwd: str | None = None) -> dict[str, Any]:
        ok, err = self._validate_command(command)
        if not ok:
            return {"ok": False, "error": err}

        sandbox = self._get_sandbox()
        work_dir = sandbox / (cwd or ".")
        work_dir.mkdir(parents=True, exist_ok=True)

        entry = TerminalEntry(
            id=f"term_{uuid.uuid4().hex[:10]}",
            command=command,
            cwd=str(work_dir),
        )
        self._audit_log.append(entry)

        await event_engine.publish(
            AetherEvent(
                type=EventType.TERMINAL_COMMAND,
                channel=EventChannel.AUTOMATION,
                payload={"id": entry.id, "command": command, "cwd": entry.cwd},
            )
        )

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "AETHEROS_SANDBOX": "1"},
            )

            output_lines: list[str] = []
            assert proc.stdout is not None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace")
                output_lines.append(decoded)
                entry.output += decoded
                await event_engine.publish(
                    AetherEvent(
                        type=EventType.TERMINAL_OUTPUT,
                        channel=EventChannel.AUTOMATION,
                        payload={
                            "id": entry.id,
                            "line": decoded,
                            "stream": "stdout",
                        },
                    )
                )

            await proc.wait()
            entry.exit_code = proc.returncode
            entry.status = "complete" if proc.returncode == 0 else "failed"

            return {
                "ok": entry.status == "complete",
                "id": entry.id,
                "output": entry.output,
                "exitCode": entry.exit_code,
            }
        except Exception as e:
            entry.status = "failed"
            entry.output += f"\nError: {e}"
            return {"ok": False, "error": str(e), "id": entry.id}

    def get_audit_log(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            {
                "id": e.id,
                "command": e.command,
                "cwd": e.cwd,
                "status": e.status,
                "output": e.output[-2000:],
                "exitCode": e.exit_code,
                "timestamp": e.timestamp,
            }
            for e in self._audit_log[-limit:]
        ]


terminal_runtime = TerminalRuntime()
