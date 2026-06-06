import json
import unittest

from click.testing import CliRunner

from agentprobe.cli.app import main


class ReplayCliTests(unittest.TestCase):
    def test_replay_scenario_returns_regression_pass(self) -> None:
        result = CliRunner().invoke(main, ["scenario", "run", "--replay", "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["terminal_state"], "regression_pass")
        evidence = payload["evidence"]
        self.assertEqual(evidence["schema_version"], "0.2.0")
        self.assertEqual(evidence["source_device"]["role"], "golden")
        self.assertEqual(evidence["target_device"]["role"], "dut")

    def test_replay_evidence_has_no_redundant_identity_fields(self) -> None:
        # v0.2.0 contract: identity lives only in source_device/target_device.
        result = CliRunner().invoke(main, ["scenario", "run", "--replay", "--json"])
        evidence = json.loads(result.output)["evidence"]
        for removed in (
            "device_id",
            "serial",
            "firmware_version",
            "bitstream_version",
            "source_device_role",
            "target_device_role",
        ):
            self.assertNotIn(removed, evidence, f"{removed} should not be at top level")


if __name__ == "__main__":
    unittest.main()
