#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "◈ AetherOS — Starting development stack"

# API
if [ ! -d "apps/api/.venv" ]; then
  echo "Creating Python venv..."
  python3 -m venv apps/api/.venv
  source apps/api/.venv/bin/activate
  pip install -q -r apps/api/requirements-core.txt
else
  source apps/api/.venv/bin/activate
fi

export PYTHONPATH="$ROOT/apps/api"

echo "Starting API on :8000..."
(cd apps/api && uvicorn main:app --reload --host 0.0.0.0 --port 8000) &
API_PID=$!

echo "Starting HUD on :3000..."
npx pnpm@9.15.0 --filter @aetheros/web dev &
WEB_PID=$!

trap "kill $API_PID $WEB_PID 2>/dev/null" EXIT

echo ""
echo "  HUD:  http://localhost:3000"
echo "  API:  http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo ""

wait
