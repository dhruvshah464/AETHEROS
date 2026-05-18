from fastapi import APIRouter
from pydantic import BaseModel

from core.security import Role, security
from core.observability import observability
from services.browser_runtime import BrowserMode, browser_runtime

router = APIRouter(prefix="/browser", tags=["Browser"])


class BrowserActionRequest(BaseModel):
    action: str
    params: dict = {}
    description: str | None = None
    force: bool = False


class BrowserModeRequest(BaseModel):
    mode: str


@router.post("/launch")
async def launch():
    await browser_runtime.start_stream(500)
    return await browser_runtime.get_state()


@router.post("/stop")
async def stop():
    await browser_runtime.stop()
    return {"ok": True}


@router.post("/action")
async def execute_action(req: BrowserActionRequest):
    detail = req.description or f"{req.action} {req.params}"
    allowed, risk, msg = security.authorize_action("operator", "browser", detail, Role.OPERATOR, "browser")
    if not allowed and not req.force:
        return {"ok": False, "error": msg, "riskScore": risk, "status": "blocked"}
    with observability.trace("browser.action", action=req.action):
        result = await browser_runtime.execute(req.action, req.params, req.description, req.force)
    observability.record_browser_action(req.action, result.get("status", "unknown"))
    return {**result, "riskScore": risk}


@router.post("/approve/{action_id}")
async def approve_action(action_id: str):
    return await browser_runtime.approve(action_id)


@router.post("/mode")
async def set_mode(req: BrowserModeRequest):
    browser_runtime.mode = BrowserMode(req.mode)
    return {"mode": browser_runtime.mode.value}


@router.get("/state")
async def get_state():
    return await browser_runtime.get_state()
