from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from agentprobe.models.evidence import DeviceIdentity
from agentprobe.protocol import _generated as protocol


ROOT = Path(__file__).resolve().parents[4]
TOPOLOGY_SCHEMA = ROOT / "scenarios" / "schemas" / "topology.schema.json"


@dataclass(frozen=True)
class Topology:
    connection_topology_id: str
    devices: dict[str, DeviceIdentity]
    allowed_state_changing_actions: frozenset[str]

    def device(self, device_id: str | None) -> DeviceIdentity | None:
        if device_id is None:
            return None
        return self.devices.get(device_id)


def load_topology(source: dict[str, Any] | Path | str) -> Topology:
    if isinstance(source, dict):
        data = source
    else:
        path = Path(source)
        data = json.loads(path.read_text(encoding="utf-8"))

    _validate_topology_schema(data)
    devices = {device["device_id"]: device for device in data["devices"]}
    allowed = data.get("allowed_state_changing_actions") or protocol.STATE_CHANGING_ACTIONS
    return Topology(
        connection_topology_id=data["connection_topology_id"],
        devices=devices,
        allowed_state_changing_actions=frozenset(allowed),
    )


def _validate_topology_schema(data: dict[str, Any]) -> None:
    schema = json.loads(TOPOLOGY_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
