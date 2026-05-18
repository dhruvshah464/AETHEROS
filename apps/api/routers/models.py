from fastapi import APIRouter
from pydantic import BaseModel

from services.model_manager import model_manager

router = APIRouter(prefix="/models", tags=["Models"])


class BenchmarkRequest(BaseModel):
    provider: str = "ollama"
    model: str | None = None


class PullRequest(BaseModel):
    name: str


@router.get("/")
async def list_models():
    return await model_manager.list_models()


@router.post("/benchmark")
async def benchmark(req: BenchmarkRequest):
    return await model_manager.benchmark(req.provider, req.model)


@router.post("/pull")
async def pull(req: PullRequest):
    return await model_manager.pull_model(req.name)
