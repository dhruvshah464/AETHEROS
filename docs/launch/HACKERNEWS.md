# Show HN: AetherOS — Open-source AI operating interface with real browser automation

**Title:** Show HN: AetherOS – Iron Man HUD meets autonomous agent runtime (open source)

**Post:**

I built AetherOS — a production-grade AI operating interface that feels like a sci-fi command center but runs real systems underneath.

Not a mock dashboard. Real subsystems:

- Playwright browser automation with approval gates and live screenshot streaming
- Multi-agent society with delegation and consensus
- Workflow DAG engine (terminal → browser → AI chains)
- Whisper STT + Edge TTS voice pipeline
- WebSocket event engine with event-sourced replay
- Prometheus metrics + distributed traces
- Sandboxed terminal, screen OCR, YOLO vision
- Plugin marketplace + visual Agent Studio

Stack: Next.js 15, FastAPI, LangChain, Three.js, Redis, ChromaDB.

Try it:
```
git clone https://github.com/yourusername/aetheros
cd aetheros && pnpm install
playwright install chromium
# terminal 1: uvicorn in apps/api
# terminal 2: pnpm dev:web
```

Click **Launch Demo** for the full cinematic sequence.

Looking for contributors on plugins, K8s charts, and SAM2 vision.

Repo: [link]
Demo GIF: [link]

Happy to answer architecture questions.
