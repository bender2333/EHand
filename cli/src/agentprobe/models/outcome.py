from __future__ import annotations

from typing import Any, Literal, TypedDict


TerminalState = Literal[
    "regression_pass",
    "explicit_escalation",
    "unsupported",
    "unknown",
    "approval_pending",
]

Confidence = Literal["high", "medium", "low"]


class Outcome(TypedDict):
    status: str
    terminal_state: TerminalState
    evidence: dict[str, Any]
    verdict: str
    confidence: Confidence
    next_action: str


def make_outcome(
    *,
    status: str,
    terminal_state: TerminalState,
    evidence: dict[str, Any],
    verdict: str,
    confidence: Confidence,
    next_action: str,
) -> Outcome:
    return {
        "status": status,
        "terminal_state": terminal_state,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": confidence,
        "next_action": next_action,
    }
