from fastapi import APIRouter
from pydantic import BaseModel

from services.workflow_engine import workflow_engine

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class CreateWorkflowRequest(BaseModel):
    name: str
    nodes: list[dict]


@router.post("/create")
async def create(req: CreateWorkflowRequest):
    wf = workflow_engine.create(req.name, req.nodes)
    return workflow_engine._to_dict(wf)


@router.post("/{workflow_id}/execute")
async def execute(workflow_id: str):
    return await workflow_engine.execute(workflow_id)


@router.get("/{workflow_id}")
async def get(workflow_id: str):
    wf = workflow_engine.get(workflow_id)
    if not wf:
        return {"error": "Not found"}
    return workflow_engine._to_dict(wf)


@router.get("/list/all")
async def list_workflows():
    return {"workflows": workflow_engine.list_all()}
