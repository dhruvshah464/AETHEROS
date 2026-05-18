# AetherOS Architecture

## Design Principles

1. **Event-first** — All subsystems communicate through typed events on a central bus
2. **Realtime by default** — WebSocket streaming with HTTP SSE fallback
3. **Graceful degradation** — Redis, Chroma, and LLM providers fail independently
4. **Modular agents** — Specialized agents with visible orchestration
5. **Local + Cloud** — Ollama for edge, OpenAI/Anthropic for cloud

## Event Engine

The `EventEngine` (`apps/api/core/events.py`) is the nervous system:

- Publishes typed `AetherEvent` objects to channel subscribers
- Fans out to all WebSocket connections
- Optionally mirrors to Redis pub/sub for horizontal scaling
- Maintains rolling history (500 events) for reconnect sync

### Event Channels

| Channel | Purpose |
|---------|---------|
| `system` | Connection, heartbeat, errors |
| `telemetry` | CPU, GPU, memory snapshots |
| `ai` | Token streaming, command lifecycle |
| `agent` | Status, messages, task progress |
| `vision` | Detections, frame metadata |
| `voice` | Transcripts, TTS state |
| `memory` | Store, recall, search |
| `automation` | Browser/terminal actions |

## LLM Router

`services/llm_router.py` implements provider abstraction:

1. Try configured primary provider (OpenAI/Anthropic/Ollama)
2. On failure, cascade through fallback chain
3. Offline mode returns structured system status message
4. Updates telemetry with token counts and latency

## Agent Orchestrator

`services/agents.py` routes commands heuristically:

- Keyword classification → specialist agent
- Publishes inter-agent messages visible in UI
- Streams LLM response through assigned agent persona
- Planning agent collaborates on complex (>100 char) tasks

## Frontend State

Zustand store (`apps/web/src/store/aether-store.ts`) mirrors backend events:

- WebSocket hook subscribes and dispatches by event type
- HTTP SSE fallback when WebSocket unavailable
- Screen router renders 10 HUD views

## Scaling Path

```
Single Node          →    Horizontal
─────────────             ──────────
FastAPI + WS         →    Redis pub/sub
In-memory events     →    Multiple API replicas
Local Chroma         →    Chroma cluster
SQLite/Postgres      →    pgvector on RDS
```

## Security Notes

- `AGENT_APPROVAL_MODE` gates autonomous actions (Phase 4)
- CORS restricted to configured origins
- API keys via environment only
- No secrets in client bundle
