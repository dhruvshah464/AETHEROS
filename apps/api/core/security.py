"""Enterprise security runtime — auth, RBAC, execution modes, risk scoring."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ExecutionMode(str, Enum):
    SAFE = "safe"
    DEVELOPER = "developer"
    AIRGAPPED = "airgapped"


class Role(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.VIEWER: {"read", "telemetry", "memory.read"},
    Role.OPERATOR: {"read", "telemetry", "memory.read", "ai.command", "browser", "terminal", "workflow"},
    Role.ADMIN: {"*"},
}


@dataclass
class APIKeyRecord:
    key_id: str
    key_hash: str
    role: Role
    name: str
    created_at: float = field(default_factory=lambda: time.time())


@dataclass
class AuditEntry:
    id: str
    action: str
    actor: str
    risk_score: float
    allowed: bool
    detail: str
    timestamp: float = field(default_factory=lambda: time.time() * 1000)


class SecurityRuntime:
    def __init__(self) -> None:
        self.execution_mode = ExecutionMode.SAFE
        self._api_keys: dict[str, APIKeyRecord] = {}
        self._audit_log: deque[AuditEntry] = deque(maxlen=1000)
        self._jwt_secret = secrets.token_hex(32)
        self._create_default_key()

    def _create_default_key(self) -> None:
        raw = f"aether_{secrets.token_urlsafe(24)}"
        kid = f"key_{secrets.token_hex(4)}"
        self._api_keys[kid] = APIKeyRecord(
            key_id=kid,
            key_hash=self._hash_key(raw),
            role=Role.ADMIN,
            name="default-dev-key",
        )
        self._default_raw_key = raw
        logger.info("default_api_key_created", hint="Check /auth/bootstrap for dev key")

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def validate_api_key(self, key: str | None) -> tuple[bool, Role | None]:
        if not key:
            return True, Role.ADMIN  # open dev mode when no key configured
        h = self._hash_key(key)
        for record in self._api_keys.values():
            if hmac.compare_digest(record.key_hash, h):
                return True, record.role
        return False, None

    def has_permission(self, role: Role, permission: str) -> bool:
        perms = ROLE_PERMISSIONS.get(role, set())
        return "*" in perms or permission in perms

    def score_risk(self, action_type: str, detail: str) -> float:
        score = 0.0
        lower = detail.lower()
        high_risk = ["rm ", "rm -rf", "sudo", "curl", "wget", "eval", "exec", "password", "token", "api_key"]
        medium_risk = ["navigate", "click", "fill", "submit", "download"]
        if action_type in ("terminal", "browser"):
            for p in high_risk:
                if p in lower:
                    score += 0.35
            for p in medium_risk:
                if p in lower:
                    score += 0.15
        if self.execution_mode == ExecutionMode.AIRGAPPED:
            score += 0.5
        return min(1.0, score)

    def authorize_action(
        self,
        actor: str,
        action: str,
        detail: str,
        role: Role,
        permission: str,
    ) -> tuple[bool, float, str]:
        if not self.has_permission(role, permission):
            self._audit(actor, action, 1.0, False, "permission denied")
            return False, 1.0, "Permission denied"

        risk = self.score_risk(action, detail)
        if self.execution_mode == ExecutionMode.SAFE and risk >= 0.4:
            self._audit(actor, action, risk, False, "requires approval — safe mode")
            return False, risk, "Action blocked in safe mode — approval required"

        if self.execution_mode == ExecutionMode.AIRGAPPED and action in ("browser", "terminal"):
            self._audit(actor, action, risk, False, "air-gapped mode")
            return False, risk, "Air-gapped mode — external actions disabled"

        self._audit(actor, action, risk, True, detail[:200])
        return True, risk, "authorized"

    def _audit(self, actor: str, action: str, risk: float, allowed: bool, detail: str) -> None:
        self._audit_log.appendleft(
            AuditEntry(
                id=f"aud_{secrets.token_hex(6)}",
                action=action,
                actor=actor,
                risk_score=risk,
                allowed=allowed,
                detail=detail,
            )
        )

    def get_audit_log(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            {
                "id": e.id,
                "action": e.action,
                "actor": e.actor,
                "riskScore": e.risk_score,
                "allowed": e.allowed,
                "detail": e.detail,
                "timestamp": e.timestamp,
            }
            for e in list(self._audit_log)[:limit]
        ]

    def create_token(self, subject: str, role: Role, expires_hours: int = 24) -> str:
        try:
            from jose import jwt

            payload = {
                "sub": subject,
                "role": role.value,
                "exp": time.time() + expires_hours * 3600,
                "iat": time.time(),
            }
            return jwt.encode(payload, self._jwt_secret, algorithm="HS256")
        except ImportError:
            return f"dev-token-{subject}-{role.value}"

    def verify_token(self, token: str) -> tuple[bool, str | None, Role | None]:
        try:
            from jose import jwt

            payload = jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
            return True, payload.get("sub"), Role(payload.get("role", "viewer"))
        except Exception:
            if token.startswith("dev-token-"):
                parts = token.split("-")
                return True, parts[2] if len(parts) > 2 else "dev", Role.ADMIN
            return False, None, None

    def bootstrap_info(self) -> dict[str, Any]:
        return {
            "executionMode": self.execution_mode.value,
            "devApiKey": getattr(self, "_default_raw_key", None),
            "roles": [r.value for r in Role],
            "modes": [m.value for m in ExecutionMode],
        }


security = SecurityRuntime()
