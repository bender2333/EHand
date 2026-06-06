from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from click.testing import CliRunner

from agentprobe.cli.app import main
from agentprobe.devices.guard import ActionRequest, GuardDecision, evaluate_action
from agentprobe.devices.topology import load_topology
from agentprobe.protocol import _generated as protocol


def _identity(role: str, device_id: str) -> dict[str, str]:
    return {
        "role": role,
        "device_id": device_id,
        "serial": f"SER-{device_id}",
        "firmware_version": "fw-0.2.0",
        "bitstream_version": "bit-0.2.0",
    }


def _topology() -> dict[str, object]:
    return {
        "schema_version": protocol.PROTOCOL_VERSION,
        "connection_topology_id": "self-hosting-two-board",
        "devices": [
            _identity("golden", "golden-001"),
            _identity("dut", "dut-001"),
            _identity("host", "host-001"),
        ],
        "connections": [
            {
                "from": "golden-001",
                "to": "dut-001",
                "signal": "swdio",
                "purpose": "swd",
            }
        ],
        "allowed_state_changing_actions": ["flash", "reset", "firmware_update"],
    }


class DeviceIdentityGuardTests(unittest.TestCase):
    def test_complete_identity_and_topology_allows_state_changing_action(self) -> None:
        topology = load_topology(_topology())
        request = ActionRequest(
            action="flash",
            source_device_id="golden-001",
            target_device_id="dut-001",
        )

        decision = evaluate_action(request, topology)

        self.assertEqual(decision, GuardDecision.allow())

    def test_missing_identity_returns_unknown_without_success_verdict(self) -> None:
        topology = load_topology(_topology())
        request = ActionRequest(
            action="flash",
            source_device_id="golden-001",
            target_device_id=None,
        )

        decision = evaluate_action(request, topology)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.terminal_state, protocol.TERMINAL_UNKNOWN)
        self.assertEqual(decision.error_code, protocol.ERR_UNKNOWN_DEVICE_IDENTITY)
        self.assertNotEqual(decision.verdict, "success")

    def test_high_risk_action_requires_approval_after_identity_is_known(self) -> None:
        topology = load_topology(_topology())
        request = ActionRequest(
            action="reset",
            source_device_id="golden-001",
            target_device_id="dut-001",
            approval_required=True,
        )

        decision = evaluate_action(request, topology)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.terminal_state, protocol.TERMINAL_APPROVAL_PENDING)
        self.assertEqual(decision.error_code, protocol.ERR_APPROVAL_REQUIRED)
        self.assertNotEqual(decision.verdict, "success")

    def test_golden_upgrade_is_refused_by_the_guard_layer(self) -> None:
        topology = load_topology(_topology())
        request = ActionRequest(
            action="firmware_update",
            source_device_id="host-001",
            target_device_id="golden-001",
        )

        decision = evaluate_action(request, topology)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.terminal_state, protocol.TERMINAL_APPROVAL_PENDING)
        self.assertEqual(decision.error_code, protocol.ERR_SAFETY_REFUSED)
        self.assertIn("Golden", decision.verdict)


class DeviceStatusTests(unittest.TestCase):
    def test_device_status_without_topology_returns_unknown_not_ok(self) -> None:
        result = CliRunner().invoke(main, ["device", "status", "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["schema_version"], protocol.PROTOCOL_VERSION)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["terminal_state"], protocol.TERMINAL_UNKNOWN)
        self.assertEqual(payload["error_code"], protocol.ERR_UNKNOWN_DEVICE_IDENTITY)
        self.assertNotEqual(payload["verdict"], "ok")

    def test_device_status_with_valid_topology_still_does_not_claim_hardware_status(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "topology.json"
            path.write_text(json.dumps(_topology()), encoding="utf-8")

            result = CliRunner().invoke(main, ["device", "status", "--topology", str(path), "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["schema_version"], protocol.PROTOCOL_VERSION)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["terminal_state"], "unknown")
        self.assertEqual(payload["hardware_status"]["status"], "unknown")
        self.assertEqual(payload["connection_topology_id"], "self-hosting-two-board")
        self.assertEqual(payload["devices"]["golden"]["device_id"], "golden-001")


if __name__ == "__main__":
    unittest.main()
