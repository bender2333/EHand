"""Mock Engine host-side module (architecture §7).

Differentiator core. Responsibilities:
- Load and validate declarative MockModel files (mock_model.schema.json).
- Host the optional PC Behavior Layer script escape hatch (<10ms, BUSY-buffered).
- Push mock configuration to the device (PS Mock Command Layer -> PL).
- Carry mock_fidelity provenance into the Evidence Envelope (P8).

V1: declarative model loading + fidelity provenance. Behavior Layer execution
and device configuration land with the SPI mock loop (T-11).
"""

from __future__ import annotations

from typing import Any

from agentprobe.models.evidence import MockFidelity


V1_MAX_FIDELITY_LEVEL = "L3"  # protocol.toml [mock_fidelity].v1_max_level


def load_model(model: dict[str, Any]) -> dict[str, Any]:
    """Validate a declarative MockModel against the v0.2.0 contract.

    Full JSON Schema validation is the authoritative gate; this performs the
    minimum structural checks needed before configuration.
    """
    meta = model.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("MockModel missing 'meta' object")
    for field in ("id", "peripheral_type", "version", "fidelity_level"):
        if field not in meta:
            raise ValueError(f"MockModel meta missing '{field}'")
    if meta["fidelity_level"] not in ("L1", "L2", "L3", "L4"):
        raise ValueError(f"Invalid fidelity_level: {meta['fidelity_level']!r}")
    return model


def fidelity(model: dict[str, Any]) -> MockFidelity:
    """Derive the mock_fidelity provenance block from a loaded model (P8)."""
    meta = model["meta"]
    return MockFidelity(
        level=meta["fidelity_level"],
        model_id=meta["id"],
        model_version=meta["version"],
    )


def configure(model: dict[str, Any]) -> None:
    """Push a validated MockModel to the device (PS Mock Command Layer -> PL).

    Implemented with the SPI mock loop (T-11).
    """
    raise NotImplementedError("Mock device configuration lands with the SPI mock loop (T-11).")
