<div align="center">

# ◈ AETHEROS

### *The open-source AI operating layer from 2032.*

**Iron Man HUD × autonomous agent runtime × production infrastructure**

[![License: MIT](https://img.shields.io/badge/License-MIT-00f0ff?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.3.0-00f0ff?style=flat-square)](.)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Prometheus](https://img.shields.io/badge/metrics-Prometheus-E6522C?style=flat-square&logo=prometheus)](infra/observability/)

*Not a chat UI. Not a mock dashboard. A real autonomous AI operating platform.*

[Launch Demo](#-60-second-demo) · [Architecture](#-architecture) · [Deploy](#-deployment) · [Plugins](#-plugin-ecosystem) · [Contributing](CONTRIBUTING.md)

</div>

---

## Why this exists

Every AI product looks like a chat window.

**AetherOS looks like you're commanding a billion-dollar intelligence system** — because underneath the holographic interface runs production engineering:

| Subsystem | What it actually does |
|-----------|----------------------|
| **Browser Runtime** | Playwright automation, approval gates, live screenshot stream |
| **Agent Society** | 12+ agents, delegation, consensus, inter-agent messaging |
| **Workflow Engine** | DAG missions: terminal → browser → AI chains |
| **Voice Pipeline** | Whisper STT → LLM → Edge TTS with waveform UI |
| **Memory V3** | Graph memory, importance scoring, vector recall |
| **Event Engine** | WebSocket pub/sub, append-only replay, Redis backbone |
| **Observability** | Prometheus metrics, distributed traces, diagnostics HUD |
| **Security** | RBAC, risk scoring, safe/developer/air-gapped modes |

---

## 60-second demo

```bash
git clone https://github.com/yourusername/aetheros.git && cd aetheros
pnpm install && cd apps/api && pip install -r requirements-core.txt
playwright install chromium

# Terminal 1
cd apps/api && uvicorn main:app --reload --port 8000

# Terminal 2  
pnpm dev:web
```

Open **http://localhost:3000** → click **Launch Demo** → watch autonomous browser, AI agents, and terminal execute a full mission.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AETHEROS PLATFORM v0.3                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐   WebSocket/SSE   ┌──────────────────────────┐ │
│  │  Next.js 15 HUD │◄──────────────────►│  FastAPI Gateway           │ │
│  │  Three.js · FUI │                    │  Event Engine · Auth       │ │
│  │  14 HUD Screens │                    │  Observability · Plugins   │ │
│  └─────────────────┘                    └─────────────┬────────────┘ │
│                                                        │               │
│     ┌──────────────────────────────────────────────────┼───────────┐ │
│     │  Browser │ Terminal │ Workflow │ Voice │ Vision │ Society    │ │
│     │  Memory  │ Demo Dir │ Studio   │ Screen│ Models │ Diagnostics│ │
│     └──────────────────────────────────────────────────┴───────────┘ │
│                              Redis · Postgres · Chroma                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## HUD Screens

| Screen | Capability |
|--------|------------|
| Command Center | Streaming AI + agent routing |
| Browser Control | Live Playwright viewport + action stream |
| Agent Network | Society topology + inter-agent comms |
| Mission / Studio | Workflow graphs + visual builder |
| Voice | Jarvis push-to-talk + TTS |
| Vision | YOLO webcam + screen analysis |
| Memory V3 | Knowledge graph + semantic search |
| Neural Activity | Token flow + attention heatmap |
| Models | Ollama/OpenAI benchmarks |
| Diagnostics | Traces, failures, latency heatmaps |
| Security | RBAC, audit log, execution modes |
| Plugin Marketplace | Extension ecosystem |

---

## Quick start

### Requirements

- Node 20+, pnpm 9+, Python 3.12+
- Optional: Docker, Ollama, NVIDIA GPU, Tesseract

### Environment

```bash
cp .env.example .env
# OPENAI_API_KEY=... or run Ollama locally
```

### Full stack (Docker)

```bash
docker compose -f infra/docker-compose.yml up -d
pnpm dev:web
```

### Observability stack (optional)

```bash
docker compose -f infra/docker-compose.yml \
  -f infra/observability/docker-compose.observability.yml up -d
# Grafana: http://localhost:3001 (admin/aetheros)
# Prometheus: http://localhost:9090
```

---

## API highlights

| Endpoint | Description |
|----------|-------------|
| `WS /ws` | Realtime event backbone |
| `POST /ai/command` | Streaming AI with agent routing |
| `POST /browser/action` | Playwright automation |
| `POST /society/execute` | Multi-agent collaborative execution |
| `POST /demo/start` | Cinematic demo sequences |
| `GET /diagnostics/metrics` | Prometheus scrape |
| `GET /memory/v3/graph` | Knowledge graph |
| `GET /plugins/marketplace` | Plugin ecosystem |

Full docs: **http://localhost:8000/docs**

---

## Plugin ecosystem

```bash
plugins/
  example-hello/     # Reference plugin
```

Create `plugins/your-plugin/plugin.json` + `tool.py` with `run(context)` → `POST /plugins/discover`

---

## Deployment

| Target | Path |
|--------|------|
| Docker Compose | `infra/docker-compose.yml` |
| Kubernetes Helm | `infra/helm/aetheros/` |
| Observability | `infra/observability/` |

---

## Demo modes

| Sequence | Audience |
|----------|----------|
| `mission_impossible` | Viral / HN |
| `recruiter` | Hiring |
| `investor` | Fundraising |
| `oss_showcase` | GitHub stars |

---

## Roadmap

- [x] Autonomous browser + terminal + workflows
- [x] Voice + vision + screen intelligence  
- [x] Observability + security + memory graph
- [x] Plugin marketplace + agent studio
- [ ] SAM2 segmentation + motion tracking
- [ ] Remote agent mesh nodes
- [ ] OpenTelemetry → Tempo full stack
- [ ] Visual regression CI

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). We need plugin authors, K8s operators, and vision engineers.

---

## License

MIT © AetherOS Contributors

---

<div align="center">

**If this blew your mind, star the repo — it fuels the mission.**

*Built for engineers who ship the future.*

</div>
