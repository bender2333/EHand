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
        self.assertEqual(payload["evidence"]["schema_version"], "0.1.0")
        self.assertEqual(payload["evidence"]["source_device"]["role"], "golden")
        self.assertEqual(payload["evidence"]["target_device"]["role"], "dut")


if __name__ == "__main__":
    unittest.main()
