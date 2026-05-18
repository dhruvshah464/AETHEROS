"""Production observability — Prometheus metrics + distributed trace spans."""

from __future__ import annotations

import time
import uuid
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator

import structlog

logger = structlog.get_logger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain"


if PROMETHEUS_AVAILABLE:
    HTTP_REQUESTS = Counter("aetheros_http_requests_total", "HTTP requests", ["method", "endpoint", "status"])
    WS_CONNECTIONS = Gauge("aetheros_websocket_connections", "Active WebSocket connections")
    AI_TOKENS = Counter("aetheros_ai_tokens_total", "AI tokens processed", ["direction"])
    AI_LATENCY = Histogram("aetheros_ai_inference_seconds", "AI inference latency", buckets=(0.1, 0.5, 1, 2, 5, 10, 30))
    AGENT_TASKS = Counter("aetheros_agent_tasks_total", "Agent tasks", ["agent", "status"])
    BROWSER_ACTIONS = Counter("aetheros_browser_actions_total", "Browser actions", ["action", "status"])
    WORKFLOW_DURATION = Histogram("aetheros_workflow_duration_seconds", "Workflow duration")
    EVENTS_PUBLISHED = Counter("aetheros_events_published_total", "Events published", ["channel", "type"])


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    name: str
    service: str
    start_ms: float
    end_ms: float | None = None
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)
    parent_id: str | None = None


class ObservabilityPlatform:
    def __init__(self) -> None:
        self._traces: deque[TraceSpan] = deque(maxlen=500)
        self._failures: deque[dict[str, Any]] = deque(maxlen=100)
        self._latency_buckets: dict[str, list[float]] = {}
        self._ws_count = 0

    def ws_connected(self) -> None:
        self._ws_count += 1
        if PROMETHEUS_AVAILABLE:
            WS_CONNECTIONS.set(self._ws_count)

    def ws_disconnected(self) -> None:
        self._ws_count = max(0, self._ws_count - 1)
        if PROMETHEUS_AVAILABLE:
            WS_CONNECTIONS.set(self._ws_count)

    def record_event(self, channel: str, event_type: str) -> None:
        if PROMETHEUS_AVAILABLE:
            EVENTS_PUBLISHED.labels(channel=channel, type=event_type).inc()

    def record_ai_tokens(self, count: int, direction: str = "out") -> None:
        if PROMETHEUS_AVAILABLE:
            AI_TOKENS.labels(direction=direction).inc(count)

    def record_ai_latency(self, seconds: float) -> None:
        if PROMETHEUS_AVAILABLE:
            AI_LATENCY.observe(seconds)
        self._bucket("ai_inference", seconds * 1000)

    def record_agent_task(self, agent: str, status: str) -> None:
        if PROMETHEUS_AVAILABLE:
            AGENT_TASKS.labels(agent=agent, status=status).inc()

    def record_browser_action(self, action: str, status: str) -> None:
        if PROMETHEUS_AVAILABLE:
            BROWSER_ACTIONS.labels(action=action, status=status).inc()

    def record_failure(self, subsystem: str, error: str, context: dict | None = None) -> None:
        self._failures.appendleft(
            {
                "id": f"fail_{uuid.uuid4().hex[:8]}",
                "subsystem": subsystem,
                "error": error,
                "context": context or {},
                "timestamp": time.time() * 1000,
            }
        )

    def _bucket(self, name: str, ms: float) -> None:
        if name not in self._latency_buckets:
            self._latency_buckets[name] = deque(maxlen=200)
        self._latency_buckets[name].append(ms)

    @contextmanager
    def trace(self, name: str, service: str = "aetheros-api", **attrs: Any) -> Generator[TraceSpan, None, None]:
        trace_id = f"tr_{uuid.uuid4().hex[:12]}"
        span = TraceSpan(
            trace_id=trace_id,
            span_id=f"sp_{uuid.uuid4().hex[:8]}",
            name=name,
            service=service,
            start_ms=time.time() * 1000,
            attributes=attrs,
        )
        self._traces.append(span)
        try:
            yield span
            span.status = "ok"
        except Exception as e:
            span.status = "error"
            span.attributes["error"] = str(e)
            self.record_failure(service, str(e), {"span": name})
            raise
        finally:
            span.end_ms = time.time() * 1000
            duration = (span.end_ms - span.start_ms) / 1000
            if "workflow" in name.lower() and PROMETHEUS_AVAILABLE:
                WORKFLOW_DURATION.observe(duration)

    def get_diagnostics(self) -> dict[str, Any]:
        traces = list(self._traces)[-50:]
        heatmap: dict[str, list[float]] = {}
        for name, samples in self._latency_buckets.items():
            if samples:
                heatmap[name] = list(samples)[-24:]

        return {
            "prometheus": PROMETHEUS_AVAILABLE,
            "websocketConnections": self._ws_count,
            "recentTraces": [
                {
                    "traceId": t.trace_id,
                    "spanId": t.span_id,
                    "name": t.name,
                    "service": t.service,
                    "durationMs": (t.end_ms or time.time() * 1000) - t.start_ms,
                    "status": t.status,
                    "attributes": t.attributes,
                }
                for t in reversed(traces)
            ],
            "failures": list(self._failures)[:20],
            "latencyHeatmap": heatmap,
        }

    def metrics_bytes(self) -> bytes:
        if PROMETHEUS_AVAILABLE:
            return generate_latest()
        return b"# prometheus_client not installed\n"


observability = ObservabilityPlatform()
