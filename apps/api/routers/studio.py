"""Agent Studio API — workflow templates and visual builder persistence."""

from fastapi import APIRouter
from pydantic import BaseModel

from services.workflow_engine import workflow_engine

router = APIRouter(prefix="/studio", tags=["Agent Studio"])

TEMPLATES = [
    {
        "id": "research_mission",
        "name": "Research Mission",
        "description": "Autonomous research with browser + AI synthesis",
        "nodes": [
            {"id": "s1", "type": "browser", "label": "Gather Intel", "params": {"action": "navigate", "params": {"url": "https://github.com/trending"}, "force": True}},
            {"id": "s2", "type": "ai", "label": "Analyze", "params": {"prompt": "Summarize trending open source projects"}, "dependsOn": ["s1"]},
        ],
    },
    {
        "id": "ops_deploy",
        "name": "Ops Deploy",
        "description": "Terminal checks + system validation",
        "nodes": [
            {"id": "o1", "type": "terminal", "label": "Health Check", "params": {"command": "echo System OK && pwd"}},
            {"id": "o2", "type": "ai", "label": "Report", "params": {"prompt": "Generate ops status report"}, "dependsOn": ["o1"]},
        ],
    },
    {
        "id": "security_audit",
        "name": "Security Audit",
        "description": "Security-focused agent workflow",
        "nodes": [
            {"id": "a1", "type": "ai", "label": "Threat Model", "params": {"prompt": "List top 5 security checks for an AI OS"}},
            {"id": "a2", "type": "terminal", "label": "Scan", "params": {"command": "echo Security scan complete"}, "dependsOn": ["a1"]},
        ],
    },
]


class SaveWorkflowRequest(BaseModel):
    name: str
    nodes: list[dict]


@router.get("/templates")
async def templates():
    return {"templates": TEMPLATES}


@router.post("/save")
async def save(req: SaveWorkflowRequest):
    wf = workflow_engine.create(req.name, req.nodes)
    return workflow_engine._to_dict(wf)


@router.post("/deploy/{template_id}")
async def deploy_template(template_id: str):
    tpl = next((t for t in TEMPLATES if t["id"] == template_id), None)
    if not tpl:
        return {"ok": False, "error": "Template not found"}
    wf = workflow_engine.create(tpl["name"], tpl["nodes"])
    result = await workflow_engine.execute(wf.id)
    return {**result, "workflow": workflow_engine._to_dict(wf)}
