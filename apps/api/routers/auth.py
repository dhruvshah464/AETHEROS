from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from core.security import ExecutionMode, Role, security

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    subject: str = "operator"
    role: str = "operator"


class ModeRequest(BaseModel):
    mode: str


@router.get("/bootstrap")
async def bootstrap():
    return security.bootstrap_info()


@router.post("/token")
async def create_token(req: LoginRequest):
    role = Role(req.role) if req.role in [r.value for r in Role] else Role.OPERATOR
    return {"token": security.create_token(req.subject, role), "role": role.value}


@router.post("/mode")
async def set_execution_mode(req: ModeRequest):
    try:
        security.execution_mode = ExecutionMode(req.mode)
    except ValueError:
        raise HTTPException(400, "Invalid mode")
    return {"mode": security.execution_mode.value}


@router.get("/audit")
async def audit_log(limit: int = 50):
    return {"entries": security.get_audit_log(limit)}


@router.get("/verify")
async def verify(authorization: str | None = Header(None), x_api_key: str | None = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        ok, sub, role = security.verify_token(authorization[7:])
        return {"valid": ok, "subject": sub, "role": role.value if role else None}
    if x_api_key:
        ok, role = security.validate_api_key(x_api_key)
        return {"valid": ok, "role": role.value if role else None}
    return {"valid": True, "mode": "open-dev"}
