"""Evidence Envelope data model (contract v0.2.0).

Device identity lives only in source_device/target_device (architecture §10.2).
The redundant top-level identity fields from v0.1.0 are intentionally absent.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict


EVIDENCE_SCHEMA_VERSION = "0.2.0"

Role = Literal["golden", "dut", "external_target", "host"]
Confidence = Literal["high", "medium", "low"]
FidelityLevel = Literal["L1", "L2", "L3", "L4"]
Bottleneck = Literal[
    "observation_gap",
    "execution_gap",
    "semantic_translation_gap",
    "agent_reasoning_gap",
    "support_boundary_gap",
]


class DeviceIdentity(TypedDict):
    role: Role
    device_id: str
    serial: str
    firmware_version: str
    bitstream_version: str


class MockFidelity(TypedDict):
    level: FidelityLevel
    model_id: str
    model_version: str


class EvidenceEnvelope(TypedDict, total=False):
    # Required fields.
    schema_version: str
    run_id: str
    trace_id: str
    connection_topology_id: str
    source_device: DeviceIdentity
    target_device: DeviceIdentity
    build_result: dict[str, Any]
    flash_result: dict[str, Any]
    capture_result: dict[str, Any]
    diagnosis_result: dict[str, Any]
    regression_result: dict[str, Any]
    verdict: str
    confidence: Confidence
    # Optional fields.
    escalation_reason: Optional[str]
    bottleneck: Optional[Bottleneck]
    mock_fidelity: Optional[MockFidelity]
    artifact_refs: list[str]


REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "trace_id",
        "connection_topology_id",
        "source_device",
        "target_device",
        "build_result",
        "flash_result",
        "capture_result",
        "diagnosis_result",
        "regression_result",
        "verdict",
        "confidence",
    }
)

_IDENTITY_FIELDS = frozenset(
    {"role", "device_id", "serial", "firmware_version", "bitstream_version"}
)


def validate(envelope: dict[str, Any]) -> None:
    """Lightweight structural validation against the v0.2.0 envelope contract.

    This mirrors evidence.schema.json for fast in-process checks; full JSON
    Schema validation remains the authoritative gate.
    """
    missing = sorted(REQUIRED_FIELDS - envelope.keys())
    if missing:
        raise ValueError(f"Evidence missing required fields: {', '.join(missing)}")

    if envelope["schema_version"] != EVIDENCE_SCHEMA_VERSION:
        raise ValueError(
            f"Evidence schema_version must be {EVIDENCE_SCHEMA_VERSION}, "
            f"got {envelope['schema_version']!r}"
        )

    for side in ("source_device", "target_device"):
        identity = envelope[side]
        missing_id = sorted(_IDENTITY_FIELDS - identity.keys())
        if missing_id:
            raise ValueError(f"{side} missing identity fields: {', '.join(missing_id)}")
