import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from core.security import ExecutionMode, Role, security


def test_risk_scoring():
    score = security.score_risk("terminal", "rm -rf /tmp")
    assert score > 0.3


def test_safe_mode_blocks_risky():
    security.execution_mode = ExecutionMode.SAFE
    allowed, risk, _ = security.authorize_action("op", "terminal", "rm -rf /tmp", Role.OPERATOR, "terminal")
    assert not allowed
    assert risk >= 0.4


def test_airgapped_blocks_browser():
    security.execution_mode = ExecutionMode.AIRGAPPED
    allowed, _, msg = security.authorize_action("op", "browser", "navigate", Role.ADMIN, "browser")
    assert not allowed
    assert "Air-gapped" in msg
