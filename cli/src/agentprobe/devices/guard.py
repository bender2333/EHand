from __future__ import annotations

from dataclasses import dataclass

from agentprobe.devices.topology import Topology
from agentprobe.models.outcome import TerminalState
from agentprobe.protocol import _generated as protocol


@dataclass(frozen=True)
class ActionRequest:
    action: str
    source_device_id: str | None
    target_device_id: str | None
    approval_required: bool = False


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    terminal_state: TerminalState
    error_code: int
    verdict: str

    @classmethod
    def allow(cls) -> "GuardDecision":
        return cls(
            allowed=True,
            terminal_state=protocol.TERMINAL_REGRESSION_PASS,
            error_code=protocol.ERR_OK,
            verdict="identity and topology guard passed",
        )


def evaluate_action(request: ActionRequest, topology: Topology | None) -> GuardDecision:
    if topology is None:
        return _unknown("topology is not declared")

    if request.action not in topology.allowed_state_changing_actions:
        return GuardDecision(
            allowed=False,
            terminal_state=protocol.TERMINAL_APPROVAL_PENDING,
            error_code=protocol.ERR_APPROVAL_REQUIRED,
            verdict=f"state-changing action {request.action!r} is not declared for this topology",
        )

    source = topology.device(request.source_device_id)
    target = topology.device(request.target_device_id)
    if source is None or target is None:
        return _unknown("source or target device identity is missing from topology")

    if _is_golden_upgrade(request.action, target["role"]):
        return GuardDecision(
            allowed=False,
            terminal_state=protocol.TERMINAL_APPROVAL_PENDING,
            error_code=protocol.ERR_SAFETY_REFUSED,
            verdict="Golden upgrade is refused by the identity guard",
        )

    if request.approval_required:
        return GuardDecision(
            allowed=False,
            terminal_state=protocol.TERMINAL_APPROVAL_PENDING,
            error_code=protocol.ERR_APPROVAL_REQUIRED,
            verdict="action requires human approval after identity and topology were resolved",
        )

    return GuardDecision.allow()


def _unknown(verdict: str) -> GuardDecision:
    return GuardDecision(
        allowed=False,
        terminal_state=protocol.TERMINAL_UNKNOWN,
        error_code=protocol.ERR_UNKNOWN_DEVICE_IDENTITY,
        verdict=verdict,
    )


def _is_golden_upgrade(action: str, target_role: str) -> bool:
    return (
        protocol.GOLDEN_UPGRADE_MODE_DEFAULT == "disabled"
        and target_role == "golden"
        and action in {"firmware_update", "bitstream_update"}
    )
