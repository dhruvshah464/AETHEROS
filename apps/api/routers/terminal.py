from fastapi import APIRouter
from pydantic import BaseModel

from core.security import Role, security
from core.observability import observability
from services.terminal_runtime import terminal_runtime

router = APIRouter(prefix="/terminal", tags=["Terminal"])


class TerminalRequest(BaseModel):
    command: str
    cwd: str | None = None


@router.post("/execute")
async def execute(req: TerminalRequest):
    allowed, risk, msg = security.authorize_action("operator", "terminal", req.command, Role.OPERATOR, "terminal")
    if not allowed:
        return {"ok": False, "error": msg, "riskScore": risk}
    with observability.trace("terminal.execute", command=req.command[:80]):
        result = await terminal_runtime.execute(req.command, req.cwd)
    return {**result, "riskScore": risk}


@router.get("/audit")
async def audit_log(limit: int = 50):
    return {"entries": terminal_runtime.get_audit_log(limit)}
