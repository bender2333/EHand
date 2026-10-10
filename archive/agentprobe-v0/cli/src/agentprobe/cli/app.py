import json
from typing import Any

import click

from agentprobe.core.engine import run_replay_scenario


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
@click.option("--json", "json_output", is_flag=True, help="Emit Agent-readable JSON.")
def device_status(json_output: bool) -> None:
    payload: dict[str, Any] = {
        "status": "ok",
        "terminal_state": "unknown",
        "evidence": {
            "schema_version": "0.1.0",
            "reason": "repo_bootstrap_placeholder",
        },
        "verdict": "device transport not initialized",
        "confidence": "low",
        "next_action": "run replay-first loop implementation",
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
