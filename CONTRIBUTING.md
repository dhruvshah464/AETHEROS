# Contributing to AetherOS

Thank you for helping build the most advanced open-source AI operating interface.

## Quick Start

```bash
pnpm install
cd apps/api && pip install -r requirements-core.txt
playwright install chromium
pnpm dev:web   # :3000
uvicorn main:app --reload  # :8000
```

## Architecture

- `apps/web` — Next.js holographic HUD
- `apps/api` — FastAPI realtime gateway + autonomous runtimes
- `packages/types` — Shared TypeScript contracts
- `plugins/` — Plugin SDK examples

## Plugin Development

1. Create `plugins/your-plugin/plugin.json`
2. Add `tool.py` with a `run(context)` function
3. Run `POST /plugins/discover`

See `plugins/example-hello/` for reference.

## Pull Request Guidelines

- Typed APIs on both frontend and backend
- Real implementations — no mock UIs
- Event publishing for realtime features
- Test critical paths when possible

## Good First Issues

- New HUD screen plugins
- Additional demo sequences
- Ollama model presets
- Vision model integrations
