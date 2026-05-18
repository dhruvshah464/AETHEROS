from fastapi import APIRouter, Response

from core.observability import CONTENT_TYPE_LATEST, observability
from core.events import event_engine

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/")
async def diagnostics():
    data = observability.get_diagnostics()
    data["eventEngine"] = {
        "websocketConnections": len(event_engine._connections),
        "historySize": len(event_engine._history),
    }
    return data


@router.get("/metrics")
async def prometheus_metrics():
    return Response(content=observability.metrics_bytes(), media_type=CONTENT_TYPE_LATEST)


@router.get("/traces")
async def traces(limit: int = 50):
    d = observability.get_diagnostics()
    return {"traces": d["recentTraces"][:limit]}


@router.get("/failures")
async def failures():
    d = observability.get_diagnostics()
    return {"failures": d["failures"]}
