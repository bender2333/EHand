import json
from pathlib import Path
from typing import Any

import click

from agentprobe.core.engine import run_replay_scenario
from agentprobe.devices.topology import load_topology
from agentprobe.protocol import _generated as protocol
from agentprobe.transport.usb_transport import UsbTransport


def _emit(payload: dict[str, Any], json_output: bool) -> None:
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return

    click.echo(f"terminal_state: {payload['terminal_state']}")
    click.echo(f"verdict: {payload['verdict']}")
    click.echo(f"confidence: {payload['confidence']}")
    click.echo(f"next_action: {payload['next_action']}")


@click.group()
def main() -> None:
    """AgentProbe physical verification CLI."""


@main.group()
def device() -> None:
    """Device inspection commands."""


@device.command("status")
@click.option(
    "--topology",
    "topology_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to a declarative topology JSON file.",
)
@click.option("--json", "json_output", is_flag=True, help="Emit Agent-readable JSON.")
def device_status(topology_path: Path | None, json_output: bool) -> None:
    if topology_path is None:
        payload: dict[str, Any] = {
            "schema_version": protocol.PROTOCOL_VERSION,
            "status": "blocked",
            "terminal_state": protocol.TERMINAL_UNKNOWN,
            "error_code": protocol.ERR_UNKNOWN_DEVICE_IDENTITY,
            "verdict": "device status requires a declared topology before identity is trusted",
            "confidence": "low",
            "next_action": "provide --topology with a schema-valid topology declaration",
        }
        _emit(payload, json_output)
        return

    topology = load_topology(topology_path)
    hardware_status = UsbTransport().info()
    devices_by_role = {device["role"]: device for device in topology.devices.values()}
    payload = {
        "schema_version": protocol.PROTOCOL_VERSION,
        "status": "blocked",
        "terminal_state": protocol.TERMINAL_UNKNOWN,
        "error_code": hardware_status["error_code"],
        "connection_topology_id": topology.connection_topology_id,
        "devices": devices_by_role,
        "hardware_status": hardware_status,
        "verdict": "declared topology identity is available, but hardware transport is not connected",
        "confidence": "low",
        "next_action": "connect AgentProbe USB transport before claiming physical device status",
    }
    _emit(payload, json_output)


@main.group()
def scenario() -> None:
    """Scenario execution commands."""


@scenario.command("run")
@click.option("--replay", is_flag=True, help="Use canonical replay fixture instead of hardware.")
@click.option("--json", "json_output", is_flag=True, help="Emit Agent-readable JSON.")
def scenario_run(replay: bool, json_output: bool) -> None:
    if not replay:
        payload: dict[str, Any] = {
            "status": "blocked",
            "terminal_state": "approval_pending",
            "evidence": {"schema_version": "0.1.0", "reason": "hardware_transport_not_ready"},
            "verdict": "hardware scenario execution is not initialized",
            "confidence": "low",
            "next_action": "use --replay until hardware transport is implemented",
        }
        _emit(payload, json_output)
        return

    _emit(run_replay_scenario(), json_output)
