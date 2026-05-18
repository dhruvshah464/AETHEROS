"""Playwright browser automation runtime with screenshot streaming."""

from __future__ import annotations

import asyncio
import base64
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from core.config import get_settings
from core.events import AetherEvent, EventChannel, EventType, event_engine

logger = structlog.get_logger(__name__)


class BrowserMode(str, Enum):
    SAFE = "safe"
    AUTONOMOUS = "autonomous"


@dataclass
class BrowserAction:
    id: str
    type: str
    description: str
    params: dict[str, Any]
    status: str = "pending"
    result: str | None = None
    timestamp: float = field(default_factory=lambda: time.time() * 1000)


class BrowserRuntime:
    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._lock = asyncio.Lock()
        self.mode = BrowserMode.SAFE
        self._action_log: list[BrowserAction] = []
        self._pending_approvals: dict[str, BrowserAction] = {}
        self._stream_task: asyncio.Task | None = None
        self._streaming = False
        self._current_url = ""

    async def _ensure_browser(self) -> bool:
        if self._page is not None:
            try:
                await self._page.title()
                return True
            except Exception:
                await self.stop()

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            settings = get_settings()
            self._browser = await self._playwright.chromium.launch(
                headless=settings.browser_headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="AetherOS/1.0 Autonomous Browser",
            )
            self._page = await self._context.new_page()
            logger.info("browser_launched")
            return True
        except Exception as e:
            logger.error("browser_launch_failed", error=str(e))
            return False

    async def start_stream(self, interval_ms: int = 500) -> None:
        if self._streaming:
            return
        self._streaming = True
        self._stream_task = asyncio.create_task(self._stream_loop(interval_ms))

    async def stop_stream(self) -> None:
        self._streaming = False
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass

    async def _stream_loop(self, interval_ms: int) -> None:
        while self._streaming:
            if self._page:
                await self._publish_screenshot()
            await asyncio.sleep(interval_ms / 1000)

    async def _publish_screenshot(self) -> None:
        if not self._page:
            return
        try:
            png = await self._page.screenshot(type="png", full_page=False)
            b64 = base64.b64encode(png).decode()
            url = self._page.url
            self._current_url = url
            await event_engine.publish(
                AetherEvent(
                    type=EventType.BROWSER_SCREENSHOT,
                    channel=EventChannel.BROWSER,
                    payload={
                        "screenshot": b64,
                        "url": url,
                        "title": await self._page.title(),
                    },
                )
            )
        except Exception as e:
            logger.debug("screenshot_failed", error=str(e))

    async def _emit_action(self, action: BrowserAction) -> None:
        self._action_log.append(action)
        if len(self._action_log) > 200:
            self._action_log = self._action_log[-200:]
        await event_engine.publish(
            AetherEvent(
                type=EventType.BROWSER_ACTION,
                channel=EventChannel.BROWSER,
                payload={
                    "id": action.id,
                    "type": action.type,
                    "description": action.description,
                    "status": action.status,
                    "result": action.result,
                    "params": action.params,
                },
            )
        )

    async def _needs_approval(self, action: BrowserAction) -> bool:
        settings = get_settings()
        if self.mode == BrowserMode.AUTONOMOUS:
            return False
        if not settings.browser_approval_mode:
            return False
        risky = {"click", "fill", "submit", "navigate"}
        return action.type in risky

    async def execute(
        self,
        action_type: str,
        params: dict[str, Any],
        description: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        async with self._lock:
            if not await self._ensure_browser():
                return {"ok": False, "error": "Browser failed to launch. Run: playwright install chromium"}

            action = BrowserAction(
                id=f"act_{uuid.uuid4().hex[:10]}",
                type=action_type,
                description=description or f"{action_type}: {params}",
                params=params,
            )

            if not force and await self._needs_approval(action):
                action.status = "awaiting_approval"
                self._pending_approvals[action.id] = action
                await self._emit_action(action)
                await event_engine.publish(
                    AetherEvent(
                        type=EventType.AUTOMATION_APPROVAL_REQUEST,
                        channel=EventChannel.AUTOMATION,
                        payload={"actionId": action.id, "description": action.description},
                    )
                )
                return {"ok": True, "actionId": action.id, "status": "awaiting_approval"}

            return await self._run_action(action)

    async def approve(self, action_id: str) -> dict[str, Any]:
        action = self._pending_approvals.pop(action_id, None)
        if not action:
            return {"ok": False, "error": "Action not found or already processed"}
        await event_engine.publish(
            AetherEvent(
                type=EventType.AUTOMATION_APPROVAL_GRANTED,
                channel=EventChannel.AUTOMATION,
                payload={"actionId": action_id},
            )
        )
        return await self._run_action(action)

    async def _run_action(self, action: BrowserAction) -> dict[str, Any]:
        action.status = "running"
        await self._emit_action(action)
        page = self._page
        assert page is not None

        try:
            if action.type == "navigate":
                url = action.params.get("url", "https://www.google.com")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                action.result = f"Navigated to {url}"
                await event_engine.publish(
                    AetherEvent(
                        type=EventType.BROWSER_NAVIGATION,
                        channel=EventChannel.BROWSER,
                        payload={"url": url},
                    )
                )

            elif action.type == "search":
                query = action.params.get("query", "")
                await page.goto(f"https://www.google.com/search?q={query}", wait_until="domcontentloaded")
                action.result = f"Searched: {query}"

            elif action.type == "click":
                selector = action.params.get("selector")
                if selector:
                    await page.click(selector, timeout=10000)
                    action.result = f"Clicked {selector}"
                else:
                    x, y = action.params.get("x", 0), action.params.get("y", 0)
                    await page.mouse.click(x, y)
                    action.result = f"Clicked ({x}, {y})"
                    await event_engine.publish(
                        AetherEvent(
                            type=EventType.BROWSER_CURSOR,
                            channel=EventChannel.BROWSER,
                            payload={"x": x, "y": y},
                        )
                    )

            elif action.type == "fill":
                selector = action.params["selector"]
                text = action.params.get("text", "")
                await page.fill(selector, text)
                action.result = f"Filled {selector}"

            elif action.type == "screenshot":
                await self._publish_screenshot()
                action.result = "Screenshot captured"

            elif action.type == "extract":
                selector = action.params.get("selector", "body")
                text = await page.inner_text(selector)
                action.result = text[:2000]

            elif action.type == "scroll":
                await page.evaluate(f"window.scrollBy(0, {action.params.get('y', 300)})")
                action.result = "Scrolled"

            else:
                action.status = "failed"
                action.result = f"Unknown action: {action.type}"
                await self._emit_action(action)
                return {"ok": False, "error": action.result}

            action.status = "complete"
            await self._emit_action(action)
            await self._publish_screenshot()
            return {"ok": True, "actionId": action.id, "result": action.result}

        except Exception as e:
            action.status = "failed"
            action.result = str(e)
            await self._emit_action(action)
            return {"ok": False, "error": str(e), "actionId": action.id}

    async def get_state(self) -> dict[str, Any]:
        return {
            "active": self._page is not None,
            "url": self._current_url or (self._page.url if self._page else ""),
            "mode": self.mode.value,
            "streaming": self._streaming,
            "pendingApprovals": len(self._pending_approvals),
            "actionLog": [
                {
                    "id": a.id,
                    "type": a.type,
                    "description": a.description,
                    "status": a.status,
                    "result": a.result,
                    "timestamp": a.timestamp,
                }
                for a in self._action_log[-50:]
            ],
        }

    async def stop(self) -> None:
        await self.stop_stream()
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = self._context = self._browser = self._playwright = None


browser_runtime = BrowserRuntime()
